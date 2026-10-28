"""Contract pins for the RWX status checks that gate the merge queue.

``.trunk/trunk.yaml``'s ``merge.required_statuses`` must match the
``status-checks.name`` values that ``.rwx/`` run definitions actually post;
drift there surfaces as a silent merge-queue stall (branch protection waits
out its test timeout), not as a red pytest.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RWX_DIR = REPO_ROOT / ".rwx"
TRUNK_YAML = REPO_ROOT / ".trunk" / "trunk.yaml"
INTEGRATION_WORKFLOW = RWX_DIR / "integration.yml"
LOCKED_VAULT_TOKEN = "vaults.sdk-python-attio.secrets.ATTIO_API_TOKEN"  # nosec B105 - vault reference, not a credential


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _github_triggers(doc: dict) -> dict:
    # PyYAML (YAML 1.1) parses the unquoted `on:` key as boolean True.
    on = doc.get(True) or doc.get("on") or {}
    return on.get("github") or {}


def _declared_status_names(gh: dict) -> list[str]:
    """Names declared via ``status-checks: name:`` on github triggers."""
    names: list[str] = []
    pull_request = gh.get("pull_request")
    if isinstance(pull_request, dict):
        checks = pull_request.get("status-checks")
        if isinstance(checks, dict) and "name" in checks:
            names.append(checks["name"])
    for push in gh.get("push") or []:
        if not isinstance(push, dict):
            continue
        checks = push.get("status-checks")
        if isinstance(checks, dict) and "name" in checks:
            names.append(checks["name"])
    return names


def _workflow_names() -> dict[str, list[str]]:
    """Declared status-check names per ``.rwx/`` run definition."""
    return {
        path.name: _declared_status_names(_github_triggers(_load(path)))
        for path in sorted(RWX_DIR.glob("*.yml"))
    }


@pytest.fixture(scope="module")
def required_statuses() -> list[str]:
    return _load(TRUNK_YAML)["merge"]["required_statuses"]


def test_every_required_rwx_status_is_declared_by_a_workflow(
    required_statuses: list[str],
) -> None:
    """A required ``RWX: *`` name that no ``.rwx/`` workflow posts never
    turns green, so the queue times the PR out instead of merging it."""
    declared = {name for names in _workflow_names().values() for name in names}
    missing = [
        status
        for status in required_statuses
        if status.startswith("RWX: ") and status.removeprefix("RWX: ") not in declared
    ]
    assert not missing, missing


def test_only_rwx_statuses_are_required(required_statuses: list[str]) -> None:
    """Externally posted checks (e.g. ``pullfrog-approval``) report on PR
    heads but never on the queue's test branches, so requiring one deadlocks
    the queue on "Waiting for status to be reported"."""
    external = [s for s in required_statuses if not s.startswith("RWX: ")]
    assert not external, external


def test_required_workflows_declare_one_name_across_triggers(
    required_statuses: list[str],
) -> None:
    """PR and push triggers must post the same name, or PRs and queue pushes
    report different checks and one of them never satisfies protection."""
    required = {
        status.removeprefix("RWX: ")
        for status in required_statuses
        if status.startswith("RWX: ")
    }
    for filename, names in _workflow_names().items():
        overlap = required.intersection(names)
        if not overlap:
            continue
        assert set(names) == overlap, (
            f"{filename} mixes required and non-required status names: {names}"
        )


def test_integration_fires_only_where_the_locked_vault_is_readable() -> None:
    """The sdk-python-attio vault is locked to main, so pull_request and
    trunk-merge/** refs can never resolve ATTIO_API_TOKEN; firing there
    would post a permanently red ``RWX: integration`` on every PR."""
    gh = _github_triggers(_load(INTEGRATION_WORKFLOW))
    assert "pull_request" not in gh
    pushes = gh.get("push") or []
    assert pushes, "expected the main-push trigger to remain"
    for push in pushes:
        assert push.get("if") == "${{ event.git.branch == 'main' }}", push


def test_integration_is_uncached_and_token_stays_scoped() -> None:
    """RWX keys the cache on content only, so a cached live-API task would
    replay a stale verdict at an unchanged SHA; and the vault token must
    reach only the integration task."""
    doc = _load(INTEGRATION_WORKFLOW)
    tasks = {task["key"]: task for task in doc["tasks"]}
    assert tasks["integration"]["cache"] is False
    holders = [
        key
        for key, task in tasks.items()
        if LOCKED_VAULT_TOKEN in str(task.get("env", {}))
    ]
    assert holders == ["integration"]


def test_integration_discards_stdout() -> None:
    """tests/test_live_api.py prints workspace people, emails and members;
    dropping the redirect would copy them into retained main-branch logs
    while every status stays green."""
    doc = _load(INTEGRATION_WORKFLOW)
    tasks = {task["key"]: task for task in doc["tasks"]}
    assert "> /dev/null" in tasks["integration"]["run"]
