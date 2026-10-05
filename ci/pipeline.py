#!/usr/bin/env python3
"""Attio SDK Dagger CI pipeline with object-oriented design and snapshots.

Available commands:
    fetch-openapi                  Fetch latest OpenAPI spec and update workflow.yaml
    check-openapi [--report PATH]  Fetch latest spec, diff vs current, verify overlay
                                   (exit 1 on structural drift or overlay rot)
    verify-version <version>       Verify pyproject.toml + _version.py match <version>
    release-bump <version>         Rewrite pyproject.toml + _version.py to <version>
    test                           Run test suite
    build                          Build distribution packages
    generate [--force] [--version] [--no-fetch]
                                   Generate SDK via Speakeasy
    publish                        Build and publish to PyPI
    ci [--force] [--version] [...] Complete workflow: fetch, generate, test, build, optionally publish

Examples:
    python ci/pipeline.py fetch-openapi
    python ci/pipeline.py check-openapi --report tmp/spec-check/report.json
    python ci/pipeline.py verify-version 0.22.9
    python ci/pipeline.py release-bump 0.22.9
    python ci/pipeline.py test
    python ci/pipeline.py generate --force --version 1.0.0
    python ci/pipeline.py generate --no-fetch
    python ci/pipeline.py build
    python ci/pipeline.py publish
    python ci/pipeline.py ci --publish

The commands above use Dagger for their isolated build and generation steps.
Use them locally and in CI so generated files are exported back to the
working tree before subsequent checks run.
"""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Protocol

import dagger  # type: ignore[import-untyped]
from dagger import Directory, Doc, dag, function  # type: ignore[import-untyped]

_VERIFY_VERSION_SCRIPT = r"""
import os, pathlib, re, sys, tomllib

expected = os.environ["EXPECTED_VERSION"]
py = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"]
m = re.search(
    r'^__version__\s*:\s*str\s*=\s*"([^"]+)"',
    pathlib.Path("src/attio/_version.py").read_text(),
    re.M,
)
under = m.group(1) if m else "<unset>"
print(f"expected={expected} pyproject={py} _version.py={under}")

fail = False
if py != expected:
    print(f"pyproject.toml version {py} does not match {expected}", file=sys.stderr)
    fail = True
if under != expected:
    print(f"_version.py __version__ {under} does not match {expected}", file=sys.stderr)
    fail = True
if fail:
    sys.exit("Version mismatch. Run scripts/release.sh to bump both files in lockstep.")
"""

_RELEASE_BUMP_SCRIPT = r"""
import os, pathlib, re, sys

version = os.environ["RELEASE_VERSION"]

pyproject = pathlib.Path("pyproject.toml")
text = pyproject.read_text()
new = re.sub(r'^(version\s*=\s*)"[^"]+"', rf'\1"{version}"', text, count=1, flags=re.M)
if new == text:
    sys.exit('Could not find version = "..." in pyproject.toml')
pyproject.write_text(new)

vfile = pathlib.Path("src/attio/_version.py")
text = vfile.read_text()
new = re.sub(
    r'^(__version__\s*:\s*str\s*=\s*)"[^"]+"',
    rf'\1"{version}"',
    text,
    count=1,
    flags=re.M,
)
new = re.sub(
    r'^(__user_agent__\s*:\s*str\s*=\s*"speakeasy-sdk/python )[^ ]+( .+")$',
    rf'\g<1>{version}\g<2>',
    new,
    count=1,
    flags=re.M,
)
if new == text:
    sys.exit('Could not find __version__ in src/attio/_version.py')
vfile.write_text(new)
"""

_GTM_PACKAGE_VARIANT_SCRIPT = r"""
# Convert the staged SDK checkout into the gtm-attio distribution.  The import
# package deliberately remains ``attio``, so users can install either
# distribution without changing their imports.

import pathlib
import re
import sys

pyproject = pathlib.Path("pyproject.toml")
text = pyproject.read_text()
new = re.sub(
    r'^(name\s*=\s*)"attio"',
    r'\1"gtm-attio"',
    text,
    count=1,
    flags=re.M,
)
if new == text:
    sys.exit('Could not change project name from "attio" to "gtm-attio"')
pyproject.write_text(new)

vfile = pathlib.Path("src/attio/_version.py")
text = vfile.read_text()
new = re.sub(
    r'^(__title__\s*:\s*str\s*=\s*)"attio"',
    r'\1"gtm-attio"',
    text,
    count=1,
    flags=re.M,
)
new = re.sub(
    r'(speakeasy-sdk/python [^ ]+ [^ ]+ [^ ]+ )attio"$',
    r'\1gtm-attio"',
    new,
    count=1,
    flags=re.M,
)
if new == text:
    sys.exit("Could not create the gtm-attio _version.py variant")
vfile.write_text(new)
"""

