"""Contract pins for the scheduled spec-update-check workflow.

The workflow's job gating is where the silent-failure bugs live (an `if:`
without a status-check function gets wrapped in an implicit `success() &&`,
so a failure-path notify job can never fire). These tests pin the gating
contract on the parsed YAML so regressions surface in pytest, not in a
Monday-morning incident.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "spec-update-check.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return doc


def test_notify_gating_never_depends_on_implicit_success(workflow: dict) -> None:
    """Without `always() &&` GitHub skips notify exactly when check or
    regenerate failed — the outage case the job exists for."""
    notify_if = " ".join(workflow["jobs"]["notify"]["if"].split())
    assert notify_if.startswith("always() &&"), notify_if
    assert "needs.check.result == 'failure'" in notify_if
    assert "needs.regenerate.result == 'failure'" in notify_if
    # Healthy green weeks run the job too, so a stale attention issue from
    # a previous outage is closed instead of accumulating.
    assert (
        "needs.check.result == 'success' && needs.check.outputs.changed == 'false' "
        "&& needs.check.outputs.overlay_ok == 'true'" in notify_if
    )


def test_notify_waits_for_both_upstream_jobs(workflow: dict) -> None:
    needs = workflow["jobs"]["notify"]["needs"]
    assert needs is not None
    assert set(needs) == {"check", "regenerate"}


def test_notify_if_expression_is_a_disjunction_of_known_clauses(workflow: dict) -> None:
    """The notify `if:` is a long boolean over job results and outputs. A
    small structural edit can silently change when attention issues fire.
    This pins the expression's shape: `always() &&` followed by top-level
    `||` clauses, each matching one of the four known-safe patterns."""
    import re

    def _top_level_clauses(expr: str) -> list[str]:
        """Split on `||` only at paren depth 0 (sub-expressions may contain
        their own `||`)."""
        clauses: list[str] = []
        current: list[str] = []
        depth = 0
        i = 0
        while i < len(expr):
            if expr[i] == "(":
                depth += 1
                current.append(expr[i])
            elif expr[i] == ")":
                depth -= 1
                current.append(expr[i])
            elif depth == 0 and expr[i : i + 4] == " || ":
                clauses.append("".join(current).strip())
                current = []
                i += 4
                continue
            else:
                current.append(expr[i])
            i += 1
        clauses.append("".join(current).strip())
        return clauses

    raw = workflow["jobs"]["notify"]["if"]
    folded = " ".join(raw.split()).removeprefix("always() && (").removesuffix(")")
    clauses = _top_level_clauses(folded)

    allowed_patterns = [
        r"^needs\.check\.result == 'failure'$",
        r"^needs\.regenerate\.result == 'failure'$",
        # a successful regeneration closed the loop with a PR: run to close
        # any stale attention issue
        r"^needs\.regenerate\.result == 'success'$",
        # the "needs a human and regenerate is not handling it" clause
        r"^\(\(needs\.check\.outputs\.changed == 'true' \|\| needs\.check\.outputs\.overlay_ok == 'false'\) && !\(needs\.check\.outputs\.changed == 'true' && needs\.check\.outputs\.overlay_ok == 'true' && needs\.check\.outputs\.has_key == 'true'\)\)$",
        # the healthy-week clause that closes stale attention issues
        r"^\(needs\.check\.result == 'success' && needs\.check\.outputs\.changed == 'false' && needs\.check\.outputs\.overlay_ok == 'true'\)$",
    ]
    assert len(clauses) == 5, clauses
    for clause in clauses:
        assert any(re.fullmatch(p, clause) for p in allowed_patterns), clause


def test_staging_allowlist_covers_gen_lock_generated_top_level() -> None:
    """The workflow stages an explicit allowlist; if Speakeasy ever emits a
    new top-level generated file that the list misses, the leftover guard
    fails the weekly job after regeneration. This pins the list against
    gen.lock's generatedFiles so that drift surfaces in pytest first."""
    import re

    gen_lock = (REPO_ROOT / ".speakeasy" / "gen.lock").read_text(encoding="utf-8")
    lock_match = re.search(r"generatedFiles:\n((?:  - .*\n)+)", gen_lock)
    assert lock_match, "gen.lock generatedFiles section not found"
    generated = {line.strip("- \n") for line in lock_match.group(1).splitlines()}
    top_level = {f for f in generated if "/" not in f}

    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    staging_match = re.search(r"for p in ([\s\S]+?); do", workflow_text)
    assert staging_match, "staging allowlist loop not found in the workflow"
    # The list spans a shell line continuation; split() leaves a stray
    # backslash token, so drop it.
    listed = {
        token for token in staging_match.group(1).split() if token != chr(92)
    }

    missing = top_level - listed - {"pyrightconfig.json"}  # gitignored
    assert not missing, f"generated top-level files not staged: {missing}"


