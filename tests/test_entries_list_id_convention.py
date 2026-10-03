"""Guard the ``list`` -> ``list_id`` overlay-rename convention across the SDK.

``overlay.yaml`` applies ``x-speakeasy-name-override: "list_id"`` to every ``list``
path/query parameter so the generated SDK exposes ``list_id`` (avoiding shadowing
Python's built-in ``list``) while keeping the wire name ``list``. This is the
documented convention (AGENTS.md: "The `list` → `list_id` renames avoid shadowing
Python's built-in `list`") and the maintainers' post-regen checklist asks:
"Do the `list` parameter rename targets still match?"

The convention broke once before: a spec bump (commit 0773aa5) added
`PUT /v2/lists/{list}/entries/{entry_id}/attributes/{attribute}/values` but the
automated regen did not update `overlay.yaml`, so the new endpoint regenerated with
a `list: str` parameter and callers using the sibling `list_id=` convention got
`TypeError`.

This test automates that checklist: for every ``list`` parameter in the active
OpenAPI spec, a matching ``x-speakeasy-name-override: "list_id"`` action must exist
in ``overlay.yaml``. It reads source files only (the overlay and the spec), not the
generated SDK, so it stays valid across regenerations and flags the exact regression
mode that introduced the bug.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".speakeasy" / "workflow.yaml"
OVERLAY = REPO_ROOT / "overlay.yaml"

# Operations that can carry path/query parameters.
HTTP_METHODS = {"get", "put", "post", "patch", "delete", "head", "options"}


def _active_spec_path() -> Path:
    """The base spec that ``workflow.yaml`` feeds the generator (its first input)."""
    # Minimal parse: the first `location:` under `inputs:` pointing at openapi/<spec>.json.
    for line in WORKFLOW.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- location:") or stripped.startswith("location:"):
            value = stripped.split("location:", 1)[1].strip().strip('"').strip("'")
            if value.startswith("openapi/") and value.endswith(".json") and "-overlay" not in value:
                return REPO_ROOT / value
    raise AssertionError(
        "Could not determine the active OpenAPI spec from .speakeasy/workflow.yaml "
        "(expected an `inputs[].location: openapi/api-*.json` entry)."
    )


def _overlay_list_id_targets() -> set[tuple[str, str]]:
    """(method, path) pairs covered by a `x-speakeasy-name-override: "list_id"` action."""
    text = OVERLAY.read_text()
    covered: set[tuple[str, str]] = set()
    # Each action begins with `  - target: "<jsonpath>"`.
    for block in re.split(r"\n  - target: ", text)[1:]:
        target = block.split("\n", 1)[0].strip().strip('"').strip("'")
        if 'x-speakeasy-name-override: "list_id"' not in block:
            continue
        match = re.search(r"paths\['([^']+)'\]\.(\w+)\.parameters", target)
        if match:
            covered.add((match.group(2), match.group(1)))
    return covered


def _spec_list_param_endpoints(spec_path: Path) -> list[tuple[str, str, str]]:
    """All (method, path, location) for `list` params in the given spec."""
    spec = json.loads(spec_path.read_text())
    found: list[tuple[str, str, str]] = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if method not in HTTP_METHODS or not isinstance(op, dict):
                continue
            for prm in op.get("parameters", []):
                if isinstance(prm, dict) and prm.get("name") == "list":
                    found.append((method, path, prm.get("in", "?")))
    return found


def test_every_list_param_has_a_list_id_overlay_rename():
    """Every `list` param in the active spec must have a `list_id` overlay action.

    This is the automated form of the AGENTS.md post-regen check "Do the `list`
    parameter rename targets still match?" A failure means a spec bump introduced a
    `list`-scoped endpoint whose `list` parameter would regenerate as `list` (shadowing
    the builtin) instead of the convention's `list_id`.
    """
    spec_path = _active_spec_path()
    spec_list_params = _spec_list_param_endpoints(spec_path)
    covered = _overlay_list_id_targets()

    uncovered = [
        (method, path, location)
        for method, path, location in spec_list_params
        if (method, path) not in covered
    ]

    assert not uncovered, (
        f"{len(spec_list_params)} `list` parameters in {spec_path.name} but "
        f"{len(uncovered)} have no `x-speakeasy-name-override: \"list_id\"` action in "
        f"overlay.yaml (the convention from AGENTS.md): {uncovered}"
    )

    # Sanity: the convention is actually in use somewhere.
    assert covered, "overlay.yaml has no `list_id` rename actions at all"