_PYPI_PUBLISHER_MODULE = "github.com/elviskahoro/sdk-python-publish-to-pypi@main"

# The Speakeasy CLI version the weekly spec-update-check workflow pins. The
# host-CLI path logs a warning when the installed CLI differs from this, so
# generated output drift between local runs and CI is visible.
_SPEAKEASY_CLI_PIN = "1.800.1"


# Repo root, anchored to this file per the repo path rule: spec adoption
# and the gate rollback must touch the same files regardless of the
# directory the pipeline is invoked from.
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _sync_write_spec(spec_path: str, spec_data: dict[str, object]) -> None:
    """Write OpenAPI spec to disk (synchronous).

    ``spec_path`` is the repo-relative label used in workflow.yaml; the
    write itself is anchored to the repo root so running the pipeline from
    another directory cannot scatter specs (or split the rollback's
    snapshot from the file that was actually rewritten).
    """
    dest = _REPO_ROOT / spec_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(spec_data, indent=2))


def _sync_update_workflow(overlay_path: str, spec_path: str) -> None:
    """Update workflow.yaml (synchronous)."""
    import re

    workflow_content = _WORKFLOW_YAML.read_text(encoding="utf-8")

    workflow_content = re.sub(
        r"location: openapi/api-[\d]+\.json",
        f"location: {spec_path}",
        workflow_content,
    )
    workflow_content = re.sub(
        r"output: openapi/api-[\d]+-overlay\.json",
        f"output: {overlay_path}",
        workflow_content,
    )

    _WORKFLOW_YAML.write_text(workflow_content, encoding="utf-8")


async def fetch_latest_spec() -> str:
    """Fetch the latest OpenAPI spec and update workflow.yaml locally."""
    import httpx

    spec_url = "https://api.attio.com/openapi/api"
    from datetime import timezone

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M")
    spec_filename = f"api-{timestamp}.json"
    spec_path = f"openapi/{spec_filename}"

    print(f"Fetching latest OpenAPI spec from {spec_url}...", file=sys.stderr)

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(spec_url)
        response.raise_for_status()
        try:
            spec_data = response.json()
        except json.JSONDecodeError as err:
            msg = f"Invalid JSON in spec: {err}"
            raise RuntimeError(msg) from err

    # Write spec and workflow synchronously outside async context
    _sync_write_spec(spec_path, spec_data)
    print(f"Saved spec to {spec_path}", file=sys.stderr)

    overlay_filename = f"api-{timestamp}-overlay.json"
    overlay_path = f"openapi/{overlay_filename}"

    _sync_update_workflow(overlay_path, spec_path)

    print(f"Updated .speakeasy/workflow.yaml to point to {spec_path}", file=sys.stderr)
    return spec_path


