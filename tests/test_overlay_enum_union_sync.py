"""Two-way sync of overlay ``enum`` replacements against spec code unions.

``verify_overlay`` (run by ``test_spec_diff.py`` against the pinned spec)
already fails PRs when an overlay enum drops a code the spec's ``anyOf``
union carries. This file adds what that one-way check deliberately omits:
overlay values the spec never lists (rot, unless it is the intentional
``validation_type`` extra), a guard that every enum action still lands on a
union, and a paste-ready fix message. The comparison itself lives in
``ci/spec_diff.py:_check_error_code_sync`` so the two gates cannot drift.
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
    return SD._check_error_code_sync(spec, enum_actions, INTENTIONAL_EXTRAS)  # noqa: SLF001


def targets_without_union(spec: dict, enum_actions: dict[str, list[str]]) -> list[str]:
    """Enum-action targets that resolve to no union node (misdirected)."""
    return [
        t
        for t in enum_actions
        if not any(
            SD._union_error_codes(n) for n in SD.resolve_jsonpath(spec, t)  # noqa: SLF001
        )
    ]


@pytest.fixture(scope="module")
def spec() -> dict:
    return SD.load_spec(SD.current_spec_path())


@pytest.fixture(scope="module")
def enum_actions() -> dict[str, list[str]]:
    return SD.load_overlay_enum_actions()


def test_overlay_enums_match_spec_unions(spec, enum_actions):
    problems = union_sync_problems(spec, enum_actions)
    assert not problems, "overlay enum drifted from spec union:\n" + "\n".join(problems)


def test_every_enum_action_hits_a_union(spec, enum_actions):
    assert enum_actions, "overlay has no enum actions; the sync test is vacuous"
    misdirected = targets_without_union(spec, enum_actions)
    assert not misdirected, (
        "overlay enum action(s) no longer resolve to a spec anyOf/oneOf union:\n"
        + "\n".join(misdirected)
    )


_SYNTH_SPEC = {"a": {"code": {"anyOf": [{"enum": ["x"]}, {"enum": ["y"]}]}}}


def test_reports_dropped_code():
    problems = union_sync_problems(_SYNTH_SPEC, {"$.a.code": ["x"]})
    assert len(problems) == 1
    assert "['y']" in problems[0]
    assert "['x', 'y']" in problems[0]


def test_reports_unknown_extra_but_allows_validation_type():
    ok = {"$.a.code": ["x", "y", "validation_type"]}
    assert union_sync_problems(_SYNTH_SPEC, ok) == []
    problems = union_sync_problems(_SYNTH_SPEC, {"$.a.code": ["x", "y", "bogus"]})
    assert len(problems) == 1
    assert "['bogus']" in problems[0]


def test_fix_message_does_not_duplicate_validation_type():
    spec = {"a": {"code": {"anyOf": [{"enum": ["x"]}, {"enum": ["validation_type"]}]}}}
    problems = union_sync_problems(spec, {"$.a.code": ["validation_type"]})
    assert len(problems) == 1
    assert "['x', 'validation_type']" in problems[0]


def test_flags_target_that_is_not_a_union():
    spec = {"a": {"code": {"enum": ["x"]}}}
    assert targets_without_union(spec, {"$.a.code": ["x"]}) == ["$.a.code"]
