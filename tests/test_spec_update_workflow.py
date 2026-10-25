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
    assert "echo failure > \"$RWX_VALUES/result\"" in run
    assert re.search(r"trap '.*exit 0' EXIT", run), "regenerate must exit 0 on failure"


def test_notify_reads_both_upstream_tasks(tasks: dict[str, dict]) -> None:
    env = tasks["notify"]["env"]
    assert "tasks.check.values.check-failed" in env["CHECK_FAILED"]
    assert "tasks.regenerate.values.result" in env["REGEN_RESULT"]


def test_verdict_fails_the_run_after_notify(tasks: dict[str, dict]) -> None:
    verdict = tasks["verdict"]
    assert verdict["after"] == ["notify"]
    assert "exit 1" in verdict["run"]
    assert 'REGEN_RESULT" = "failure"' in verdict["run"]
    assert 'CHECK_FAILED" = "true"' in verdict["run"]


def test_regenerate_only_runs_when_automation_can_handle_it(tasks: dict[str, dict]) -> None:
    run = tasks["regenerate"]["run"]
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

    script = tasks["regenerate"]["run"]
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
