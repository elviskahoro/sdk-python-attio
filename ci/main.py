"""Portable CI core: pytest, pyright and pyrefly run in Dagger containers.

Plain Dagger SDK program (no module). Run through the engine session:

    dagger run python ci/main.py <test|pyright|pyrefly|all> [options]

The same command runs locally (Docker + ``dagger`` CLI) and in RWX. RWX owns
caching of everything before this step; locally Dagger uses its own engine cache.
"""

# ruff: noqa: INP001

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import dagger
from dagger import dag

PYTHON_IMAGE = "python:3.13-slim-bookworm"
UV_VERSION = "0.11.26"  # keep in sync with the `uv` task in .rwx/*.yml
# Pinned to the Trunk versions (.trunk/trunk.yaml); not in the dev group.
PYRIGHT_SPEC = "pyright[nodejs]==1.1.414"
PYREFLY_SPEC = "pyrefly==1.3.1"
DEFAULT_TYPE_PATHS = "attio_cli ci"
REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDES = [
    ".git",
    ".venv",
    ".beads",
    ".context",
    "dist",
    "tmp",
    "openapi",
    "generated/docs",
    "**/__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


def _source() -> dagger.Directory:
    return dag.host().directory(str(REPO_ROOT), exclude=EXCLUDES)


def _base() -> dagger.Container:
    """Toolchain -> uv -> sources -> `uv sync` (least to most changing)."""
    return (
        dag.container()
        .from_(PYTHON_IMAGE)
        .with_exec(["pip", "install", "--no-cache-dir", f"uv=={UV_VERSION}"])
        .with_mounted_cache("/root/.cache/uv", dag.cache_volume("attio-uv-cache"))
        .with_env_variable("UV_LINK_MODE", "copy")
        .with_env_variable("UV_PROJECT_ENVIRONMENT", "/venv")
        .with_workdir("/repo")
        # Manifests first so the sync layer survives source-only edits.
        .with_directory(
            "/repo",
            _source(),
            include=[
                "pyproject.toml",
                "uv.lock",
                "README.md",
                "generated/src",
                "attio_cli",
            ],
        )
        .with_exec(["uv", "sync", "--frozen"])
        .with_directory("/repo", _source())
    )


async def _run(
    ctr: dagger.Container,
    args: list[str],
    export: str | None = None,
) -> int:
    """Run args; always export `export` dir (junit, logs) even on failure."""
    ctr = ctr.with_exec(args, expect=dagger.ReturnType.ANY)
    code = await ctr.exit_code()
    out = await ctr.stdout()
    err = await ctr.stderr()
    sys.stdout.write(out)
    sys.stderr.write(err)
    if export:
        dest = REPO_ROOT / export
        dest.mkdir(parents=True, exist_ok=True)
        await ctr.directory(f"/repo/{export}").export(str(dest))
    return code


async def cmd_test(ns: argparse.Namespace) -> int:
    name = ns.junit_name
    args = [
        "uv", "run", "pytest", "-q", "-o", "junit_family=xunit1",
        f"--junit-xml=tmp/junit-{name}.xml", "--report-log=tmp/log.json",
        *ns.pytest_args,
    ]  # fmt: skip
    ctr = _base().with_exec(["mkdir", "-p", "tmp"])
    return await _run(ctr, args, export="tmp")


async def cmd_pyright(ns: argparse.Namespace) -> int:
    paths = ns.paths.split()
    return await _run(
        _base(),
        ["uv", "run", "--with", PYRIGHT_SPEC, "pyright", *paths],
    )


async def cmd_pyrefly(ns: argparse.Namespace) -> int:
    paths = ns.paths.split()
    return await _run(
        _base(),
        [
            "uv", "run", "--with", PYREFLY_SPEC, "pyrefly", "check",
            "--python-interpreter-path", "/venv/bin/python", "--search-path", ".",
            "--site-package-path", "generated/src", *paths,
        ],
    )  # fmt: skip


async def cmd_all(ns: argparse.Namespace) -> int:
    codes = [await cmd_test(ns), await cmd_pyright(ns), await cmd_pyrefly(ns)]
    return max(codes)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ci/main.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("test", cmd_test), ("pyright", cmd_pyright),
        ("pyrefly", cmd_pyrefly), ("all", cmd_all),
    ):  # fmt: skip
        sp = sub.add_parser(name)
        sp.set_defaults(fn=fn)
        sp.add_argument("--junit-name", default="sdk-python-attio-pytest")
        sp.add_argument(
            "--paths",
            default=os.environ.get("CHECK_PATHS", DEFAULT_TYPE_PATHS),
        )
        sp.add_argument("pytest_args", nargs="*", help="extra pytest args (test/all)")
    return p


async def main() -> int:
    ns = _parser().parse_args()
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        return await ns.fn(ns)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
