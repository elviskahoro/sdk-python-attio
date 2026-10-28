"""Contract pins for the scheduled spec-update-check RWX workflow.

The workflow's failure handling is where the silent-failure bugs live: a
task that fails skips every task reading its values, so the notify task
could never fire in the outage case. These tests pin that contract on the
parsed YAML so regressions surface in pytest, not in a Monday-morning
incident.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".rwx" / "spec-update-check.yml"
JQ_DIR = REPO_ROOT / "ci" / "spec_check"


@pytest.fixture(scope="module")
def tasks() -> dict[str, dict]:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return {task["key"]: task for task in doc["tasks"]}


def test_regenerate_failure_does_not_fail_the_task(tasks: dict[str, dict]) -> None:
    """notify reads regenerate's values, so a failed regenerate task would
    skip it. The task must record `failure` and still exit 0."""
    run = tasks["regenerate"]["run"]
    assert 'echo failure > "$RWX_VALUES/result"' in run
    assert re.search(r"trap '.*exit 0' EXIT", run), "regenerate must exit 0 on failure"


def test_regenerate_initializes_every_value_open_pr_reads(tasks: dict[str, dict]) -> None:
    """open-pr resolves regenerate's `result` and `branch`; a value missing on
    an early-exit path leaves open-pr (and so notify) unable to start."""
    run = tasks["regenerate"]["run"]
    first_exit = run.index("exit 0")
    names = re.findall(r"tasks\.regenerate\.values\.([\w-]+)", str(tasks["open-pr"]["env"]))
    assert names
    for name in names:
        assert f'> "$RWX_VALUES/{name}"' in run[:first_exit], name


def test_check_records_hard_failures_instead_of_failing(tasks: dict[str, dict]) -> None:
    """A failing check task skips regenerate/open-pr/notify/verdict, so no
    attention issue would open. Values are written before any fallible
    command and an EXIT trap records the failure."""
    run = tasks["check"]["run"]
    assert re.search(r"trap '.*check-failed.*exit 0' EXIT", run)
    assert run.index('echo true > "$RWX_VALUES/check-failed"') < run.index("mkdir -p")


@pytest.mark.parametrize("key", ["check", "notify", "verdict"])
def test_live_tasks_are_uncached(tasks: dict[str, dict], key: str) -> None:
    """RWX caches on content only; at an unchanged main SHA a cached task
    would replay last week's verdict without contacting Attio."""
    assert tasks[key]["cache"] is False


def test_notify_reads_both_upstream_tasks(tasks: dict[str, dict]) -> None:
    env = tasks["notify"]["env"]
    assert "tasks.check.values.check-failed" in env["CHECK_FAILED"]
    assert "tasks.open-pr.values.result" in env["REGEN_RESULT"]


def test_verdict_fails_the_run_after_notify(tasks: dict[str, dict]) -> None:
    verdict = tasks["verdict"]
    assert verdict["after"] == ["notify"]
    assert "exit 1" in verdict["run"]
    assert 'REGEN_RESULT" = "failure"' in verdict["run"]
    assert 'CHECK_FAILED" = "true"' in verdict["run"]
    assert 'OVERLAY_OK" = "false"' in verdict["run"]


def test_check_fails_fast_on_skip_overlay_check(tasks: dict[str, dict]) -> None:
    """The escape hatch must never ride the weekly automation, and the
    guard's exit 1 deliberately precedes the value writes: a forbidden
    configuration fails the run outright instead of opening an issue."""
    run = tasks["check"]["run"]
    assert 'case "${SKIP_OVERLAY_CHECK:-}" in' in run
    assert run.index('case "${SKIP_OVERLAY_CHECK:-}"') < run.index('> "$RWX_VALUES/')


def test_skip_overlay_guard_rejects_every_truthy_spelling(
    tasks: dict[str, dict],
) -> None:
    """Only genuinely-false values may fall through the guard's allow arm;
    anything ci/pipeline.py::_env_flag treats as enabled must be rejected."""
    run = tasks["check"]["run"]
    arm = next(
        line.strip().removesuffix(") ;;")
        for line in run.splitlines()
        if line.strip().startswith('""|')
    )
    allowed = {value.lower() for value in arm.split("|")}
    assert allowed == {'""', "0", "false", "no"}
    assert not allowed & {"1", "true", "yes"}


