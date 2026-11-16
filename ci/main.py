"""Portable CI core: pytest, pyright, pyrefly and the release checks run in
Dagger containers.

Plain Dagger SDK program (no module). Run through the engine session:

    dagger run python ci/main.py <test|pyright|pyrefly|all> [options]
    dagger run python ci/main.py <release-status|release-verify> X.Y.Z

The same command runs locally (Docker + ``dagger`` CLI) and in RWX. RWX owns
caching of everything before this step; locally Dagger uses its own engine cache.
"""

# ruff: noqa: INP001

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
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
    "**/__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


# Type checkers read no spec or docs; pytest does (overlay/spec/README tests).
TYPECHECK_EXCLUDES = ["openapi", "generated/docs"]


def _source(*, typecheck: bool = False) -> dagger.Directory:
    extra = TYPECHECK_EXCLUDES if typecheck else []
    return dag.host().directory(str(REPO_ROOT), exclude=[*EXCLUDES, *extra])


def _base(*, typecheck: bool = False) -> dagger.Container:
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
            _source(typecheck=typecheck),
            include=[
                "pyproject.toml",
                "uv.lock",
                "README.md",
                "generated/src",
                "attio_cli",
            ],
        )
        .with_exec(["uv", "sync", "--frozen"])
        .with_directory("/repo", _source(typecheck=typecheck))
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
        _base(typecheck=True),
        ["uv", "run", "--with", PYRIGHT_SPEC, "pyright", *paths],
    )


async def cmd_pyrefly(ns: argparse.Namespace) -> int:
    paths = ns.paths.split()
    return await _run(
        _base(typecheck=True),
        [
            "uv", "run", "--with", PYREFLY_SPEC, "pyrefly", "check",
            "--python-interpreter-path", "/venv/bin/python", "--search-path", ".",
            "--site-package-path", "generated/src", *paths,
        ],
    )  # fmt: skip


async def cmd_all(ns: argparse.Namespace) -> int:
    codes = [await cmd_test(ns), await cmd_pyright(ns), await cmd_pyrefly(ns)]
    return max(codes)


def _release_base() -> dagger.Container:
    """Python + uv with only the stdlib PyPI checker; no repo sync needed.

    PyPI is external state, so a per-call cache buster stops Dagger from
    replaying an earlier answer for the same version.
    """
    return (
        dag.container()
        .from_(PYTHON_IMAGE)
        .with_exec(["pip", "install", "--no-cache-dir", f"uv=={UV_VERSION}"])
        .with_workdir("/repo")
        .with_file(
            "/repo/ci/pypi_release_status.py",
            dag.host().file(str(REPO_ROOT / "ci" / "pypi_release_status.py")),
        )
        .with_env_variable("CACHE_BUSTER", str(time.time_ns()))
    )


async def cmd_release_status(ns: argparse.Namespace) -> int:
    """Exit 0 when both packages have a wheel and sdist on PyPI, 1 when not,
    2 when PyPI could not be read (see ci/pypi_release_status.py).
    """
    return await _run(
        _release_base(),
        ["python", "ci/pypi_release_status.py", ns.version],
    )


# Wait for every file (wheel + sdist, both packages), ~10 minutes, then
# smoke-test both commands; the CDN can lag the JSON API, so retry installs.
_RELEASE_VERIFY_SCRIPT = r"""
set -eu
for attempt in $(seq 1 60); do
  if python ci/pypi_release_status.py "$VERSION"; then break; fi
  if [ "$attempt" -eq 60 ]; then
    echo "attio and gtm-attio $VERSION were not complete on PyPI within 10 minutes" >&2
    exit 1
  fi
  sleep 10
done
for cmd in attio gtm-attio; do
  for attempt in 1 2 3 4 5 6; do
    if uvx --refresh "$cmd@$VERSION" --version; then break; fi
    if [ "$attempt" -eq 6 ]; then echo "uvx $cmd@$VERSION --version failed" >&2; exit 1; fi
    sleep 20
  done
done
"""


async def cmd_release_verify(ns: argparse.Namespace) -> int:
    ctr = _release_base().with_env_variable("VERSION", ns.version)
    return await _run(ctr, ["sh", "-c", _RELEASE_VERIFY_SCRIPT])


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
    for name, fn in (
        ("release-status", cmd_release_status),
        ("release-verify", cmd_release_verify),
    ):
        sp = sub.add_parser(name)
        sp.set_defaults(fn=fn)
        sp.add_argument("version", help="release version, e.g. 0.28.9")
    return p


async def main() -> int:
    ns = _parser().parse_args()
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        return await ns.fn(ns)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
