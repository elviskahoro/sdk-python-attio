#!/usr/bin/env python3
"""Attio SDK Dagger CI pipeline with object-oriented design and snapshots.

Available commands:
    fetch-openapi                  Fetch latest OpenAPI spec and update workflow.yaml
    verify-version <version>       Verify pyproject.toml + _version.py match <version>
    release-bump <version>         Rewrite pyproject.toml + _version.py to <version>
    test                           Run test suite
    build                          Build distribution packages
    generate [--force] [--version] Generate SDK via Speakeasy
    publish                        Build and publish to PyPI
    ci [--force] [--version] [...] Complete workflow: fetch, generate, test, build, optionally publish

Examples:
    python ci/pipeline.py fetch-openapi
    python ci/pipeline.py verify-version 0.22.9
    python ci/pipeline.py release-bump 0.22.9
    python ci/pipeline.py test
    python ci/pipeline.py generate --force --version 1.0.0
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
from typing import Annotated

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


def _sync_write_spec(spec_path: str, spec_data: dict[str, object]) -> None:
    """Write OpenAPI spec to disk (synchronous)."""
    Path(spec_path).parent.mkdir(parents=True, exist_ok=True)
    Path(spec_path).write_text(json.dumps(spec_data, indent=2))


def _sync_update_workflow(overlay_path: str, spec_path: str) -> None:
    """Update workflow.yaml (synchronous)."""
    import re

    workflow_content = Path(".speakeasy/workflow.yaml").read_text()

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

    Path(".speakeasy/workflow.yaml").write_text(workflow_content)


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
    result = subprocess.run(
        ["speakeasy", "auth", "status"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


async def _run_local_speakeasy(*, version: str | None) -> None:
    """Run generation with the authenticated host CLI session."""
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
        raise RuntimeError("dist/ does not exist; run the build command before publishing")
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
            .with_exec(["/bin/sh", "-c", "mkdir -p /work /dist && cp -a /repo/. /work/"])
            .with_workdir("/work")
            .with_exec(["uv", "build", "--out-dir", "/dist"])
        )
        return (
            staged.with_exec(["python", "-c", _GTM_PACKAGE_VARIANT_SCRIPT])
            .with_exec(["uv", "build", "--out-dir", "/dist"])
        )

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


async def cmd_generate(*, force: bool, version: str | None) -> None:
    """Fetch, generate, and export the SDK into the local working tree."""
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    api_key_str = os.environ.get("SPEAKEASY_API_KEY")
    if not api_key_str and not _has_local_speakeasy_auth():
        msg = "SPEAKEASY_API_KEY is not set and the local Speakeasy CLI is not authenticated"
        raise RuntimeError(msg) from None

    await fetch_latest_spec()
    if not api_key_str:
        _ = force
        await _run_local_speakeasy(version=version)
        _apply_post_generation_patches()
        print("SDK generated with the local Speakeasy CLI", file=sys.stderr)
        return

    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        api_key = dag.set_secret("SPEAKEASY_API_KEY", api_key_str)
        source_dir = _host_source_dir()
        pipeline = AttioSDKPipeline(source=source_dir)
        generated = await pipeline.generate(api_key=api_key, force=force, version=version)
        await generated.export("./src")
        _apply_post_generation_patches()
        print("SDK generated and exported to ./src", file=sys.stderr)


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
) -> None:
    """Fetch, generate, test, build, and optionally publish the SDK."""
    import os

    os.environ.setdefault("DAGGER_PROGRESS", "plain")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    api_key_str = os.environ.get("SPEAKEASY_API_KEY")
    if not api_key_str and not _has_local_speakeasy_auth():
        msg = "SPEAKEASY_API_KEY is not set and the local Speakeasy CLI is not authenticated"
        raise RuntimeError(msg) from None

    await fetch_latest_spec()
    async with dagger.connection(dagger.Config(log_output=sys.stderr)):
        if api_key_str:
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
        else:
            _ = force
            await _run_local_speakeasy(version=version)
            _apply_post_generation_patches()
            print("SDK generated with the local Speakeasy CLI", file=sys.stderr)

        # Re-read the host directory after export so test/build consume the
        # generated SDK rather than Dagger's pre-generation source snapshot.
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
    args = parser.parse_args()

    if args.command == "fetch-openapi":
        asyncio.run(cmd_fetch_openapi())
    elif args.command == "verify-version":
        asyncio.run(cmd_verify_version(version=args.version))
    elif args.command == "release-bump":
        asyncio.run(cmd_release_bump(version=args.version))
    elif args.command == "test":
        asyncio.run(cmd_test())
    elif args.command == "build":
        asyncio.run(cmd_build())
    elif args.command == "generate":
        asyncio.run(cmd_generate(force=args.force, version=args.version))
    elif args.command == "publish":
        asyncio.run(cmd_publish())
    elif args.command == "ci":
        asyncio.run(
            cmd_ci(
                force=args.force,
                version=args.version,
                publish=args.publish,
            ),
        )


if __name__ == "__main__":
    main()
