"""Offline guard that overlay ``enum`` replacements match the spec's code unions.

``ci/spec_diff.py:_check_error_code_sync`` only runs from the network-fetching
``check-openapi`` / ``check-overlay`` commands. This lifts the same check into
pytest so an overlay edit that drops a code the pinned spec's ``anyOf`` union
still carries fails on the PR, not in the weekly ``spec-update-check``.

Both directions are pinned: a spec code missing from the overlay enum drops it
from the generated ``Literal`` (``ResponseValidationError`` at runtime), and an
overlay value the spec never lists is rot — except ``validation_type``, the
intentional extra the overlay adds.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIFF = REPO_ROOT / "ci" / "spec_diff.py"

INTENTIONAL_EXTRAS = frozenset({"validation_type"})


def _load_module():
    spec = importlib.util.spec_from_file_location("attio_test_enum_sync", SPEC_DIFF)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SD = _load_module()


def union_sync_problems(spec: dict, enum_actions: dict[str, list[str]]) -> list[str]:
    """Return one message per overlay enum that disagrees with its spec union."""
    problems: list[str] = []
    for target, overlay_values in enum_actions.items():
        for node in SD.resolve_jsonpath(spec, target):
            spec_values = SD._union_error_codes(node)  # noqa: SLF001
            if spec_values is None:
                continue
            missing = [v for v in dict.fromkeys(spec_values) if v not in overlay_values]
            extra = [
                v
                for v in dict.fromkeys(overlay_values)
                if v not in spec_values and v not in INTENTIONAL_EXTRAS
            ]
            if not (missing or extra):
                continue
            fixed = list(dict.fromkeys(spec_values))
            if any(v in overlay_values for v in INTENTIONAL_EXTRAS):
                fixed += sorted(INTENTIONAL_EXTRAS & set(overlay_values))
            problems.append(
                f"{target}: missing from overlay {missing}, "
                f"not in spec union {extra}. Fix: set the overlay enum to {fixed}",
            )
    return problems


@pytest.fixture(scope="module")
def spec() -> dict:
    return SD.load_spec(SD.current_spec_path())


@pytest.fixture(scope="module")
def enum_actions() -> dict[str, list[str]]:
    return SD.load_overlay_enum_actions()


def test_overlay_enums_match_spec_unions(spec, enum_actions):
    problems = union_sync_problems(spec, enum_actions)
    assert not problems, "overlay enum drifted from spec union:\n" + "\n".join(problems)


def test_enum_actions_actually_hit_unions(spec, enum_actions):
    hits = [
        t
        for t in enum_actions
        if any(SD._union_error_codes(n) for n in SD.resolve_jsonpath(spec, t))  # noqa: SLF001
    ]
    assert hits, "no overlay enum action resolves to a spec union; the sync test is vacuous"


_SYNTH_SPEC = {"a": {"code": {"anyOf": [{"enum": ["x"]}, {"enum": ["y"]}]}}}


def test_reports_dropped_code():
    problems = union_sync_problems(_SYNTH_SPEC, {"$.a.code": ["x"]})
    assert len(problems) == 1
    assert "['y']" in problems[0]
    assert "['x', 'y']" in problems[0]


def test_reports_unknown_extra_but_allows_validation_type():
    assert union_sync_problems(_SYNTH_SPEC, {"$.a.code": ["x", "y", "validation_type"]}) == []
    problems = union_sync_problems(_SYNTH_SPEC, {"$.a.code": ["x", "y", "bogus"]})
    assert len(problems) == 1
    assert "['bogus']" in problems[0]