def test_notify_if_truth_table() -> None:
    """Evaluate the notify job's actual `if:` expression over the full
    input combination space by substituting Python values into the YAML
    text, so a semantic edit (not just a structural one) fails here.

    The translation supports a deliberately tiny vocabulary — `==`,
    `&&`, `||`, `!`, and parentheses — asserted by the structural test
    below; any richer syntax in the workflow's `if:` must grow this
    evaluator."""
    import itertools
    import re

    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    raw = " ".join(doc["jobs"]["notify"]["if"].split())
    inner = raw.removeprefix("always() && (").removesuffix(")")
    assert "!=" not in inner  # the ! -> not translation below assumes this
    # Vocabulary closure: after stripping identifiers, string literals, and
    # the supported operators (== && || ! and parentheses), nothing may
    # remain — otherwise the textual translation below silently
    # mis-evaluates.
    residual = re.sub(r"[A-Za-z_.]+|'[^']*'|[().!= &|]", "", inner)
    assert residual == "", f"unsupported tokens in the if: expression: {residual!r}"

    def evaluate(
        check_result: str,
        regen_result: str,
        changed: str,
        overlay_ok: str,
        has_key: str,
    ) -> bool:
        expr = inner
        for name, value in (
            ("needs.check.result", check_result),
            ("needs.regenerate.result", regen_result),
            ("needs.check.outputs.changed", changed),
            ("needs.check.outputs.overlay_ok", overlay_ok),
            ("needs.check.outputs.has_key", has_key),
        ):
            expr = expr.replace(name, repr(value))
        expr = expr.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
        return bool(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 - fixed vocabulary

    for check_result, regen_result, changed, overlay_ok, has_key in itertools.product(
        ("success", "failure"),
        ("success", "failure", "skipped"),
        ("true", "false"),
        ("true", "false"),
        ("true", "false"),
    ):
        runs = evaluate(check_result, regen_result, changed, overlay_ok, has_key)
        expected = (
            check_result == "failure"
            or regen_result == "failure"
            or regen_result == "success"
            or (
                (changed == "true" or overlay_ok == "false")
                and not (changed == "true" and overlay_ok == "true" and has_key == "true")
            )
            or (check_result == "success" and changed == "false" and overlay_ok == "true")
        )
        assert runs == expected, (
            check_result,
            regen_result,
            changed,
            overlay_ok,
            has_key,
        )


def test_regenerate_only_runs_when_automation_can_handle_it(workflow: dict) -> None:
    regen_if = " ".join(workflow["jobs"]["regenerate"]["if"].split())
    for clause in (
        "needs.check.outputs.changed == 'true'",
        "needs.check.outputs.overlay_ok == 'true'",
        "needs.check.outputs.has_key == 'true'",
    ):
        assert clause in regen_if, clause


def test_no_checkout_persists_credentials(workflow: dict) -> None:
    """The regenerate job runs Speakeasy, uv, and pytest on generated code;
    none of them may be able to read a write-capable token from .git/config."""
    for name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            if "uses" not in step or "checkout" not in step["uses"]:
                continue
            assert step.get("with", {}).get("persist-credentials") is False, (
                f"{name}: checkout persists credentials"
            )


def test_actions_are_sha_pinned(workflow: dict) -> None:
    for name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if not uses or uses.startswith("./"):
                continue
            ref = uses.split("@", 1)[1]
            assert len(ref) >= 40 and all(c in "0123456789abcdef" for c in ref), (
                f"{name}: {uses} is not pinned to a commit SHA"
            )


def test_commit_guard_ignores_staged_entries_and_flags_leftovers(workflow: dict) -> None:
    """The "unexpected changes" guard must fire only for what the allowlist
    missed. `git status --porcelain` lists fully-staged entries too, so a
    naive non-empty check would fail every real drift run. This pins the
    exclusion pattern against porcelain's exact output shapes."""
    import re

    commit_step = next(
        s
        for s in workflow["jobs"]["regenerate"]["steps"]
        if s.get("name") == "Commit regenerated SDK"
    )
    match = re.search(r"git status --porcelain \| grep -v '([^']+)'", commit_step["run"])
    assert match, "leftover guard missing from the commit step"
    pattern = match.group(1)

    porcelain_shapes = {
        # Staged with a clean worktree — exactly what regeneration produced.
        "M  src/attio/sdk.py": False,
        "A  docs/models/new.md": False,
        "D  docs/models/old.md": False,
        "R  docs/a.md -> docs/b.md": False,
        # Not covered by the staged allowlist — these are the failures the
        # guard exists to catch.
        "?? stray-cache/": True,
        " M pyproject.toml": True,
        "MM src/attio/sdk.py": True,
    }
    for line, is_leftover in porcelain_shapes.items():
        excluded_by_guard = re.search(pattern, line) is not None
        assert not excluded_by_guard == is_leftover, (
            f"guard misclassifies porcelain line: {line!r}"
        )


def test_speakeasy_installer_is_pinned(workflow: dict) -> None:
    import importlib.util
    import re

    steps = workflow["jobs"]["regenerate"]["steps"]
    install = next(s for s in steps if s.get("name", "").startswith("Install Speakeasy"))
    script = install["run"]
    assert "raw.githubusercontent.com/speakeasy-api/speakeasy/" in script
    assert "/install.sh" in script
    # The URL pins a commit SHA, the checksum verifies the script before it
    # runs, and VERSION freezes the CLI release.
    assert "89688fa0cfc3c959f4ac370329325d1b274db551/install.sh" in script
    assert "9e2c4f1054e214d05352597cfd9ed1ab117a089e9442f532dd4a0d168665d757" in script
    assert "shasum -a 256 -c -" in script
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
    """The embedded jq filters are only ever executed by GitHub, on Mondays.

    This extracts each `jq -r '...'` program from the workflow and compiles
    and runs it locally against a fixture report, so invalid string escapes
    (jq accepts a much smaller set than bash) fail here in pytest instead
    of on the first automated regeneration.
    """
    import json
    import re
    import shutil
    import subprocess

    jq = shutil.which("jq")
    if jq is None:
        pytest.skip("jq not installed")

    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    programs: list[str] = []
    for job in doc["jobs"].values():
        for step in job.get("steps", []):
            programs += re.findall(r"jq -r '([^']+)'", step.get("run", ""))
    # Content-probe the two non-trivial renderers so a regex-extraction
    # truncation (a future program containing a single quote) cannot
    # silently skip them. Together with the report-schema assertions in
    # tests/test_spec_diff.py (which pin the exact key names these filters
    # index), a rename of any .diff/.overlay key fails a test, not a
    # Monday run.
    assert any("Structural drift detected" in p for p in programs), "summary jq missing"
    assert any("operations_added" in p and "pytest green" in p for p in programs), (
        "PR-body jq missing"
    )

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

    for program in programs:
        proc = subprocess.run(
            [jq, "-r", program],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"jq program failed: {program}\n{proc.stderr}"
        assert proc.stdout.strip(), f"jq program rendered nothing: {program}"