def test_write_token_is_scoped_to_repo_operations(tasks: dict[str, dict]) -> None:
    """Speakeasy, uv, and pytest run in `check`/`regenerate`; neither may
    see the repo-write token. Only open-pr, cleanup, and notify (issues) hold it."""
    holders = {
        key for key, task in tasks.items() if "secrets.GITHUB_TOKEN" in str(task.get("env", {}))
    }
    assert holders == {"open-pr", "notify", "cleanup"}


def test_publish_requires_manual_start() -> None:
    doc = yaml.safe_load((REPO_ROOT / ".rwx" / "publish.yml").read_text(encoding="utf-8"))
    # PyYAML parses the bare `on` key as boolean True.
    tag_triggers = doc[True]["github"]["push"]
    assert all(t.get("start") == "manually" for t in tag_triggers)


def test_publish_uploads_only_for_tag_runs() -> None:
    """`start: manually` gates only the GitHub tag trigger; a CLI run has an
    empty tag and must not reach the PyPI upload."""
    doc = yaml.safe_load((REPO_ROOT / ".rwx" / "publish.yml").read_text(encoding="utf-8"))
    publish = next(t for t in doc["tasks"] if t["key"] == "publish")
    assert publish["if"] == "${{ init.tag != '' }}"
    assert doc[True]["cli"]["init"]["tag"] == ""


def test_publish_chain_survives_skipped_version_check() -> None:
    """CLI runs skip verify-version; test must still run, and the long
    Dagger tasks need an explicit timeout above RWX's 10m default."""
    doc = yaml.safe_load((REPO_ROOT / ".rwx" / "publish.yml").read_text(encoding="utf-8"))
    by_key = {t["key"]: t for t in doc["tasks"]}
    assert "verify-version.skipped" in by_key["test"]["after"]
    for key in ("verify-version", "test", "build"):
        assert by_key[key]["timeout"] == "30m", key


@pytest.mark.parametrize("key", ["fetch-spec", "generate", "regenerate"])
def test_regeneration_stages_have_explicit_timeout(tasks: dict[str, dict], key: str) -> None:
    """A timeout SIGKILLs the task past its EXIT trap, so the 10m default
    must not apply to the regeneration stages."""
    assert tasks[key]["timeout"] == "60m"


def test_speakeasy_key_reaches_only_the_generate_task(tasks: dict[str, dict]) -> None:
    """The installer, spec fetch, uv, and pytest must not see the key."""
    holders = {k for k, t in tasks.items() if "SPEAKEASY_API_KEY" in t.get("env", {})}
    assert holders == {"check", "generate"}
    assert "ci/pipeline.py generate" in tasks["generate"]["run"]
    for key in ("fetch-spec", "regenerate"):
        assert "ci/pipeline.py generate" not in tasks[key]["run"], key


@pytest.mark.parametrize("key", ["check", "generate"])
def test_speakeasy_key_reads_from_the_project_vault(tasks: dict[str, dict], key: str) -> None:
    """`secrets.*` resolves from the `default` vault, which lacks the key."""
    assert (
        tasks[key]["env"]["SPEAKEASY_API_KEY"]
        == "${{ vaults.sdk-python-attio.secrets.SPEAKEASY_API_KEY }}"
    )


@pytest.mark.parametrize("key", ["fetch-spec", "generate", "regenerate"])
def test_regeneration_stages_record_failure_and_skip_cleanly(
    tasks: dict[str, dict], key: str
) -> None:
    run = tasks[key]["run"]
    assert 'echo failure > "$RWX_VALUES/result"' in run
    assert re.search(r"trap '.*exit 0' EXIT", run)
    assert run.index('> "$RWX_VALUES/result"') < run.index("exit 0")


def test_publish_installs_pinned_twine_before_the_token() -> None:
    doc = yaml.safe_load((REPO_ROOT / ".rwx" / "publish.yml").read_text(encoding="utf-8"))
    by_key = {t["key"]: t for t in doc["tasks"]}
    assert re.search(r"twine==\d", by_key["twine"]["run"])
    assert "secrets" not in str(by_key["twine"])
    assert by_key["publish"]["use"] == "twine"
    assert "uvx" not in by_key["publish"]["run"]


