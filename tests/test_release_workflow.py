"""Contract pins for the one-command RWX release workflow.

``rwx dispatch release --ref main`` tags and publishes the version already
committed on main. Its safety properties (dispatch-only, no Speakeasy, no push
to main, idempotent re-runs) only show up at release time, so pin them here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".rwx" / "release.yml"
GITHUB_TOKEN_REFERENCE = (
    "vaults.sdk-python-attio-release.github-apps.rwx-automation-elviskahoro.token"  # nosec B105 - vault reference, not a credential
)


@pytest.fixture(scope="module")
def doc() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tasks(doc: dict) -> dict[str, dict]:
    return {task["key"]: task for task in doc["tasks"]}


def test_dispatch_is_the_only_trigger(doc: dict) -> None:
    """A `cli` or push trigger could start from an unmerged commit and tag or
    publish it; dispatch pins the run to the ref the vaults release to."""
    triggers = doc[True]  # YAML 1.1 parses `on` as True
    assert set(triggers) == {"dispatch"}
    assert [t["key"] for t in triggers["dispatch"]] == ["release"]
    assert triggers["dispatch"][0]["init"]["commit-sha"] == "${{ event.git.sha }}"


def test_no_speakeasy(doc: dict) -> None:
    """Bumps come from the regeneration pipeline; releasing must never need
    the approval-gated SPEAKEASY_API_KEY."""
    task_text = str(doc["tasks"])
    assert "SPEAKEASY" not in task_text
    assert "vaults.sdk-python-attio.secrets" not in task_text


def test_github_token_reaches_only_tag(doc: dict) -> None:
    holders = [
        task["key"]
        for task in doc["tasks"]
        if GITHUB_TOKEN_REFERENCE in str(task.get("env", {}))
    ]
    assert holders == ["tag"]


def test_no_stored_github_secret(doc: dict) -> None:
    """GitHub write access comes from the vault's GitHub App (a per-run
    installation token), never from a stored PAT secret."""
    assert "secrets.GITHUB_TOKEN" not in str(doc["tasks"])


def test_pypi_tokens_stay_in_publish_yml() -> None:
    """The upload chain is embedded, not copied, so release.yml never sees
    the PyPI tokens itself."""
    assert "PYPI_TOKEN" not in str(
        yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["tasks"]
    )


def test_only_the_release_tag_is_pushed(tasks: dict[str, dict]) -> None:
    pushes = [
        (key, line.strip())
        for key, task in tasks.items()
        for line in str(task.get("run", "")).splitlines()
        if re.search(r"\bgit\b.*\bpush\b|^\s*push\s", line)
    ]
    assert [key for key, _ in pushes] == ["tag"], pushes
    [(_, line)] = pushes
    assert '"refs/tags/${TAG}:refs/tags/${TAG}"' in line
    assert "main" not in line
    assert "--force" not in line and " -f " not in line


def test_tag_is_annotated_and_never_moved(tasks: dict[str, dict]) -> None:
    tag = tasks["tag"]
    assert re.search(r"git tag -a ", tag["run"])
    assert "-f" not in re.findall(r"git tag (.*)", tag["run"])[0].split()
    assert "tag-exists != 'true'" in tag["if"]


def test_publish_embeds_publish_yml_at_preflight_sha_and_tag(
    tasks: dict[str, dict],
) -> None:
    publish = tasks["publish"]
    assert publish["call"] == "${{ run.dir }}/publish.yml"
    assert publish["init"] == {
        "commit-sha": "${{ tasks.preflight.values.release-sha }}",
        "tag": "${{ tasks.preflight.values.tag }}",
    }
    # Waits for the tag push, but still runs when the tag already existed.
    assert publish["after"] == "${{ tag.succeeded || tag.skipped }}"


@pytest.mark.parametrize("key", ["tag", "publish", "verify"])
def test_already_published_versions_stop_after_preflight(
    tasks: dict[str, dict], key: str
) -> None:
    assert "tasks.preflight.values.published != 'true'" in tasks[key]["if"]


def test_preflight_writes_every_value_read_downstream(tasks: dict[str, dict]) -> None:
    run = tasks["preflight"]["run"]
    read = set(
        re.findall(
            r"tasks\.preflight\.values\.([\w-]+)",
            str({k: v for k, v in tasks.items() if k != "preflight"}),
        )
    )
    assert read
    for name in read:
        assert f'> "$RWX_VALUES/{name}"' in run, name


@pytest.mark.parametrize("key", ["preflight", "tag", "verify"])
def test_external_state_tasks_are_uncached(tasks: dict[str, dict], key: str) -> None:
    """A cache hit would replay a stale PyPI/tag check or skip the push."""
    assert tasks[key]["cache"] is False


def test_release_runs_one_at_a_time(doc: dict) -> None:
    pools = doc["concurrency-pools"]
    assert pools == [
        {
            "id": "elviskahoro/sdk-python-attio:release",
            "capacity": 1,
            "on-overflow": "queue",
        }
    ]


def _verify_script() -> str:
    """The verify loop lives in Dagger (ci/main.py), not in the YAML."""
    import ast

    tree = ast.parse((REPO_ROOT / "ci" / "main.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_RELEASE_VERIFY_SCRIPT"
            for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("_RELEASE_VERIFY_SCRIPT not found in ci/main.py")


@pytest.mark.parametrize(
    ("key", "command"),
    [("preflight", "release-status"), ("verify", "release-verify")],
)
def test_pypi_checks_run_in_dagger(
    tasks: dict[str, dict], key: str, command: str
) -> None:
    """The PyPI checks and smoke tests run through the Dagger CI core; RWX
    only orchestrates them."""
    task = tasks[key]
    assert f"ci/run.sh {command} " in task["run"]
    assert task["docker"] is True
    assert task["use"] == "sync"
    assert "pypi.org" not in task["run"]


def test_verify_smoke_tests_both_cli_names() -> None:
    script = _verify_script()
    assert "for cmd in attio gtm-attio" in script
    assert 'uvx --refresh "$cmd@$VERSION" --version' in script


def test_pypi_checks_require_every_artifact() -> None:
    """A bare "version exists" check would treat a partial upload as done,
    and preflight would then skip the publish that finishes it."""
    main = (REPO_ROOT / "ci" / "main.py").read_text(encoding="utf-8")
    assert '["python", "ci/pypi_release_status.py", ns.version]' in main
    assert "python ci/pypi_release_status.py" in _verify_script()


def test_verify_timeout_outlasts_its_retry_budget(tasks: dict[str, dict]) -> None:
    """RWX SIGKILLs on timeout, so a slow but successful release would end red
    if the timeout were shorter than the polling and uvx retry loops (plus
    Dagger engine start-up)."""
    run = _verify_script()
    polls = int(re.search(r"seq 1 (\d+)", run).group(1))
    poll_sleep = int(re.search(r"sleep (\d+)\ndone\n", run).group(1))
    uvx_attempts = len(re.search(r"for attempt in ([\d ]+); do", run).group(1).split())
    uvx_sleep = int(re.findall(r"sleep (\d+)", run)[-1])
    budget_seconds = polls * poll_sleep + 2 * uvx_attempts * uvx_sleep
    timeout_minutes = int(str(tasks["verify"]["timeout"]).rstrip("m"))
    assert timeout_minutes * 60 >= budget_seconds + 5 * 60, budget_seconds
