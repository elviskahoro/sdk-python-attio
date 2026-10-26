"""Contract pins for the on-demand regenerate RWX workflow.

Regressions in its load-bearing settings would otherwise only surface at
the next manual ``rwx run .rwx/regenerate.yml``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".rwx" / "regenerate.yml"
VAULT_KEY_REFERENCE = "vaults.sdk-python-attio.secrets.SPEAKEASY_API_KEY"


@pytest.fixture(scope="module")
def tasks() -> dict[str, dict]:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return {task["key"]: task for task in doc["tasks"]}


def test_generate_is_uncached(tasks: dict[str, dict]) -> None:
    """RWX keys the cache on content, so a cached generate would replay stale
    output at an unchanged SHA instead of calling Speakeasy."""
    assert tasks["generate"]["cache"] is False


def test_speakeasy_key_reaches_only_generate() -> None:
    """The installer, uv, mypy, and pytest must never see the credential."""
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    holders = [
        task["key"]
        for task in doc["tasks"]
        if VAULT_KEY_REFERENCE in str(task.get("env", {}))
    ]
    assert holders == ["generate"]


@pytest.mark.parametrize("key", ["generate", "verify"])
def test_long_tasks_have_explicit_timeouts(tasks: dict[str, dict], key: str) -> None:
    """A timeout SIGKILLs the task and skips patch, so no artifact appears."""
    timeout = tasks[key]["timeout"]
    assert int(str(timeout).rstrip("m")) > 10, key


def test_no_github_write_token() -> None:
    """The pipeline only exports a patch; it never pushes or opens a PR."""
    assert "GITHUB_TOKEN" not in WORKFLOW.read_text(encoding="utf-8")