def test_regenerate_only_runs_when_automation_can_handle_it(tasks: dict[str, dict]) -> None:
    run = tasks["fetch-spec"]["run"]
    skip_guard = next(line for line in run.splitlines() if "CHECK_FAILED" in line and "exit" not in line)
    for clause in (
        '"$CHECK_FAILED" = "true"',
        '"$CHANGED" != "true"',
        '"$OVERLAY_OK" != "true"',
        '"$HAS_KEY" != "true"',
    ):
        assert clause in skip_guard, clause


def test_staging_allowlist_covers_generated_tree(tasks: dict[str, dict]) -> None:
    """The workflow stages an explicit allowlist; Speakeasy writes everything
    it owns under generated/ (gen.lock lives there too), so staging that one
    directory must cover every file gen.lock claims."""
    gen_lock = (REPO_ROOT / "generated" / ".speakeasy" / "gen.lock").read_text(
        encoding="utf-8",
    )
    assert re.search(r"generatedFiles:\n((?:  - .*\n)+)", gen_lock), (
        "gen.lock generatedFiles section not found"
    )

    staging_match = re.search(r"for p in ([\s\S]+?); do", tasks["regenerate"]["run"])
    assert staging_match, "staging allowlist loop not found in the workflow"
    listed = {token for token in staging_match.group(1).split() if token != chr(92)}

    assert "generated" in listed, "generated/ is not staged by the workflow"


def test_commit_guard_ignores_staged_entries_and_flags_leftovers(
    tasks: dict[str, dict],
) -> None:
    """The "unexpected changes" guard must fire only for what the allowlist
    missed. `git status --porcelain` lists fully-staged entries too, so a
    naive non-empty check would fail every real drift run."""
    match = re.search(
        r"git status --porcelain \| grep -v '([^']+)'",
        tasks["regenerate"]["run"],
    )
    assert match, "leftover guard missing from the regenerate task"
    pattern = match.group(1)

    porcelain_shapes = {
        "M  generated/src/attio/sdk.py": False,
        "A  docs/models/new.md": False,
        "D  docs/models/old.md": False,
        "R  docs/a.md -> docs/b.md": False,
        "?? stray-cache/": True,
        " M pyproject.toml": True,
        "MM generated/src/attio/sdk.py": True,
    }
    for line, is_leftover in porcelain_shapes.items():
        excluded_by_guard = re.search(pattern, line) is not None
        assert not excluded_by_guard == is_leftover, (
            f"guard misclassifies porcelain line: {line!r}"
        )


def test_speakeasy_installer_is_pinned(tasks: dict[str, dict]) -> None:
    import importlib.util

    script = tasks["fetch-spec"]["run"]
    assert "raw.githubusercontent.com/speakeasy-api/speakeasy/" in script
    assert "/install.sh" in script
    # The URL pins a commit SHA, the checksum verifies the script before it
    # runs, and VERSION freezes the CLI release.
    assert "89688fa0cfc3c959f4ac370329325d1b274db551/install.sh" in script
    assert "9e2c4f1054e214d05352597cfd9ed1ab117a089e9442f532dd4a0d168665d757" in script
    assert "sha256sum -c -" in script
    assert "VERSION=1.800.1" in script

    # The workflow's CLI pin and the pipeline's version-drift warning must
    # agree, or the warning compares against the wrong version.
    pipeline_path = REPO_ROOT / "ci" / "pipeline.py"
    spec = importlib.util.spec_from_file_location("attio_test_pipeline_pin", pipeline_path)
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    workflow_version = re.search(r"VERSION=(\S+)", script).group(1)
    assert workflow_version == pipeline._SPEAKEASY_CLI_PIN

    # speakeasyVersion in workflow.yaml is what stops `speakeasy run` from
    # self-upgrading to latest; it must match the other pins.
    speakeasy_workflow = yaml.safe_load(
        (REPO_ROOT / ".speakeasy" / "workflow.yaml").read_text(encoding="utf-8")
    )
    assert str(speakeasy_workflow["speakeasyVersion"]) == pipeline._SPEAKEASY_CLI_PIN