def _has_local_speakeasy_auth() -> bool:
    """Return whether the installed Speakeasy CLI has an authenticated session."""
    try:
        result = subprocess.run(
            ["speakeasy", "auth", "status"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def _env_flag(name: str) -> bool:
    """Truthy env flag: only ``1``/``true``/``yes`` count.

    Plain truthiness would let ``SKIP_OVERLAY_CHECK=0`` or ``=false`` (as
    set by some CI systems for disabled flags) silently disable a safety
    gate, which is exactly the failure mode this repo guards against.
    """
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def _local_speakeasy_usable() -> bool:
    """Return whether generation can run through the host Speakeasy CLI.

    Defaults preserve the historical split: a logged-in CLI session with no
    ``SPEAKEASY_API_KEY`` in the environment uses the host CLI, while a set
    key selects the pinned Dagger container (matching CI's pinned
    generator). Setting ``SPEAKEASY_USE_HOST_CLI`` opts into the host CLI
    explicitly — with either a login session or the key — which is how the
    scheduled workflow (CLI installed, no container runtime) takes that
    path deliberately. The chosen CLI's version is logged on every run, so
    drift from the pin is visible rather than silent.
    """
    if shutil.which("speakeasy") is None:
        if _env_flag("SPEAKEASY_USE_HOST_CLI"):
            # An explicit opt-in must not silently fall back to the Dagger
            # path: the scheduled workflow has no container runtime, so the
            # fallback would die later with an unrelated engine error —
            # after the spec was already adopted.
            msg = (
                "SPEAKEASY_USE_HOST_CLI is set but the speakeasy CLI is not "
                "on PATH — install it (the weekly workflow pins the version) "
                "or unset the flag to use the Dagger container path"
            )
            raise RuntimeError(msg)
        return False
    has_key = bool(os.environ.get("SPEAKEASY_API_KEY"))
    if _env_flag("SPEAKEASY_USE_HOST_CLI"):
        return _has_local_speakeasy_auth() or has_key
    return _has_local_speakeasy_auth() and not has_key


class _SpecDiffModule(Protocol):
    """The slice of ci/spec_diff.py the pipeline depends on."""

    def main(self, argv: list[str] | None = None) -> int: ...


def _load_spec_diff_module() -> "_SpecDiffModule":
    """Load ci/spec_diff.py by path.

    A bare ``import spec_diff`` would only resolve when ``ci/`` happens to
    be on ``sys.path`` (true for ``python ci/pipeline.py``, false when this
    file is imported as a module from tests or ``python -m``), so load it
    explicitly from its path next to this file.
    """
    import importlib.util

    path = Path(__file__).resolve().parent / "spec_diff.py"
    spec = importlib.util.spec_from_file_location("attio_ci_spec_diff", path)
    if spec is None or spec.loader is None:
        msg = f"could not load {path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module  # type: ignore[return-value]


def _verify_overlay_health(*, skip: bool = False) -> None:
    """Refuse to generate while the overlay is unhealthy.

    Speakeasy silently skips overlay actions whose JSONPath no longer
    matches, so generating with a broken overlay ships an SDK that is
    missing fixes this repo believes it applies. Running check-overlay
    here (against the spec about to be used) closes the loop for manual
    ``speakeasy run`` / ``pipeline generate`` invocations too, not just
    the weekly workflow.

    ``skip`` (from ``--skip-overlay-check`` or ``SKIP_OVERLAY_CHECK=1``)
    is an explicit, loudly-logged escape hatch for a false positive in
    the checker's heuristics blocking an urgent regeneration — the check
    itself stays on by default everywhere, including the workflow.
    """
    if skip:
        print(
            "WARNING: skipping the overlay health check; speakeasy may "
            "silently drop overlay actions whose targets no longer match",
            file=sys.stderr,
        )
        return
    spec_diff = _load_spec_diff_module()
    code = spec_diff.main(["check-overlay"])
    if code:
        msg = (
            "overlay is unhealthy — fix overlay.yaml before generating "
            "(see the check-overlay output above), or pass "
            "--skip-overlay-check to bypass in an emergency. Note: if the "
            "spec was just fetched, it is already adopted into "
            ".speakeasy/workflow.yaml and openapi/ — the tree now points at "
            "the new spec even though nothing was generated"
        )
        raise RuntimeError(msg)


# Anchored (not cwd-relative) per the repo path rule: the gate rollback
# must find workflow.yaml even when invoked from another directory — and
# the same anchor the fetch-side helpers write through, so the snapshot
# and the restored file are always the same file.
_WORKFLOW_YAML = _REPO_ROOT / ".speakeasy" / "workflow.yaml"


async def _fetch_then_verify_overlay(*, skip: bool = False) -> None:
    """Fetch the latest spec, then gate on overlay health.

    ``fetch_latest_spec()`` adopts the new spec (rewriting
    ``.speakeasy/workflow.yaml`` and writing ``openapi/api-*.json``), so
    the snapshot is taken BEFORE the fetch. On a gate failure — including
    cancellation — the workflow.yaml reference is restored to its
    pre-fetch state and the unadopted spec file is removed, so the tree
    never keeps pointing at a spec that was never verified.
    """
    snapshot = (
        _WORKFLOW_YAML.read_text(encoding="utf-8") if _WORKFLOW_YAML.exists() else None
    )
    adopted_spec = await fetch_latest_spec()
    gate_passed = False
    try:
        _verify_overlay_health(skip=skip)
        gate_passed = True
    finally:
        # finally + flag (not except Exception): a KeyboardInterrupt or
        # asyncio.CancelledError mid-gate must roll back too, and the
        # original exception propagates naturally.
        if (
            not gate_passed
            and snapshot is not None
            and _WORKFLOW_YAML.read_text(encoding="utf-8") != snapshot
        ):
            _WORKFLOW_YAML.write_text(snapshot, encoding="utf-8")
            # The just-fetched spec file is unreferenced once
            # workflow.yaml is restored; remove it (off the event loop)
            # so a failed run leaves no orphan.
            await asyncio.to_thread(
                (_REPO_ROOT / adopted_spec).unlink,
                missing_ok=True,
            )
            print(
                "Restored .speakeasy/workflow.yaml to the pre-fetch spec "
                "reference and removed the unadopted spec file",
                file=sys.stderr,
            )


def _preflight_generation_path() -> None:
    """Surface generation-path problems before anything is adopted.

    Runs the path-selection predicate purely for its loud failure (an
    explicit ``SPEAKEASY_USE_HOST_CLI`` with no installed CLI raises), so a
    later ``_generate_sdk`` call cannot hit that error after the fetch has
    already adopted a new spec.
    """
    _local_speakeasy_usable()


def _log_host_cli_version() -> None:
    """Log the host CLI version and warn when it differs from the pin."""
    import re

    cli = shutil.which("speakeasy")
    if cli is None:
        return
    try:
        probe = subprocess.run(  # noqa: S603 - cli is shutil.which("speakeasy"), not user input
            [cli, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return
    lines = (probe.stdout or probe.stderr or "").strip().splitlines()
    banner = lines[0] if lines else "unknown"
    print(f"Host Speakeasy CLI: {banner}", file=sys.stderr)
    match = re.search(r"version (\S+)", banner)
    if match is None:
        # An unparsed banner must be visible too, or CLI drift hides behind
        # a format change in the --version output.
        print(
            f"WARNING: could not parse the CLI version from {banner!r}; "
            f"unable to compare against the pinned {_SPEAKEASY_CLI_PIN}",
            file=sys.stderr,
        )
    elif match.group(1) != _SPEAKEASY_CLI_PIN:
        print(
            f"WARNING: host CLI {match.group(1)} differs from the pinned "
            f"{_SPEAKEASY_CLI_PIN}; generated output may differ from CI",
            file=sys.stderr,
        )


async def _run_local_speakeasy(*, version: str | None) -> None:
    """Run generation with the host CLI, after logging which CLI is in use."""
    _log_host_cli_version()
    command = [
        "speakeasy",
        "run",
        "--auto-yes",
        "--output",
        "console",
        "--skip-upload-spec",
    ]
    if version:
        command.extend(["--set-version", version])
    await asyncio.to_thread(subprocess.run, command, check=True)


def _host_source_dir() -> Directory:
    """Create a stable Dagger source snapshot without local runtime state."""
    return dag.host().directory(
        ".",
        exclude=[".git", ".venv", ".beads", "dist"],
    )


def _replace_dist_directory() -> None:
    """Remove prior distribution artifacts before exporting a fresh build."""
    dist_dir = Path("dist")
    if dist_dir.is_symlink() or dist_dir.is_file():
        dist_dir.unlink()
    elif dist_dir.is_dir():
        shutil.rmtree(dist_dir)


def _apply_post_generation_patches() -> None:
    """Re-apply manual patches to the freshly generated SDK source.

    ``speakeasy run`` rewrites ``src/`` from the OpenAPI overlay, dropping
    hand-edits to generated files. ``ci/post_generate_patch.py`` idempotently
    re-injects the patches that ``overlay.yaml`` cannot express, so the tree
    the tests, build, and PR commit consume already carries them. Run after
    every generation export so a regeneration can no longer silently drop
    the manual edits.
    """
    script = Path(__file__).resolve().parent / "post_generate_patch.py"
    subprocess.run([sys.executable, str(script)], check=True)


def _publish_artifacts() -> None:
    """Publish the just-built artifacts through the shared Dagger module.

    ``env:PYPI_TOKEN`` makes Dagger read the token as a Secret, so it is never
    passed as a command-line token or copied into build artifacts.
    """
    if not Path("dist").is_dir():
        raise RuntimeError(
            "dist/ does not exist; run the build command before publishing",
        )
    subprocess.run(
        [
            "dagger",
            "-m",
            _PYPI_PUBLISHER_MODULE,
            "call",
            "publish-artifacts",
            "--artifacts",
            "./dist",
            "--pypi-token",
            "env:PYPI_TOKEN",
        ],
        check=True,
    )


class AttioSDKPipeline:
    def __init__(self, source: Directory) -> None:
        """Initialize pipeline with source directory."""
        self.source = source

    @function
    def builder_env(self) -> dagger.Container:
        """Base Python environment with uv and pip cache."""
        pip_cache = dag.cache_volume("pip-cache")
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_mounted_cache("/root/.cache/pip", pip_cache)
            .with_exec(["pip", "install", "uv"])
            .with_mounted_directory("/repo", self.source)
            .with_workdir("/repo")
        )

    @function
    def dependencies_installed(self, container: dagger.Container) -> dagger.Container:
        """Install project dependencies snapshot."""
        return container.with_exec(["uv", "sync"])

    @function
    async def test(self) -> str:
        """Run test suite."""
        env = self.builder_env()
        deps = self.dependencies_installed(env)
        return await deps.with_exec(["uv", "run", "pytest", "-v"]).stdout()

    @function
    async def verify_version(
        self,
        version: Annotated[
            str,
            Doc("Expected version (no leading 'v')"),
        ],
    ) -> str:
        """Verify pyproject.toml and src/attio/_version.py match the expected version.

        Used by the release workflow before publishing to PyPI to catch tags
        that drift from the in-tree version. Run scripts/release.sh <version>
        to fix any mismatch.
        """
        return await (
            dag.container()
            .from_("python:3.13-slim")
            .with_mounted_directory("/repo", self.source)
            .with_workdir("/repo")
            .with_env_variable("EXPECTED_VERSION", version)
            .with_exec(["python", "-c", _VERIFY_VERSION_SCRIPT])
            .stdout()
        )

    @function
    def release_bump(
        self,
        version: Annotated[
            str,
            Doc("Target version (no leading 'v'), e.g. 0.22.9"),
        ],
    ) -> dagger.Directory:
        """Rewrite pyproject.toml + src/attio/_version.py to the target version.

        Returns the patched repo as a Directory so the caller can export the
        files back to the host (the git commit/tag/push lives in
        scripts/release.sh, not inside the container).
        """
        return (
            dag.container()
            .from_("python:3.13-slim")
            .with_mounted_directory("/repo", self.source)
            .with_workdir("/repo")
            .with_env_variable("RELEASE_VERSION", version)
            .with_exec(["python", "-c", _RELEASE_BUMP_SCRIPT])
            .directory("/repo")
        )

    @function
    def speakeasy_env(self, api_key: dagger.Secret) -> dagger.Container:
        """Speakeasy environment with dependencies."""
        apt_cache = dag.cache_volume("apt-cache")
        return (
            dag.container()
            .from_("ghcr.io/speakeasy-api/speakeasy:latest")
            .with_mounted_cache("/var/cache/apt/archives", apt_cache)
            .with_exec(
                [
                    "/bin/sh",
                    "-c",
                    "sudo apt-get update && sudo apt-get install -y ca-certificates",
                ],
            )
            .with_secret_variable("SPEAKEASY_API_KEY", api_key)
            .with_mounted_directory("/repo", self.source)
            .with_workdir("/repo")
        )

    @function
    def speakeasy_prepared(
        self,
        container: dagger.Container,
    ) -> dagger.Container:
        """Prepare speakeasy container with ownership and temp dir."""
        return container.with_exec(
            ["/bin/sh", "-c", "sudo chown -R speakeasy:speakeasy /repo"],
        ).with_exec(["/bin/sh", "-c", "mkdir -p .speakeasy/temp"])

    @function
    def speakeasy_executed(
        self,
        container: dagger.Container,
        *,
        force: bool = False,
        version: str | None = None,
    ) -> dagger.Container:
        """Execute speakeasy generation."""
        run_args = ["speakeasy", "run"]
        if force:
            run_args.append("--force")
        if version:
            run_args += ["--set-version", version]
        return container.with_exec(run_args)

    @function
    async def generate(
        self,
        api_key: Annotated[dagger.Secret, Doc("Speakeasy API key")],
        *,
        force: Annotated[bool, Doc("Force regeneration")] = False,
        version: Annotated[str | None, Doc("SDK version")] = None,
    ) -> dagger.Directory:
        """Generate SDK via Speakeasy.

        Steps:
        1. Prepare Speakeasy container with API key
        2. Set up ownership and temp directories
        3. Execute generation with optional flags

        The caller must fetch the spec and create ``source`` afterwards, so
        the mounted source snapshot includes the updated workflow and spec.
        """
        env = self.speakeasy_env(api_key)
        prepared = self.speakeasy_prepared(env)
        executed = self.speakeasy_executed(prepared, force=force, version=version)

        await executed.sync()
        return executed.directory("/repo/src")

    @function
    def build(self) -> dagger.Container:
        """Build the ``attio`` and ``gtm-attio`` distribution artifacts.

        Both distributions expose the same ``attio`` import package.  The
        gtm-attio metadata is applied only to a staged copy, so the canonical
        source tree remains the attio SDK Speakeasy regenerates.
        """
        staged = (
            self.builder_env()
            .with_exec(
                ["/bin/sh", "-c", "mkdir -p /work /dist && cp -a /repo/. /work/"],
            )
            .with_workdir("/work")
            .with_exec(["uv", "build", "--out-dir", "/dist"])
        )
        return staged.with_exec(
            ["python", "-c", _GTM_PACKAGE_VARIANT_SCRIPT],
        ).with_exec(["uv", "build", "--out-dir", "/dist"])

    @function
    async def ci(
        self,
        api_key: Annotated[dagger.Secret, Doc("Speakeasy API key")],
    ) -> str:
        """Complete CI workflow: test, generate, and build."""
        test_output = await self.test()
        print(f"Tests passed\n{test_output}", file=sys.stderr)

        await self.generate(api_key=api_key)
        print("SDK generated successfully", file=sys.stderr)

        built = self.build()
        await built.sync()
        print("Build completed successfully", file=sys.stderr)

        return "Complete CI pipeline finished"


async def cmd_test() -> None:
    """CLI handler for test command."""
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        result = await pipeline.test()
        print(result)


async def _generate_sdk(
    *,
    force: bool,
    version: str | None,
    api_key_str: str | None,
) -> None:
    """Generate the SDK via the host CLI or the pinned Dagger container.

    Single implementation shared by ``cmd_generate`` and ``cmd_ci`` so the
    two paths cannot drift apart. Prefers the host CLI when usable (faster,
    no engine, and the path the scheduled GitHub workflow takes); otherwise
    generates in the pinned Speakeasy container via Dagger, exporting
    ``src/`` back to the host. Post-generation patches are re-applied on
    both paths.
    """
    if _local_speakeasy_usable():
        _ = force
        print("Generating with the host Speakeasy CLI", file=sys.stderr)
        await _run_local_speakeasy(version=version)
        _apply_post_generation_patches()
        print("SDK generated with the local Speakeasy CLI", file=sys.stderr)
        return

    # Callers guarantee api_key_str is set whenever the local-CLI path is
    # not taken; keep the guard so a future refactor fails loudly.
    if api_key_str is None:
        msg = "unreachable: SPEAKEASY_API_KEY must be set on the Dagger path"
        raise RuntimeError(msg)
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        print(
            "Generating with the pinned Speakeasy container via Dagger "
            "(src/ only — use the host CLI for the full tree: docs/, "
            "README, pyproject, USAGE)",
            file=sys.stderr,
        )
        api_key = dag.set_secret("SPEAKEASY_API_KEY", api_key_str)
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        generated = await pipeline.generate(
            api_key=api_key,
            force=force,
            version=version,
        )
        await generated.export("./src")
        _apply_post_generation_patches()
        print("SDK generated and exported to ./src", file=sys.stderr)


async def cmd_generate(
    *,
    force: bool,
    version: str | None,
    no_fetch: bool = False,
    skip_overlay_check: bool = False,
) -> None:
    """Fetch (unless ``no_fetch``), generate, and export the SDK into the tree."""
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    api_key_str = os.environ.get("SPEAKEASY_API_KEY")
    if not api_key_str and not _has_local_speakeasy_auth():
        msg = "SPEAKEASY_API_KEY is not set and the local Speakeasy CLI is not authenticated"
        raise RuntimeError(msg) from None

    # Preflight the generation-path choice BEFORE the fetch adopts a new
    # spec: an explicit host-CLI opt-in with no CLI installed must fail
    # here, not after the tree is already pointing at an unverified spec.
    _preflight_generation_path()

    # Fetch, then gate on overlay health with rollback: speakeasy silently
    # skips broken overlay actions, a manual generate must not ship an SDK
    # that is missing fixes any more than the weekly workflow may, and a
    # failed gate must not leave the tree adopted to an unverified spec.
    # With --no-fetch nothing is adopted, so the gate runs directly.
    if no_fetch:
        _verify_overlay_health(
            skip=skip_overlay_check or _env_flag("SKIP_OVERLAY_CHECK"),
        )
    else:
        await _fetch_then_verify_overlay(
            skip=skip_overlay_check or _env_flag("SKIP_OVERLAY_CHECK"),
        )

    await _generate_sdk(force=force, version=version, api_key_str=api_key_str)


async def cmd_build() -> None:
    """CLI handler for build command.

    Builds inside a container and exports the resulting wheel/sdist back to
    the host's ./dist directory so callers (CI publish step, manual uploads)
    can pick them up.
    """
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        built = pipeline.build()
        _replace_dist_directory()
        await built.directory("/dist").export("./dist")
        print("Build completed successfully (artifacts in ./dist)", file=sys.stderr)


async def cmd_publish() -> None:
    """Build once and publish both SDK distributions with the shared module."""
    if "PYPI_TOKEN" not in os.environ:
        raise RuntimeError("PYPI_TOKEN environment variable not set")
    await cmd_build()
    _publish_artifacts()


async def cmd_ci(
    *,
    force: bool = False,
    version: str | None = None,
    publish: bool = False,
    skip_overlay_check: bool = False,
) -> None:
    """Fetch, generate, test, build, and optionally publish the SDK."""
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    api_key_str = os.environ.get("SPEAKEASY_API_KEY")
    if not api_key_str and not _has_local_speakeasy_auth():
        msg = "SPEAKEASY_API_KEY is not set and the local Speakeasy CLI is not authenticated"
        raise RuntimeError(msg) from None

    # Same preflight as cmd_generate: fail path-selection problems before
    # the fetch adopts anything.
    _preflight_generation_path()

    # Fetch, then gate with rollback — same overlay-health contract as
    # cmd_generate: never generate against a broken overlay, and never
    # leave the tree adopted to one.
    await _fetch_then_verify_overlay(
        skip=skip_overlay_check or _env_flag("SKIP_OVERLAY_CHECK"),
    )

    await _generate_sdk(force=force, version=version, api_key_str=api_key_str)

    # Test and build still run through Dagger, against the freshly generated
    # tree (the source snapshot is re-read after any export).
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        test_output = await pipeline.test()
        print(f"Tests passed\n{test_output}", file=sys.stderr)

        built = pipeline.build()
        _replace_dist_directory()
        await built.directory("/dist").export("./dist")
        print("Build completed successfully (artifacts in ./dist)", file=sys.stderr)

    if publish:
        if "PYPI_TOKEN" not in os.environ:
            raise RuntimeError("PYPI_TOKEN environment variable not set")
        _publish_artifacts()


async def cmd_fetch_openapi() -> None:
    """CLI handler for fetch-openapi command."""
    await fetch_latest_spec()
    print("OpenAPI spec fetched and workflow updated", file=sys.stderr)


async def cmd_check_openapi(*, report: str | None, no_strict: bool) -> None:
    """CLI handler for check-openapi command.

    Delegates to ci/spec_diff.py, which fetches the latest spec into tmp/,
    diffs it against the spec referenced by .speakeasy/workflow.yaml, and
    verifies every overlay target still resolves against the NEW spec
    (speakeasy silently skips non-matching overlay actions, so dead targets
    otherwise go unnoticed). Exit 1 on structural drift or overlay problems
    unless --no-strict, which makes this report-only; environmental errors
    (fetch, parse) still exit 2.
    """
    spec_diff = _load_spec_diff_module()

    argv = ["check"]
    if report:
        argv += ["--report", report]
    if no_strict:
        argv += ["--no-strict"]
    code = spec_diff.main(argv)
    if code:
        raise SystemExit(code)


async def cmd_verify_version(version: str) -> None:
    """CLI handler for verify-version command."""
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        result = await pipeline.verify_version(version=version)
        print(result)


async def cmd_release_bump(version: str) -> None:
    """CLI handler for release-bump command.

    Bumps the version inside a container, then exports the patched files back
    to the host so the caller (scripts/release.sh) can commit, tag, and push.
    """
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        patched = pipeline.release_bump(version=version)
        await patched.export(".")
        print(f"Bumped version to {version}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Attio SDK CI pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "fetch-openapi",
        help="Fetch latest OpenAPI spec and update workflow.yaml",
    )

    check_openapi = sub.add_parser(
        "check-openapi",
        help="Fetch latest spec, diff vs current, and verify overlay health",
    )
    check_openapi.add_argument(
        "--report",
        metavar="PATH",
        help="Write a JSON report (e.g. tmp/spec-check/report.json)",
    )
    check_openapi.add_argument(
        "--no-strict",
        action="store_true",
        help="Exit 0 on drift or overlay problems (report only); "
        "environmental errors still fail",
    )

    sub.add_parser("test", help="Run test suite")
    sub.add_parser("build", help="Build distribution packages")

    verify = sub.add_parser(
        "verify-version",
        help="Verify pyproject.toml + _version.py match the given version",
    )
    verify.add_argument("version", help="Expected version (no leading 'v')")

    bump = sub.add_parser(
        "release-bump",
        help="Bump pyproject.toml + _version.py to a new version",
    )
    bump.add_argument("version", help="Target version (no leading 'v'), e.g. 0.22.9")

    gen = sub.add_parser("generate", help="Generate the SDK via Speakeasy")
    gen.add_argument("--force", action="store_true", help="Force regeneration")
    gen.add_argument(
        "--version",
        metavar="VERSION",
        help="Pin SDK to a specific version",
    )
    gen.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip fetching the spec; use the one referenced by workflow.yaml",
    )
    gen.add_argument(
        "--skip-overlay-check",
        action="store_true",
        help="Bypass the overlay health gate (emergency use; logs loudly)",
    )

    sub.add_parser(
        "publish",
        help="Build and publish the SDK with the shared PyPI publisher",
    )

    ci = sub.add_parser(
        "ci",
        help="Complete CI workflow: fetch, generate, test, build, and publish",
    )
    ci.add_argument("--force", action="store_true", help="Force SDK regeneration")
    ci.add_argument(
        "--version",
        metavar="VERSION",
        help="Pin SDK to a specific version",
    )
    ci.add_argument(
        "--publish",
        action="store_true",
        help="Publish freshly built artifacts with the shared PyPI publisher",
    )
    ci.add_argument(
        "--skip-overlay-check",
        action="store_true",
        help="Bypass the overlay health gate (emergency use; logs loudly)",
    )
    args = parser.parse_args()

    if args.command == "fetch-openapi":
        asyncio.run(cmd_fetch_openapi())
    elif args.command == "check-openapi":
        asyncio.run(
            cmd_check_openapi(report=args.report, no_strict=args.no_strict),
        )
    elif args.command == "verify-version":
        asyncio.run(cmd_verify_version(version=args.version))
    elif args.command == "release-bump":
        asyncio.run(cmd_release_bump(version=args.version))
    elif args.command == "test":
        asyncio.run(cmd_test())
    elif args.command == "build":
        asyncio.run(cmd_build())
    elif args.command == "generate":
        asyncio.run(
            cmd_generate(
                force=args.force,
                version=args.version,
                no_fetch=args.no_fetch,
                skip_overlay_check=args.skip_overlay_check,
            ),
        )
    elif args.command == "publish":
        asyncio.run(cmd_publish())
    elif args.command == "ci":
        asyncio.run(
            cmd_ci(
                force=args.force,
                version=args.version,
                publish=args.publish,
                skip_overlay_check=args.skip_overlay_check,
            ),
        )


if __name__ == "__main__":
    main()
