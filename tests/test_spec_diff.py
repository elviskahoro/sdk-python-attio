"""Tests for the spec drift detector (``ci/spec_diff.py``).

These tests pin the three guarantees the scheduled spec-update-check
workflow depends on:

* the mini JSONPath resolver resolves every overlay target syntax (and
  loudly rejects syntax it cannot read),
* the real overlay verifies healthy against the real current spec, and
* each failure mode is actually detected: dead targets, uncovered
  timestamp values, error-code enums that drop spec values, and
  structural (vs description-only) drift — including changes hidden in
  non-schema ``components`` sections and path-item-level parameters.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIFF = REPO_ROOT / "ci" / "spec_diff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("attio_test_spec_diff", SPEC_DIFF)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SD = _load_module()


@pytest.fixture(scope="module")
def real_spec() -> dict:
    return SD.load_spec(SD.current_spec_path())


@pytest.fixture(scope="module")
def real_targets() -> list[str]:
    return SD.load_overlay_targets(SD.OVERLAY_YAML)


# ---------------------------------------------------------------------------
# JSONPath resolver
# ---------------------------------------------------------------------------


DOC = {
    "paths": {
        "/v2/lists/{list}": {
            "get": {
                "parameters": [
                    {"name": "list", "in": "path"},
                    {"name": "limit", "in": "query"},
                ]
            }
        }
    },
    "components": {
        "schemas": {
            "output-value": {
                "anyOf": [
                    {"properties": {"value": {"type": "string"}}},
                    {"properties": {"value": {"type": "string", "format": "date"}}},
                ]
            }
        }
    },
}


def test_resolver_dot_and_bracket_keys() -> None:
    matches = SD.resolve_jsonpath(DOC, "$.components.schemas['output-value'].anyOf[1].properties.value.format")
    assert matches == ["date"]


def test_resolver_index_and_nested_path() -> None:
    matches = SD.resolve_jsonpath(DOC, "$.paths['/v2/lists/{list}'].get.parameters[1].name")
    assert matches == ["limit"]


def test_resolver_filter_expression() -> None:
    matches = SD.resolve_jsonpath(
        DOC, "$.paths['/v2/lists/{list}'].get.parameters[?(@.name=='list')]"
    )
    assert matches == [{"name": "list", "in": "path"}]


def test_resolver_returns_empty_on_no_match() -> None:
    assert SD.resolve_jsonpath(DOC, "$.paths['/v2/missing'].get") == []


def test_resolver_rejects_unsupported_syntax() -> None:
    with pytest.raises(SD.UnsupportedSyntaxError, match="unsupported JSONPath"):
        SD.resolve_jsonpath(DOC, "$..parameters")


def test_resolver_rejects_missing_root() -> None:
    with pytest.raises(SD.UnsupportedSyntaxError, match="does not start with"):
        SD.resolve_jsonpath(DOC, "components.schemas")


# ---------------------------------------------------------------------------
# Overlay parsing + verification against the real spec
# ---------------------------------------------------------------------------


def test_load_overlay_targets_captures_every_declared_action() -> None:
    text = SD.OVERLAY_YAML.read_text(encoding="utf-8")
    declared = len(re.findall(r"^\s*-\s*target:\s", text, re.M))
    targets = SD.load_overlay_targets(SD.OVERLAY_YAML)
    assert len(targets) == declared
    assert all(t.startswith("$") for t in targets)


def test_load_overlay_targets_raises_on_unparsed_actions(tmp_path: Path) -> None:
    """Malformed YAML must fail loudly — there is no drift verdict without
    a readable overlay."""
    probe = tmp_path / "overlay_probe.yaml"
    probe.write_text(
        'overlay: 1.0.0\ninfo: {title: t, version: "0"}\nactions:\n'
        '  - target: "$.a.b"\n    remove: true\n'
        "  - target: [broken\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="not valid YAML"):
        SD.load_overlay_targets(probe)


def test_load_overlay_targets_accepts_unquoted_scalars(tmp_path: Path) -> None:
    """Unquoted target values parse fine through PyYAML — the old regex
    parser silently skipped them, under-reporting what it verified."""
    probe = tmp_path / "overlay_probe.yaml"
    probe.write_text(
        'overlay: 1.0.0\ninfo: {title: t, version: "0"}\nactions:\n'
        '  - target: "$.a.b"\n    remove: true\n'
        "  - target: $.c.d\n    remove: true\n",
        encoding="utf-8",
    )
    assert SD.load_overlay_targets(probe) == ["$.a.b", "$.c.d"]


def test_load_overlay_enum_actions_accepts_flow_style(tmp_path: Path) -> None:
    """Flow-style enum lists parse like block lists — formatting cannot
    silently disable the dropped-error-code check."""
    probe = tmp_path / "overlay_probe.yaml"
    probe.write_text(
        'overlay: 1.0.0\ninfo: {title: t, version: "0"}\nactions:\n'
        "  - target: $.a.code\n"
        "    update:\n"
        "      type: string\n"
        "      enum: [value_not_found, validation_type]\n",
        encoding="utf-8",
    )
    actions = SD.load_overlay_enum_actions(probe)
    assert actions == {"$.a.code": ["value_not_found", "validation_type"]}


def test_load_overlay_actions_requires_string_targets(tmp_path: Path) -> None:
    probe = tmp_path / "overlay_probe.yaml"
    probe.write_text(
        'overlay: 1.0.0\ninfo: {title: t, version: "0"}\nactions:\n'
        "  - remove: true\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="without a string target"):
        SD.load_overlay_targets(probe)


def test_real_overlay_verifies_healthy_against_current_spec(
    real_spec: dict, real_targets: list[str]
) -> None:
    enum_actions = SD.load_overlay_enum_actions(SD.OVERLAY_YAML)
    health = SD.verify_overlay(real_spec, real_targets, enum_actions)
    assert health["healthy"], json.dumps(
        {k: v for k, v in health.items() if k != "healthy"}, indent=2
    )


def test_current_spec_timestamp_trail_count_is_pinned(real_spec: dict) -> None:
    """Pin the number of timestamp value surfaces in the current spec.

    Detection relies on Attio's descriptions naming "ISO 8601" (or on
    time-like examples under ``.value``); if Attio rewords a description, a
    real timestamp node silently stops being detected and the
    uncovered-timestamp guard under-reports. A count drop fails here,
    loudly, instead."""
    trails = SD.find_timestamp_value_trails(real_spec)
    # 22 endpoint oneOf[16] value surfaces + input-value/output-value
    # anyOf[18] components. Update this number when the spec legitimately
    # gains or loses timestamp surfaces (and extend the overlay to match).
    assert len(trails) == 24, "\n".join(trails)


def test_flatten_actions_are_parsed_with_expected_enums() -> None:
    actions = SD.load_overlay_enum_actions(SD.OVERLAY_YAML)
    post = "$.paths['/v2/objects/{object}/records'].post.responses['400'].content['application/json'].schema.properties.code"
    put = "$.paths['/v2/objects/{object}/records'].put.responses['400'].content['application/json'].schema.properties.code"
    assert post in actions
    assert put in actions
    assert "validation_type" in actions[post]
    assert "particle_gate_violation" in actions[put]


# ---------------------------------------------------------------------------
# Failure detection on mutated specs
# ---------------------------------------------------------------------------


def test_verify_overlay_flags_dead_target(real_spec: dict, real_targets: list[str]) -> None:
    spec = copy.deepcopy(real_spec)
    del spec["components"]["schemas"]["output-value"]

    health = SD.verify_overlay(spec, real_targets, {})
    assert health["healthy"] is False
    assert any("output-value" in t for t in health["dead_targets"])


def test_verify_overlay_flags_uncovered_timestamp_value(
    real_spec: dict, real_targets: list[str]
) -> None:
    spec = copy.deepcopy(real_spec)
    # A timestamp surface NOT named `value` — only the ISO 8601 description
    # identifies it, which is why detection must not require a .value trail.
    spec["components"]["schemas"]["probe-timestamp"] = {
        "type": "object",
        "properties": {
            "deadline": {
                "type": "string",
                "format": "date",
                "description": "A timestamp value in ISO 8601 format.",
            }
        },
    }

    health = SD.verify_overlay(spec, real_targets, {})
    assert health["healthy"] is False
    assert "$.components.schemas['probe-timestamp'].properties.deadline" in health[
        "uncovered_timestamp_values"
    ]


def test_verify_overlay_flags_dead_format_action_as_uncovered(
    real_spec: dict, real_targets: list[str]
) -> None:
    """A timestamp value whose .format removal target went dead must be
    reported uncovered, not silently covered by the dead action."""
    spec = copy.deepcopy(real_spec)
    # Shift the oneOf index the overlay targets for POST records (16 -> 15):
    # the .format removal now either matches a different node or nothing, and
    # the timestamp value (now at index 15) has no live coverage either way.
    one_of = (
        spec["paths"]["/v2/objects/{object}/records"]["post"]["responses"]["200"]
        ["content"]["application/json"]["schema"]["properties"]["data"]["properties"]
        ["values"]["additionalProperties"]["items"]["oneOf"]
    )
    one_of.insert(15, one_of.pop(16))

    health = SD.verify_overlay(spec, real_targets, {})
    assert health["healthy"] is False
    # The moved timestamp value is uncovered at its new position...
    assert any(
        t.endswith("oneOf[15].properties.value")
        for t in health["uncovered_timestamp_values"]
    )
    # ...and any stale index-16 action that still resolves is flagged as
    # landing on a non-timestamp node (collateral damage), never counted
    # as coverage.
    assert health["misdirected_targets"] == [] or all(
        "oneOf[16]" in t for t in health["misdirected_targets"]
    )


def test_verify_overlay_flags_misdirected_format_action(
    real_spec: dict, real_targets: list[str]
) -> None:
    """An upstream reorder can keep an old index alive but pointing at a
    different union member: the live `.format` removal then strips
    `format: date` from a genuine date-only field. That must be reported
    as a misdirected target, not silently applied."""
    spec = copy.deepcopy(real_spec)
    one_of = (
        spec["paths"]["/v2/objects/{object}/records"]["post"]["responses"]["200"]
        ["content"]["application/json"]["schema"]["properties"]["data"]["properties"]
        ["values"]["additionalProperties"]["items"]["oneOf"]
    )
    # Move the timestamp (16) onto a slot whose target stays resolvable but
    # points at another member with a `value` — simulate by swapping two
    # members and keeping a .format-bearing non-timestamp node at index 16.
    timestamp = one_of[16]
    neighbor = one_of[15]
    # Give the neighbor's value a plain date format without ISO 8601 docs.
    neighbor_props = neighbor.setdefault("properties", {})
    neighbor_props["value"] = {
        "type": "string",
        "format": "date",
        "description": "A calendar date, no time component.",
    }
    one_of[15], one_of[16] = timestamp, neighbor

    health = SD.verify_overlay(spec, real_targets, {})
    assert health["healthy"] is False
    assert any(
        "oneOf[16].properties.value.format" in t for t in health["misdirected_targets"]
    ), health["misdirected_targets"]


def test_verify_overlay_flags_dropped_error_code(
    real_spec: dict, real_targets: list[str]
) -> None:
    spec = copy.deepcopy(real_spec)
    code = spec["paths"]["/v2/objects/{object}/records"]["post"]["responses"]["400"][
        "content"
    ]["application/json"]["schema"]["properties"]["code"]
    code["anyOf"].append({"type": "string", "enum": ["brand_new_code"]})

    enum_actions = SD.load_overlay_enum_actions(SD.OVERLAY_YAML)
    health = SD.verify_overlay(spec, real_targets, enum_actions)
    assert health["healthy"] is False
    assert any(
        "brand_new_code" in note for note in health["dropped_error_codes"]
    ), health["dropped_error_codes"]


def test_flat_enum_to_anyof_migration_reports_dead_target(
    real_spec: dict, real_targets: list[str]
) -> None:
    """When Attio migrates a flat `.code.enum` endpoint to an anyOf union,
    the old-style overlay target stops matching and must surface as a dead
    target — the check still fails loudly — rather than passing silently."""
    target = (
        "$.paths['/v2/objects/records/search'].post.responses['400']"
        ".content['application/json'].schema.properties.code.enum"
    )
    assert target in real_targets  # the old-style action under test

    spec = copy.deepcopy(real_spec)
    code = (
        spec["paths"]["/v2/objects/records/search"]["post"]["responses"]["400"]
        ["content"]["application/json"]["schema"]["properties"]["code"]
    )
    assert "enum" in code  # still flat in the current spec
    values = code.pop("enum")
    code["anyOf"] = [
        {"type": "string", "enum": values},
        {"type": "string", "enum": ["brand_new_code"]},
    ]

    health = SD.verify_overlay(spec, real_targets, SD.load_overlay_enum_actions())
    assert health["healthy"] is False
    assert target in health["dead_targets"]


def test_union_error_codes_ignores_plain_enums_and_non_unions() -> None:
    assert SD._union_error_codes({"type": "string", "enum": ["a"]}) is None
    assert SD._union_error_codes({"type": "string"}) is None
    assert SD._union_error_codes(["not", "a", "dict"]) is None
    values = SD._union_error_codes(
        {"anyOf": [{"enum": ["a"]}, {"enum": ["b"]}, {"type": "string"}]}
    )
    assert values == ["a", "b"]
    # Single-value variants may be written as `const` instead of one-element
    # `enum`; they contribute the same value.
    const_values = SD._union_error_codes({"anyOf": [{"const": "solo"}, {"enum": ["a"]}]})
    assert const_values == ["solo", "a"]


# ---------------------------------------------------------------------------
# Structural diff classification
# ---------------------------------------------------------------------------


def _mini_spec(*, description: str = "docs", extra_param: bool = False) -> dict:
    parameters = [{"name": "a", "in": "query"}]
    if extra_param:
        parameters.append({"name": "b", "in": "query"})
    return {
        "openapi": "3.1.0",
        "paths": {
            "/p": {
                "get": {
                    "operationId": "x",
                    "description": description,
                    "parameters": parameters,
                    "responses": {
                        "200": {
                            "description": "OK docs",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "properties": {}}
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {"Thing": {"type": "object", "properties": {}}},
            "parameters": {
                "PageSize": {"name": "page_size", "in": "query", "schema": {"type": "integer"}}
            },
        },
    }


def test_description_only_changes_are_not_structural() -> None:
    old = _mini_spec()
    new = _mini_spec(description="entirely new marketing copy")
    # Also reword a nested description (response description) — still doc-only.
    new["paths"]["/p"]["get"]["responses"]["200"]["description"] = "new response docs"

    diff = SD.structural_diff(old, new)
    assert diff["has_structural_changes"] is False
    assert diff["description_only_changes"] == ["GET /p"]


def test_nested_schema_description_change_is_not_structural() -> None:
    old = _mini_spec()
    new = _mini_spec()
    new["components"]["schemas"]["Thing"]["description"] = "new nested docs"

    diff = SD.structural_diff(old, new)
    assert diff["has_structural_changes"] is False
    assert "component schemas/Thing" in diff["description_only_changes"]


def test_parameter_change_is_structural() -> None:
    diff = SD.structural_diff(_mini_spec(), _mini_spec(extra_param=True))
    assert diff["has_structural_changes"] is True
    assert "GET /p" in diff["operations_changed"]


def test_component_parameter_section_change_is_structural() -> None:
    old = _mini_spec()
    new = _mini_spec()
    new["components"]["parameters"]["PageSize"]["schema"]["type"] = "number"

    diff = SD.structural_diff(old, new)
    assert diff["has_structural_changes"] is True
    assert "parameters/PageSize" in diff["components_changed"]


def test_path_item_level_parameter_change_is_structural() -> None:
    old = _mini_spec()
    new = _mini_spec()
    new["paths"]["/p"]["parameters"] = [{"name": "shared", "in": "query"}]

    diff = SD.structural_diff(old, new)
    assert diff["has_structural_changes"] is True
    assert "/p" in diff["path_items_changed"]


def test_added_and_removed_operations() -> None:
    old = _mini_spec()
    new = _mini_spec()
    new["paths"]["/p"]["post"] = {"operationId": "y", "responses": {}}

    diff = SD.structural_diff(old, new)
    assert diff["operations_added"] == ["POST /p"]

    diff_back = SD.structural_diff(new, old)
    assert diff_back["operations_removed"] == ["POST /p"]


def test_less_common_methods_count_as_operations() -> None:
    old = _mini_spec()
    new = _mini_spec()
    new["paths"]["/p"]["options"] = {"responses": {"204": {"description": "no content"}}}

    diff = SD.structural_diff(old, new)
    assert "OPTIONS /p" in diff["operations_added"]


def test_new_path_expands_into_per_method_operations() -> None:
    """A brand-new endpoint must appear in the per-method lists the workflow
    summaries and PR body render — not only in `paths_added`."""
    old = _mini_spec()
    new = _mini_spec()
    new["paths"]["/brand/new"] = {
        "get": {"responses": {"200": {"description": "ok"}}},
        "post": {"responses": {"201": {"description": "created"}}},
    }

    diff = SD.structural_diff(old, new)
    assert diff["paths_added"] == ["/brand/new"]
    assert diff["operations_added"] == ["GET /brand/new", "POST /brand/new"]


# ---------------------------------------------------------------------------
# cmd_check exit codes and the report schema the workflow's jq depends on
# ---------------------------------------------------------------------------


def test_fetch_rejects_json_that_is_not_an_openapi_document() -> None:
    """An HTTP 200 error envelope must read as a fetch problem (exit 2),
    not as a catastrophic-looking upstream deletion."""
    for bad in ({"error": "envelope"}, {}, {"openapi": "3.1.0"}, {"openapi": "3.1.0", "paths": {}}):
        with pytest.raises(RuntimeError, match="not a usable OpenAPI document"):
            SD._assert_openapi_document(bad)
    # A minimal real document passes.
    SD._assert_openapi_document({"openapi": "3.1.0", "paths": {"/x": {}}})


def test_cmd_check_exit_codes_and_report_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mini = {"openapi": "3.1.0", "info": {"title": "t", "version": "1"}, "paths": {}}
    drifted = copy.deepcopy(mini)
    drifted["paths"]["/new"] = {"get": {"responses": {"200": {"description": "ok"}}}}

    current = tmp_path / "current.json"
    current.write_text(json.dumps(mini), encoding="utf-8")

    monkeypatch.setattr(SD, "current_spec_path", lambda: current)
    monkeypatch.setattr(SD, "TMP_DIR", tmp_path)
    monkeypatch.setattr(SD, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SD, "load_overlay_targets", lambda *a, **k: ["$.info.title"])
    monkeypatch.setattr(SD, "load_overlay_enum_actions", lambda *a, **k: {})

    def fake_fetch(spec: dict):
        def _fetch(dest: Path) -> Path:
            dest.write_text(json.dumps(spec), encoding="utf-8")
            return dest

        return _fetch

    # No drift: exit 0, and every key the workflow's jq reads is present.
    monkeypatch.setattr(SD, "fetch_latest_spec", fake_fetch(mini))
    report = tmp_path / "report.json"
    assert SD.main(["check", "--report", str(report)]) == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["structural_changes"] is False
    assert data["overlay"]["healthy"] is True
    assert data["overlay"]["dead_targets"] == []
    assert data["overlay"]["misdirected_targets"] == []
    for key in (
        "operations_added",
        "operations_removed",
        "operations_changed",
        "path_items_changed",
        "components_added",
        "components_removed",
        "components_changed",
        "top_level_changed",
        "description_only_changes",
    ):
        assert key in data["diff"], key

    # Drift: exit 1 strict, 0 with --no-strict; new paths land in the
    # per-method lists.
    monkeypatch.setattr(SD, "fetch_latest_spec", fake_fetch(drifted))
    report = tmp_path / "report2.json"
    assert SD.main(["check", "--report", str(report)]) == 1
    assert SD.main(["check", "--no-strict"]) == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["structural_changes"] is True
    assert data["diff"]["paths_added"] == ["/new"]
    assert data["diff"]["operations_added"] == ["GET /new"]

    # Environmental failure: fetch error exits 2 even with --no-strict.
    def boom(dest: Path) -> Path:
        raise RuntimeError("network down")

    monkeypatch.setattr(SD, "fetch_latest_spec", boom)
    assert SD.main(["check", "--no-strict"]) == 2
    assert SD.main(["check"]) == 2
    # The temp spec file is cleaned up either way.
    assert not list(tmp_path.glob("spec-check-*.json"))


def test_cmd_check_flags_timestamp_detection_regression(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A drop in detected timestamp surfaces vs the baseline must block
    (unhealthy overlay) with an explanatory note — those values would
    otherwise regenerate as `date` while the check reports healthy."""

    def iso_surface(description: str = "A timestamp value in ISO 8601 format.") -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {
                    "type": "string",
                    "format": "date",
                    "description": description,
                }
            },
        }

    baseline = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {},
        "components": {"schemas": {"a": iso_surface(), "b": iso_surface()}},
    }
    # Fetched: one timestamp surface reworded away from detection.
    fetched = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {},
        "components": {
            "schemas": {"a": iso_surface(), "b": iso_surface("A moment.")}
        },
    }

    current = tmp_path / "current.json"
    current.write_text(json.dumps(baseline), encoding="utf-8")

    monkeypatch.setattr(SD, "current_spec_path", lambda: current)
    monkeypatch.setattr(SD, "TMP_DIR", tmp_path)
    monkeypatch.setattr(SD, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(SD, "load_overlay_targets", lambda *a, **k: ["$.info.title"])
    monkeypatch.setattr(SD, "load_overlay_enum_actions", lambda *a, **k: {})

    def fake_fetch(dest: Path) -> Path:
        dest.write_text(json.dumps(fetched), encoding="utf-8")
        return dest

    monkeypatch.setattr(SD, "fetch_latest_spec", fake_fetch)

    report = tmp_path / "report.json"
    assert SD.main(["check", "--report", str(report)]) == 1
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["timestamp_trail_count"] == 1
    assert data["overlay"]["healthy"] is False
    assert any(
        "detection regression" in note for note in data["overlay"]["uncovered_timestamp_values"]
    )


def test_strip_doc_keys_is_recursive() -> None:
    node = {
        "description": "top",
        "summary": "also top",
        "properties": {
            "a": {"type": "string", "description": "nested"},
            "b": {"summary": "nested summary", "type": "integer"},
        },
        "items": [{"description": "in a list", "x": 1}],
    }
    stripped = SD.strip_doc_keys(node)
    assert stripped == {
        "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
        "items": [{"x": 1}],
    }
    # The input is not mutated.
    assert node["properties"]["a"]["description"] == "nested"


def test_strip_doc_keys_never_strips_schema_field_names() -> None:
    """A schema property literally named `description` is an API surface,
    not prose — stripping it would hide real drift from the check."""
    node = {
        "description": "schema docs",
        "properties": {
            "description": {"type": "string", "description": "field docs"},
        },
    }
    stripped = SD.strip_doc_keys(node)
    # The `description` PROPERTY is kept; its inner prose is still stripped.
    assert stripped == {"properties": {"description": {"type": "string"}}}


def test_schema_property_named_description_is_structural() -> None:
    old = _mini_spec()
    new = _mini_spec()
    new["components"]["schemas"]["Thing"]["properties"] = {
        "description": {"type": "string"}
    }

    diff = SD.structural_diff(old, new)
    assert diff["has_structural_changes"] is True
    assert "schemas/Thing" in diff["components_changed"]