def test_every_jq_program_runs_clean_against_a_sample_report() -> None:
    """The jq filters only ever run on Mondays in RWX. This compiles and runs
    each against a fixture report, so invalid string escapes (jq accepts a
    much smaller set than bash) fail here in pytest instead of on the first
    automated regeneration.
    """
    jq = shutil.which("jq")
    if jq is None:
        pytest.skip("jq not installed")

    summary = (JQ_DIR / "summary.jq").read_text(encoding="utf-8")
    pr_body = (JQ_DIR / "pr-body.jq").read_text(encoding="utf-8")
    # Content-probe both renderers. Together with the report-schema
    # assertions in tests/test_spec_diff.py (which pin the exact key names
    # these filters index), a rename of any .diff/.overlay key fails a
    # test, not a Monday run.
    assert "Structural drift detected" in summary, "summary jq missing"
    assert "operations_added" in pr_body and "pytest green" in pr_body, "PR-body jq missing"

    report = {
        "current_spec": "openapi/api-test.json",
        "structural_changes": True,
        "diff": {
            "paths_added": ["/new"],
            "paths_removed": [],
            "operations_added": ["GET /new"],
            "operations_removed": [],
            "operations_changed": {"GET /p": ["note"]},
            "path_items_changed": {"/p": ["note"]},
            "description_only_changes": ["GET /doc"],
            "components_added": ["schemas/New"],
            "components_removed": [],
            "components_changed": {"schemas/Old": ["note"]},
            "top_level_changed": {"servers": ["note"]},
        },
        "overlay": {
            "healthy": False,
            "dead_targets": ["$.dead"],
            "uncovered_timestamp_values": ["$.uncovered"],
            "misdirected_targets": ["$.misdirected.format"],
            "dropped_error_codes": ["$.code drops value_x"],
        },
    }
    payload = json.dumps(report)

    for program in (summary, pr_body):
        proc = subprocess.run(  # noqa: S603 - fixed argv
            [jq, "-r", program],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"jq program failed: {program}\n{proc.stderr}"
        assert proc.stdout.strip(), f"jq program rendered nothing: {program}"


def test_publish_dagger_is_pinned_and_verified_and_upload_uncached() -> None:
    doc = yaml.safe_load((REPO_ROOT / ".rwx" / "publish.yml").read_text(encoding="utf-8"))
    by_key = {t["key"]: t for t in doc["tasks"]}
    run = by_key["dagger-cli"]["run"]
    assert "install.sh" not in run
    assert re.search(r"releases/\d+\.\d+\.\d+/", run)
    assert re.search(r"[0-9a-f]{64}  /tmp/dagger.tgz", run)
    assert "sha256sum -c -" in run
    assert by_key["publish"]["cache"] is False


def test_open_pr_initializes_every_value_downstream_tasks_read(
    tasks: dict[str, dict],
) -> None:
    """notify and verdict resolve open-pr's values; one missing on an early
    exit path leaves them unable to start."""
    run = tasks["open-pr"]["run"]
    first_exit = run.index("exit 0")
    names = set()
    for key in ("notify", "verdict"):
        names |= set(re.findall(r"tasks\.open-pr\.values\.([\w-]+)", str(tasks[key]["env"])))
    assert names
    for name in names:
        assert f'> "$RWX_VALUES/{name}"' in run[:first_exit], name


def test_twine_is_on_path_for_publish() -> None:
    doc = yaml.safe_load((REPO_ROOT / ".rwx" / "publish.yml").read_text(encoding="utf-8"))
    twine = next(t for t in doc["tasks"] if t["key"] == "twine")
    assert '.local/bin" >> "$RWX_ENV/PATH"' in twine["run"]


def test_cleanup_deletes_only_branches_without_a_pr(tasks: dict[str, dict]) -> None:
    cleanup = tasks["cleanup"]
    assert "open-pr.failed" in cleanup["after"]
    assert "gh pr list --head" in cleanup["run"]
    assert "--delete" in cleanup["run"]
