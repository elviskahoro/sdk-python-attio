"""Dagger pin lockstep across the repo.

``pyproject.toml`` pins ``dagger-io``; the three check workflows install the
Dagger CLI (``v=`` in ``dagger-cli-install``) and pre-pull the matching engine
image (``dagger-engine-warm``); ``.rwx/publish.yml`` installs the same CLI and
``ci/README.md`` documents the version. A partial bump fails silently: bump
the CLI pin alone and the warm task still runs (its ``use`` input changed) but
pulls the old image, so the consuming task pays the cold pull anyway. This
test makes that drift loud, in the spirit of
``test_post_generate_patch.py::test_committed_versions_are_in_lockstep``.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_WORKFLOWS = (".rwx/pytest.yml", ".rwx/pyright.yml", ".rwx/pyrefly.yml")


def _dagger_io_version() -> str:
    match = re.search(
        r'"dagger-io ==(\d+\.\d+\.\d+)"', (REPO_ROOT / "pyproject.toml").read_text()
    )
    assert match, "pyproject.toml lost the `dagger-io ==<version>` dev pin"
    return match[1]


def _dagger_tarball_checksum(text: str) -> str:
    match = re.search(r'echo "([0-9a-f]{64})  /tmp/dagger\.tgz"', text)
    assert match, "no checksum-pinned dagger tarball download found"
    return match[1]


def test_check_workflow_dagger_pins_are_in_lockstep() -> None:
    version = _dagger_io_version()
    for workflow in CHECK_WORKFLOWS:
        text = (REPO_ROOT / workflow).read_text()
        assert f"v={version}" in text, (
            f"{workflow}: `dagger-cli-install` no longer pins the CLI at v={version}"
        )
        assert f"registry.dagger.io/engine:v{version}" in text, (
            f"{workflow}: `dagger-engine-warm` no longer pre-pulls engine:v{version}"
        )


def test_publish_workflow_installs_the_same_dagger_cli() -> None:
    version = _dagger_io_version()
    text = (REPO_ROOT / ".rwx" / "publish.yml").read_text()
    assert f"releases/{version}/dagger_v{version}_linux_amd64.tar.gz" in text, (
        f".rwx/publish.yml no longer installs dagger {version}"
    )


def test_dagger_tarball_checksums_are_identical() -> None:
    workflows = CHECK_WORKFLOWS + (".rwx/publish.yml",)
    checksums = {
        workflow: _dagger_tarball_checksum((REPO_ROOT / workflow).read_text())
        for workflow in workflows
    }
    assert len(set(checksums.values())) == 1, f"checksums drifted: {checksums}"


def test_ci_docs_name_the_pinned_dagger_version() -> None:
    version = _dagger_io_version()
    readme = (REPO_ROOT / "ci" / "README.md").read_text()
    assert f"dagger-io=={version}" in readme, (
        "ci/README.md no longer names the pinned dagger-io version"
    )
