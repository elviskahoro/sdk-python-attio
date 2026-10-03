#!/usr/bin/env python3
"""Detect upstream OpenAPI spec drift and overlay rot for the Attio SDK.

Speakeasy silently skips overlay actions whose JSONPath targets no longer
match, and upstream spec edits (new endpoints, error-schema reshuffles) are
otherwise invisible until someone re-runs generation by hand. This module
makes both failure modes loud, with three commands:

    diff OLD.json NEW.json           Structural diff between two spec files
    check-overlay [SPEC] [OVERLAY]   Verify overlay targets resolve, every
                                     timestamp value has a live .format
                                     removal, and error-code enums stay in
                                     sync with the spec's anyOf unions
    check [--report PATH] [--no-strict]
                                     Fetch the latest spec from
                                     https://api.attio.com/openapi/api, diff it
                                     against the spec referenced by
                                     .speakeasy/workflow.yaml, and verify the
                                     overlay still applies to the NEW spec.
                                     Exit 1 on structural drift or overlay
                                     problems (unless --no-strict).

``check`` is the entrypoint for humans and for the scheduled
spec-update-check GitHub workflow. It never writes to ``openapi/``; the
fetched spec lands in ``tmp/`` and is deleted afterwards.

Exit codes (``check``):
    0  fetched spec is structurally identical and overlay is healthy
    1  structural drift and/or overlay problems detected
    2  environmental failure (fetch error, unreadable files)

Dependency footprint: the JSONPath resolution is dependency-free; the
spec fetch uses httpx (a main dependency of the SDK) and overlay parsing
uses PyYAML (a dev dependency, declared in gen.yaml so regeneration
preserves it — run this module through ``uv run``). workflow.yaml is read
with a targeted regex (a stable, single-key file). Unknown JSONPath
syntax raises ``UnsupportedSyntaxError`` so new overlay constructs fail
loudly here instead of silently passing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_URL = "https://api.attio.com/openapi/api"
WORKFLOW_YAML = REPO_ROOT / ".speakeasy" / "workflow.yaml"
OVERLAY_YAML = REPO_ROOT / "overlay.yaml"
TMP_DIR = REPO_ROOT / "tmp"

# Short bound for values rendered into diff notes.
_NOTE_MAX = 60


class UnsupportedSyntaxError(RuntimeError):
    """Raised when an overlay target uses JSONPath syntax this tool cannot resolve."""


# ---------------------------------------------------------------------------
# Spec loading / fetching
# ---------------------------------------------------------------------------


def load_spec(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        return json.load(fh)


def current_spec_path() -> Path:
    """Return the spec file referenced by .speakeasy/workflow.yaml."""
    text = WORKFLOW_YAML.read_text(encoding="utf-8")
    match = re.search(r"location:\s*(openapi/api-[\d]+\.json)", text)
    if not match:
        msg = f"could not find 'location: openapi/api-*.json' in {WORKFLOW_YAML}"
        raise RuntimeError(msg)
    return REPO_ROOT / match.group(1)


def _assert_openapi_document(doc: Any) -> None:  # noqa: ANN401 - arbitrary JSON
    """Reject JSON that is not a usable OpenAPI document.

    An HTTP 200 error envelope or empty object would otherwise diff as
    "every path and component removed" — a catastrophic-looking upstream
    deletion that is really a fetch problem.
    """
    if (
        not isinstance(doc, dict)
        or not isinstance(doc.get("openapi"), str)
        or not isinstance(doc.get("paths"), dict)
        or not doc["paths"]
    ):
        msg = (
            "fetched payload is JSON but not a usable OpenAPI document "
            "(expected an `openapi` version string and a non-empty `paths` mapping)"
        )
        raise RuntimeError(msg)


def fetch_latest_spec(dest: Path) -> Path:
    """Download the latest spec from Attio into ``dest`` and return it."""
    import httpx

    dest.parent.mkdir(parents=True, exist_ok=True)
    # httpx (a main dependency, also used by ci/pipeline.py's fetch) rather
    # than urllib: same code path everywhere and no audit noise about
    # dynamic urllib usage.
    with httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "attio-sdk-spec-check"},
    ) as client:
        response = client.get(SPEC_URL)
        response.raise_for_status()
        payload = response.content
    # Fail fast on non-JSON responses (HTML error pages, auth walls) and on
    # JSON that is not an OpenAPI document — both raise before anything
    # lands on disk, so a failed check never leaves a stale or misleading
    # file behind.
    _assert_openapi_document(json.loads(payload.decode("utf-8")))
    dest.write_bytes(payload)
    return dest


# ---------------------------------------------------------------------------
# Overlay parsing — via PyYAML (a dev dependency) rather than regexes, so
# any valid YAML formatting (flow lists, unquoted scalars, indentation
# changes) parses identically and cannot silently under-report actions.
# ---------------------------------------------------------------------------


def _load_overlay_actions(overlay_path: str | Path = OVERLAY_YAML) -> list[dict]:
    """Load the overlay document and return its ``actions`` list.

    Raises ``RuntimeError`` for an overlay with no actions, and lets
    ``yaml.YAMLError`` propagate for malformed YAML — both are treated as
    environmental errors (exit 2) by the ``check`` command, because there
    is no meaningful drift verdict without a readable overlay.
    """
    try:
        import yaml
    except ImportError as err:
        msg = (
            "PyYAML is required to read the overlay (it is a dev dependency, "
            "so run this through `uv run` or after `uv sync`)"
        )
        raise RuntimeError(msg) from err

    text = Path(overlay_path).read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError as err:
        msg = f"{overlay_path} is not valid YAML: {err}"
        raise RuntimeError(msg) from err
    actions = doc.get("actions") or []
    if not isinstance(actions, list) or not actions:
        msg = f"no overlay actions found in {overlay_path}"
        raise RuntimeError(msg)
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("target"), str):
            # RuntimeError (not TypeError) by design: every overlay-parse
            # failure is an environmental error for the check command.
            msg = (
                f"overlay action without a string target in {overlay_path}: {action!r}"
            )
            raise RuntimeError(msg)  # noqa: TRY004 - see comment above
    return actions


def load_overlay_targets(overlay_path: str | Path = OVERLAY_YAML) -> list[str]:
    """Extract the JSONPath targets from the overlay, in file order."""
    return [action["target"] for action in _load_overlay_actions(overlay_path)]


def load_overlay_enum_actions(
    overlay_path: str | Path = OVERLAY_YAML,
) -> dict[str, list[str]]:
    """Map overlay targets whose update sets a string enum to those values.

    Only actions whose ``update`` is a mapping containing an ``enum`` list
    are returned — the error-code flatten actions. Their enums REPLACE the
    spec's value set (the paired remove action deletes the anyOf union
    first), which is why the drift check must compare them against the
    union members: a hardcoded list that misses a newly added spec code
    would silently drop it and cause ResponseValidationError at runtime.
    """
    enum_actions: dict[str, list[str]] = {}
    for action in _load_overlay_actions(overlay_path):
        update = action.get("update")
        if not isinstance(update, dict):
            continue
        values = update.get("enum")
        if isinstance(values, list) and values:
            target = action["target"]
            # Merge rather than overwrite: two actions sharing a target
            # (e.g. a remove + a later update) must both be checked.
            merged = enum_actions.setdefault(target, [])
            merged.extend(str(v) for v in values)
    return enum_actions


# ---------------------------------------------------------------------------
# Mini JSONPath resolver for the overlay target subset
#
# Supported syntax:  $  .name  ['quoted key']  [123]  [?(@.field=='value')]
# Anything else raises UnsupportedSyntaxError.
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    \.(?P<dot>[A-Za-z_][A-Za-z0-9_-]*)          # .name
    | \[\s*(?P<idx>\d+)\s*\]                    # [123]
    | \[\s*'(?P<key>[^']+)'\s*\]                # ['quoted key']
    | \[\s*\?\(\s*@\.(?P<fld>[A-Za-z_][A-Za-z0-9_]*)
        \s*==\s*'(?P<fval>[^']*)'\s*\)\s*\]     # [?(@.name=='value')]
    """,
    re.X,
)


def _select_dict_key(nodes: list[Any], key: str) -> list[Any]:
    """Keep the ``key`` member of every dict node that has it."""
    return [node[key] for node in nodes if isinstance(node, dict) and key in node]


def _select_list_index(nodes: list[Any], idx: int) -> list[Any]:
    """Keep index ``idx`` of every list node long enough to have it."""
    return [
        node[idx]
        for node in nodes
        if isinstance(node, list) and -len(node) <= idx < len(node)
    ]


def _select_filtered(nodes: list[Any], field: str, value: str) -> list[Any]:
    """Keep list items (as list members) whose ``field`` equals ``value``."""
    picked: list[Any] = []
    for node in nodes:
        if not isinstance(node, list):
            continue
        for item in node:
            if isinstance(item, dict) and item.get(field) == value:
                picked.append(item)
    return picked


def resolve_jsonpath(doc: Any, target: str) -> list[Any]:  # noqa: ANN401 - arbitrary JSON
    """Resolve ``target`` against ``doc``; return every matched node.

    Raises ``UnsupportedSyntaxError`` for syntax outside the supported
    subset so that novel overlay constructs are flagged rather than
    silently treated as matching nothing.
    """
    if not target.startswith("$"):
        msg = f"target does not start with '$': {target}"
        raise UnsupportedSyntaxError(msg)
    rest = target[1:]
    nodes: list[Any] = [doc]
    pos = 0
    while pos < len(rest):
        match = _TOKEN_RE.match(rest, pos)
        if match is None:
            msg = f"unsupported JSONPath syntax at {rest[pos:]!r} in {target}"
            raise UnsupportedSyntaxError(msg)
        pos = match.end()
        if match.group("dot") is not None:
            nodes = _select_dict_key(nodes, match.group("dot"))
        elif match.group("idx") is not None:
            nodes = _select_list_index(nodes, int(match.group("idx")))
        elif match.group("key") is not None:
            nodes = _select_dict_key(nodes, match.group("key"))
        else:  # filter expression over a list
            nodes = _select_filtered(nodes, match.group("fld"), match.group("fval"))
        if not nodes:
            return []
    return nodes


# ---------------------------------------------------------------------------
# Trail normalization (must render identically for spec walks and overlay
# target bases so coverage comparisons are exact string matches)
# ---------------------------------------------------------------------------

# Standard JSONPath dot notation does not allow hyphens unquoted, and
# overlay.yaml brackets hyphenated keys ('input-value', 'output-value'), so
# trail normalization must do the same or coverage comparisons mismatch.
# Keys containing a single quote cannot be expressed by the overlay target
# syntax at all (the resolver rejects them), so any timestamp value under
# such a key is unrepresentable-and-uncovered: it flags as uncovered, which
# is loud rather than silently mismatched. No current spec key hits this.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def trail_key(key: str) -> str:
    if _IDENT_RE.match(key):
        return f".{key}"
    return f"['{key}']"


def make_trail(parent: str, key: str) -> str:
    return f"{parent}{trail_key(key)}"


def make_index_trail(parent: str, idx: int) -> str:
    return f"{parent}[{idx}]"


def overlay_target_base(target: str) -> str:
    """Strip the trailing leaf the overlay patches (format/example/...).

    Timestamp fix targets point at ``...value.format`` / ``.value.example`` /
    ``.value.description``; the base ``...value`` is what must line up with
    the trail of a ``format: date`` node found in the spec.
    """
    return re.sub(r"\.(format|example|description|enum)$", "", target)


# ---------------------------------------------------------------------------
# Structural diff between two specs
# ---------------------------------------------------------------------------


def _short(value: Any) -> str:  # noqa: ANN401 - arbitrary JSON
    text = json.dumps(value, sort_keys=True, default=str)
    if len(text) > _NOTE_MAX:
        text = text[: _NOTE_MAX - 3] + "..."
    return text


def _diff_mapping(
    a: dict[str, Any],
    b: dict[str, Any],
    trail: str,
    notes: list[str],
    limit: int,
) -> None:
    """Diff two mappings key by key."""
    for key in sorted(set(a) | set(b)):
        if key not in a:
            notes.append(f"{make_trail(trail, key)} added")
        elif key not in b:
            notes.append(f"{make_trail(trail, key)} removed")
        else:
            deep_diff_notes(a[key], b[key], make_trail(trail, key), notes, limit)


def _diff_sequence(
    a: list[Any],
    b: list[Any],
    trail: str,
    notes: list[str],
    limit: int,
) -> None:
    """Diff two sequences index by index."""
    if len(a) != len(b):
        notes.append(f"{trail}: {len(a)} items -> {len(b)} items")
    for i, (x, y) in enumerate(zip(a, b, strict=False)):
        deep_diff_notes(x, y, make_index_trail(trail, i), notes, limit)


def deep_diff_notes(
    a: Any,  # noqa: ANN401 - arbitrary JSON
    b: Any,  # noqa: ANN401 - arbitrary JSON
    trail: str,
    notes: list[str],
    limit: int = 8,
) -> None:
    """Append short human-readable notes describing how ``a`` became ``b``."""
    if a == b or len(notes) >= limit:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        _diff_mapping(a, b, trail, notes, limit)
    elif isinstance(a, list) and isinstance(b, list):
        _diff_sequence(a, b, trail, notes, limit)
    else:
        notes.append(f"{trail}: {_short(a)} -> {_short(b)}")


# Every OpenAPI Operations Object method (not just the common five): a new
# `options` or `head` operation is drift just like a new `get`.
_HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

# Documentation-only keys in every OpenAPI construct. Stripped recursively
# before structural comparisons so pure doc edits (marketing copy tweaks,
# docstring rewording) never count as structural drift, at any depth.
_DOC_KEYS = ("description", "summary")


def strip_doc_keys(node: Any, *, under_properties: bool = False) -> Any:  # noqa: ANN401 - arbitrary JSON
    """Return a deep copy of ``node`` without documentation-only keys.

    ``description`` and ``summary`` are documentation in every OpenAPI
    construct, so stripping them lets pure doc edits (marketing copy
    tweaks, docstring rewording) classify as non-structural at any depth.
    Two guards keep real API changes visible: a doc key is stripped only
    when its value is a plain string (a schema property named
    ``description`` holds a schema object, not prose), and keys inside a
    ``properties`` mapping are never stripped — they are user-defined
    field names, not documentation.
    """
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            is_doc_key = (
                key in _DOC_KEYS and isinstance(value, str) and not under_properties
            )
            if is_doc_key:
                continue
            out[key] = strip_doc_keys(value, under_properties=key == "properties")
        return out
    if isinstance(node, list):
        return [strip_doc_keys(item) for item in node]
    return node


def _classify_operation_change(
    result: dict[str, Any],
    label: str,
    old_op: dict[str, Any],
    new_op: dict[str, Any],
) -> None:
    """File one changed operation as description-only or structural."""
    structural_old = strip_doc_keys(old_op)
    structural_new = strip_doc_keys(new_op)
    if structural_old == structural_new:
        result["description_only_changes"].append(label)
        return
    notes: list[str] = []
    deep_diff_notes(structural_old, structural_new, label, notes)
    result["operations_changed"][label] = notes


def _diff_operations(
    result: dict[str, Any],
    old_ops: dict[str, Any],
    new_ops: dict[str, Any],
    path: str,
) -> None:
    """Compare the operations of one path that exists in both specs."""
    for method in _HTTP_METHODS:
        label = f"{method.upper()} {path}"
        in_old, in_new = method in old_ops, method in new_ops
        if in_old and not in_new:
            result["operations_removed"].append(label)
        elif in_new and not in_old:
            result["operations_added"].append(label)
        elif in_old and in_new and old_ops[method] != new_ops[method]:
            _classify_operation_change(result, label, old_ops[method], new_ops[method])


def _diff_path_item(
    result: dict[str, Any],
    old_item: dict[str, Any],
    new_item: dict[str, Any],
    path: str,
) -> None:
    """Compare path-item-level keys (shared parameters, servers, ...).

    Operations are handled by :func:`_diff_operations`; this covers the
    remaining keys, which apply to every operation on the path and are easy
    to miss because they sit outside the method bodies.
    """
    structural_old = strip_doc_keys(
        {k: v for k, v in old_item.items() if k not in _HTTP_METHODS},
    )
    structural_new = strip_doc_keys(
        {k: v for k, v in new_item.items() if k not in _HTTP_METHODS},
    )
    if structural_old == structural_new:
        return
    notes: list[str] = []
    deep_diff_notes(structural_old, structural_new, f"{path} (path item)", notes)
    result["path_items_changed"][path] = notes


def _diff_components(
    result: dict[str, Any],
    old: dict[str, Any],
    new: dict[str, Any],
) -> None:
    """Compare every ``components`` section, not just ``schemas``.

    ``$ref`` targets like ``components.parameters`` and
    ``components.requestBodies`` do not appear inside the operation dicts,
    so a change there would otherwise be invisible to the operation diff.
    """
    old_components = old.get("components", {}) or {}
    new_components = new.get("components", {}) or {}
    for section in sorted(set(old_components) | set(new_components)):
        old_sec = old_components.get(section) or {}
        new_sec = new_components.get(section) or {}
        if not isinstance(old_sec, dict) or not isinstance(new_sec, dict):
            continue
        for name in sorted(set(old_sec) | set(new_sec)):
            label = f"{section}/{name}"
            if name not in old_sec:
                result["components_added"].append(label)
            elif name not in new_sec:
                result["components_removed"].append(label)
            elif old_sec[name] != new_sec[name]:
                if strip_doc_keys(old_sec[name]) == strip_doc_keys(new_sec[name]):
                    result["description_only_changes"].append(f"component {label}")
                    continue
                notes: list[str] = []
                deep_diff_notes(
                    strip_doc_keys(old_sec[name]),
                    strip_doc_keys(new_sec[name]),
                    f"component {label}",
                    notes,
                )
                result["components_changed"][label] = notes


def _collect_path_operations(
    result: dict[str, Any],
    item: dict[str, Any],
    path: str,
    *,
    added: bool,
) -> None:
    """Record every operation of an entirely new/removed path.

    Without this, a brand-new endpoint only shows up in ``paths_added`` and
    the per-method lists (which the workflow summaries and PR body render)
    stay silent about it.
    """
    key = "operations_added" if added else "operations_removed"
    for method in _HTTP_METHODS:
        if method in item:
            result[key].append(f"{method.upper()} {path}")


def _diff_top_level(
    result: dict[str, Any],
    old: dict[str, Any],
    new: dict[str, Any],
) -> None:
    """Compare top-level keys other than ``paths`` and ``components``.

    ``servers``, ``security``, ``webhooks``, ``tags``, ``info`` and ``x-*``
    extensions all shape the generated SDK or its behavior; a change there
    (a new server URL, a new global security requirement, a new webhook)
    is structural drift and must not hide behind the path-level diff.
    """
    for key in sorted(set(old) | set(new)):
        if key in ("paths", "components"):
            continue
        old_val, new_val = old.get(key), new.get(key)
        if old_val == new_val:
            continue
        if strip_doc_keys(old_val) == strip_doc_keys(new_val):
            result["description_only_changes"].append(f"top-level {key}")
            continue
        notes: list[str] = []
        deep_diff_notes(
            strip_doc_keys(old_val),
            strip_doc_keys(new_val),
            f"{key} (top level)",
            notes,
        )
        result["top_level_changed"][key] = notes


def structural_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Compare two OpenAPI specs and classify the differences.

    Description/summary edits are stripped recursively and separated from
    structural edits so that doc-only churn (marketing copy tweaks) does not
    trigger a regeneration while real API changes — including changes hidden
    behind ``$ref`` in any ``components`` section or in path-item-level
    parameters — always do.
    """
    result: dict[str, Any] = {
        "paths_added": [],
        "paths_removed": [],
        "operations_added": [],
        "operations_removed": [],
        "operations_changed": {},
        "path_items_changed": {},
        "description_only_changes": [],
        "components_added": [],
        "components_removed": [],
        "components_changed": {},
        "top_level_changed": {},
    }

    old_paths, new_paths = old.get("paths", {}), new.get("paths", {})
    for path in sorted(set(old_paths) | set(new_paths)):
        if path not in old_paths:
            result["paths_added"].append(path)
            _collect_path_operations(result, new_paths[path], path, added=True)
        elif path not in new_paths:
            result["paths_removed"].append(path)
            _collect_path_operations(result, old_paths[path], path, added=False)
        else:
            _diff_operations(result, old_paths[path], new_paths[path], path)
            _diff_path_item(result, old_paths[path], new_paths[path], path)

    _diff_components(result, old, new)
    _diff_top_level(result, old, new)

    result["has_structural_changes"] = bool(
        result["paths_added"]
        or result["paths_removed"]
        or result["operations_added"]
        or result["operations_removed"]
        or result["operations_changed"]
        or result["path_items_changed"]
        or result["components_added"]
        or result["components_removed"]
        or result["components_changed"]
        or result["top_level_changed"],
    )
    return result


# ---------------------------------------------------------------------------
# Overlay verification
# ---------------------------------------------------------------------------


class TimestampTrailFinder:
    """Walk a spec and collect trails of Attio timestamp value nodes.

    Attio declares timestamp attribute values as ISO 8601 strings that
    Speakeasy mis-infers as ``datetime.date`` because of ``format: date``;
    those are exactly the nodes overlay.yaml exists to fix. Genuine
    date-only fields are left alone.

    A node counts as a timestamp value when its description names the ISO
    8601 format (the strongest signal, regardless of the property name) or
    when it sits under a ``value`` property and its example carries a time
    component (``2023-01-02T13:00:00Z``).
    """

    _EXAMPLE_TIMESTAMP_HINT_LEN = 32
    # An ISO 8601 time component (e.g. `02T13` in `2023-01-02T13:00:00Z`) —
    # a bare capital `T` (as in "Test") is not a timestamp signal.
    _EXAMPLE_TIME_RE = re.compile(r"\d{2}T\d{2}")

    def __init__(self) -> None:
        """Start with no collected trails."""
        self.trails: list[str] = []

    def _is_timestamp_value(self, node: dict[str, Any], trail: str) -> bool:
        if node.get("format") != "date" or node.get("type") != "string":
            return False
        description = node.get("description", "")
        # Deliberately narrow: "ISO 8601" (the exact signal Attio uses) or a
        # time-bearing example under a `.value` trail. A broader keyword like
        # the bare word "timestamp" would flag genuine date-only fields as
        # uncovered, and nothing can allowlist those — the weekly workflow
        # would then block regeneration permanently. Description rewording
        # is caught loudly instead by the pinned timestamp-trail-count test.
        if "ISO 8601" in description:
            return True
        if trail.endswith(".value"):
            example = str(node.get("example", ""))
            hint = example[: self._EXAMPLE_TIMESTAMP_HINT_LEN]
            return bool(self._EXAMPLE_TIME_RE.search(hint))
        return False

    def walk(self, node: Any, trail: str) -> None:  # noqa: ANN401 - arbitrary JSON
        if isinstance(node, dict):
            if self._is_timestamp_value(node, trail):
                self.trails.append(trail)
            for key, value in node.items():
                self.walk(value, make_trail(trail, key))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                self.walk(item, make_index_trail(trail, i))


def find_timestamp_value_trails(doc: dict[str, Any]) -> list[str]:
    """Find every Attio timestamp value node (``format: date`` ISO 8601 string)."""
    finder = TimestampTrailFinder()
    finder.walk(doc.get("paths", {}), "$.paths")
    finder.walk(doc.get("components", {}), "$.components")
    return finder.trails


def _union_error_codes(node: Any) -> list[str] | None:  # noqa: ANN401 - arbitrary JSON
    """Error-code values a spec node accepts, when the node is a union.

    Only ``anyOf``/``oneOf``-of-enums nodes return values: an overlay
    ``update`` on such a node REPLACES the value set (the paired ``remove``
    deletes the union first), so the overlay enum must include every spec
    value or the generated Literal silently drops codes. Nodes with a plain
    ``enum`` are merge-appends that cannot drop values, and anything else is
    not an error-code node; both return ``None`` (no check). Variants that
    carry their values via ``$ref`` or nesting are not resolved — the spec
    expresses error codes inline, and a restructure away from that surfaces
    through the dead-target check on the paired remove action.
    """
    if not isinstance(node, dict):
        return None
    variants = node.get("anyOf") if "anyOf" in node else node.get("oneOf")
    if variants is None:
        return None
    values: list[str] = []
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        if isinstance(variant.get("enum"), list):
            values.extend(str(v) for v in variant["enum"])
        elif "const" in variant:
            # A single-value variant can be written as `const` instead of a
            # one-element `enum`; it contributes the same value.
            values.append(str(variant["const"]))
    return values or None


class OverlayHealth(TypedDict):
    """Result of :func:`verify_overlay` — lists of problems plus a rollup."""

    dead_targets: list[str]
    uncovered_timestamp_values: list[str]
    misdirected_targets: list[str]
    dropped_error_codes: list[str]
    healthy: bool


def _resolve_targets(
    spec: dict[str, Any],
    targets: list[str],
) -> tuple[list[str], list[str], set[str]]:
    """Resolve every overlay target against ``spec``.

    Returns ``(dead_targets, misdirected_targets, covered_bases)``: dead
    targets match nothing (speakeasy silently skips them), misdirected
    targets are live timestamp-fix actions that no longer land on a
    timestamp value (collateral damage from index drift), and covered
    bases are the trails protected by a live ``.format`` removal.
    """
    dead: list[str] = []
    misdirected: list[str] = []
    covered: set[str] = set()
    timestamp_trails = set(find_timestamp_value_trails(spec))
    for target in targets:
        try:
            matches = resolve_jsonpath(spec, target)
        except UnsupportedSyntaxError as err:
            dead.append(f"{target} ({err})")
            continue
        if not matches:
            if target.endswith(".anyOf") and ".code." in target:
                # Attio reverting an error-code field to a flat enum kills
                # the remove half of a flatten pair; name the remedy instead
                # of leaving a bare "dead target" to interpret.
                dead.append(
                    f"{target} (dead: the spec no longer uses an error-code "
                    "union here — drop the flatten remove/update pair from "
                    "overlay.yaml)",
                )
            else:
                dead.append(target)
            continue  # dead targets never count as coverage
        if not target.endswith((".format", ".example", ".description")):
            continue
        base = overlay_target_base(target)
        if target.endswith(".format"):
            covered.add(base)
            # Only the type-driving `.format` removals are checked for
            # misdirection: an upstream reorder can keep the old index
            # alive but pointing at a different member, silently stripping
            # `format: date` from a genuine date-only field. Example and
            # description updates are cosmetic and may legitimately target
            # non-timestamp nodes, so flagging those would be noise.
            if base not in timestamp_trails:
                misdirected.append(target)
    return dead, misdirected, covered


def _check_error_code_sync(
    spec: dict[str, Any],
    enum_actions: dict[str, list[str]] | None,
) -> list[str]:
    """Report overlay enums that drop values the spec's unions still carry.

    Deliberately one-way: overlay enums may carry intentional extras the
    spec does not list (``validation_type`` is exactly that), so values
    present only in the overlay are not reported. The reverse — a spec
    value missing from the overlay — is the case that drops codes from the
    generated Literal.
    """
    dropped: list[str] = []
    for target, overlay_values in (enum_actions or {}).items():
        try:
            nodes = resolve_jsonpath(spec, target)
        except UnsupportedSyntaxError as err:
            dropped.append(f"{target} (unparsed action: {err})")
            continue
        for node in nodes:
            spec_values = _union_error_codes(node)
            if spec_values is None:
                continue
            missing = [v for v in spec_values if v not in overlay_values]
            if missing:
                dropped.append(
                    f"{target} drops spec error code(s) {', '.join(missing)}"
                    " - add them to the overlay enum",
                )
    return dropped


def verify_overlay(
    spec: dict[str, Any],
    targets: list[str],
    enum_actions: dict[str, list[str]] | None = None,
) -> OverlayHealth:
    """Check overlay health against ``spec``.

    Four failure modes are detected:

    * ``dead_targets`` — overlay actions whose JSONPath matches nothing.
      Speakeasy skips these silently, so a dead target means a fix this
      repo believes it is applying is actually not being applied.
    * ``uncovered_timestamp_values`` — timestamp value nodes in the spec
      with no *resolvable* ``.format`` removal action targeting them, i.e.
      values that will regenerate as ``date`` instead of ``str``. Only a
      live ``.format`` removal counts as coverage: a dead or doc-only
      action proves nothing about the generated type.
    * ``misdirected_targets`` — live timestamp-fix actions whose target
      now resolves onto a node that is NOT a timestamp value. An upstream
      union reorder can keep the old index alive but pointing at a
      different member, silently stripping ``format: date`` from a
      genuine date-only field; this reports that collateral damage
      directly instead of leaving it as a confusing "uncovered" note.
    * ``dropped_error_codes`` — overlay actions that replace an anyOf
      error-code union with a hardcoded enum missing one or more of the
      union's values, which would make the generated Literal reject codes
      the API actually returns.
    """
    dead_targets, misdirected, covered_bases = _resolve_targets(spec, targets)

    uncovered = [
        trail
        for trail in find_timestamp_value_trails(spec)
        if trail not in covered_bases
    ]

    dropped = _check_error_code_sync(spec, enum_actions)

    return OverlayHealth(
        dead_targets=dead_targets,
        uncovered_timestamp_values=uncovered,
        misdirected_targets=misdirected,
        dropped_error_codes=dropped,
        healthy=not dead_targets and not uncovered and not misdirected and not dropped,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_MAX_NOTES_SHOWN = 4


def _render_noted(
    lines: list[str],
    header: str,
    noted: dict[str, list[str]],
) -> None:
    """Render ``header`` followed by one ``- label`` line per entry, with up
    to ``_MAX_NOTES_SHOWN`` indented notes and an overflow marker.
    """
    if not noted:
        return
    lines.append(header)
    for label, notes in noted.items():
        lines.append(f"  - {label}")
        lines += [f"      {note}" for note in notes[:_MAX_NOTES_SHOWN]]
        if len(notes) > _MAX_NOTES_SHOWN:
            lines.append(f"      ... and {len(notes) - _MAX_NOTES_SHOWN} more")


def _render_listed(lines: list[str], title: str, items: list[str]) -> None:
    """Render ``title`` followed by one ``- item`` line per item."""
    if not items:
        return
    lines.append(f"{title}:")
    lines += [f"  - {item}" for item in items]


def render_report(diff: dict[str, Any], overlay: OverlayHealth) -> list[str]:
    """Render a human-readable summary of a diff + overlay verification."""
    lines: list[str] = []
    if diff["has_structural_changes"]:
        lines.append("STRUCTURAL DRIFT DETECTED — regeneration recommended")
    else:
        lines.append("No structural changes (descriptions only or identical).")

    _render_listed(lines, "New endpoints", diff["paths_added"])
    _render_listed(lines, "Removed endpoints", diff["paths_removed"])
    _render_listed(lines, "New operations", diff["operations_added"])
    _render_listed(lines, "Removed operations", diff["operations_removed"])
    _render_noted(lines, "Changed operations:", diff["operations_changed"])
    _render_noted(lines, "Changed path items:", diff["path_items_changed"])

    for title, key in (
        ("New component definitions", "components_added"),
        ("Removed component definitions", "components_removed"),
    ):
        if diff[key]:
            lines.append(f"{title}: {', '.join(diff[key])}")

    if diff["components_changed"]:
        lines.append("Changed component definitions:")
        for label, notes in diff["components_changed"].items():
            lines.append(f"  - {label}: {notes[0] if notes else 'changed'}")

    _render_noted(lines, "Changed top-level keys:", diff["top_level_changed"])

    if diff["description_only_changes"]:
        lines.append(
            f"Description-only changes (no regeneration needed): "
            f"{len(diff['description_only_changes'])} item(s)",
        )

    _render_overlay_verdict(lines, overlay)

    return lines


def _render_overlay_verdict(lines: list[str], overlay: OverlayHealth) -> None:
    """Render the overlay section of a report."""
    if overlay["healthy"]:
        lines.append(
            "Overlay OK: all targets resolve, all timestamp values covered, "
            "all fix actions land on timestamp values, all error-code enums "
            "in sync.",
        )
        return
    lines.append("OVERLAY PROBLEMS — fix overlay.yaml before regenerating:")
    for target in overlay["dead_targets"]:
        lines.append(f"  - dead target (matches nothing): {target}")
    for trail in overlay["uncovered_timestamp_values"]:
        lines.append(
            f"  - timestamp value not covered by a live .format removal: {trail}",
        )
    for target in overlay["misdirected_targets"]:
        lines.append(
            f"  - fix action no longer lands on a timestamp value: {target}",
        )
    for note in overlay["dropped_error_codes"]:
        lines.append(f"  - error-code enum out of sync with spec: {note}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_diff(args: argparse.Namespace) -> int:
    old, new = load_spec(args.old), load_spec(args.new)
    diff = structural_diff(old, new)
    if args.json:
        print(json.dumps(diff, indent=2))
    else:
        overlay_ok = OverlayHealth(
            dead_targets=[],
            uncovered_timestamp_values=[],
            misdirected_targets=[],
            dropped_error_codes=[],
            healthy=True,
        )
        print("\n".join(render_report(diff, overlay_ok)) or "identical")
    return 0


def cmd_check_overlay(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec) if args.spec else current_spec_path()
    overlay_path = Path(args.overlay) if args.overlay else OVERLAY_YAML
    spec = load_spec(spec_path)
    targets = load_overlay_targets(overlay_path)
    enum_actions = load_overlay_enum_actions(overlay_path)
    problems = verify_overlay(spec, targets, enum_actions)
    if problems["healthy"]:
        print(f"Overlay OK against {spec_path} ({len(targets)} targets)")
        return 0
    print(f"Overlay problems against {spec_path}:")
    for target in problems["dead_targets"]:
        print(f"  dead target: {target}")
    for trail in problems["uncovered_timestamp_values"]:
        print(f"  uncovered timestamp value: {trail}")
    for target in problems["misdirected_targets"]:
        print(f"  fix action no longer lands on a timestamp value: {target}")
    for note in problems["dropped_error_codes"]:
        print(f"  error-code enum out of sync: {note}")
    return 1


def cmd_check(args: argparse.Namespace) -> int:
    import httpx

    current: Path | None = None
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    fetched = TMP_DIR / f"spec-check-{timestamp}.json"
    print(f"Fetching latest spec from {SPEC_URL} ...", file=sys.stderr)
    try:
        # current_spec_path() is environmental too (a workflow.yaml without
        # a spec reference), so it lives inside the try.
        current = current_spec_path()
        fetch_latest_spec(fetched)
        latest = load_spec(fetched)
        baseline = load_spec(current)
        # Overlay parse failures (malformed overlay.yaml) are environmental:
        # there is no meaningful drift verdict to report, so they exit 2 with
        # the fetch/load errors rather than masquerading as a healthy check.
        overlay_targets = load_overlay_targets()
        overlay_enums = load_overlay_enum_actions()
    except (
        httpx.HTTPError,
        OSError,
        RuntimeError,
        ValueError,
    ) as err:
        # Deliberately narrow: environmental failures (network, disk, bad
        # JSON or undecodable bytes, unreadable overlay/workflow files) exit
        # 2 cleanly — ValueError covers UnicodeDecodeError alongside
        # JSONDecodeError — while programming errors keep their traceback
        # instead of masquerading as an Attio outage in the attention issue.
        print(
            f"error: could not fetch or load specs, or parse the overlay: {err}",
            file=sys.stderr,
        )
        return 2
    finally:
        fetched.unlink(missing_ok=True)

    if current is None:
        # Unreachable when the try block succeeded; kept so a future refactor
        # fails loudly instead of crashing on Optional member access.
        msg = "unreachable: current spec path must be resolved by now"
        raise RuntimeError(msg)
    diff = structural_diff(baseline, latest)
    overlay = verify_overlay(latest, overlay_targets, overlay_enums)
    timestamp_trail_count = len(find_timestamp_value_trails(latest))
    baseline_trail_count = len(find_timestamp_value_trails(baseline))
    if timestamp_trail_count < baseline_trail_count:
        # Fewer detected timestamp surfaces than the baseline usually means
        # Attio reworded a description so the detector no longer recognizes
        # a node — those values would regenerate as `date`. Block (the note
        # lands in the uncovered bucket) until a human confirms whether the
        # drop is a legitimate surface removal or a detection regression.
        overlay["healthy"] = False
        overlay["uncovered_timestamp_values"].append(
            f"(detection regression) the fetched spec exposes "
            f"{timestamp_trail_count} timestamp surfaces, the baseline has "
            f"{baseline_trail_count} — if this is a legitimate removal, "
            "update the pinned count test and the overlay; otherwise the "
            "detector lost a node to a description rewording",
        )

    report = {
        "current_spec": str(current.relative_to(REPO_ROOT)),
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
        "spec_url": SPEC_URL,
        "structural_changes": diff["has_structural_changes"],
        # Informational: the fetched spec's timestamp-surface count. The
        # committed-spec count is pinned by a test; a drop here (Attio
        # rewording a description so detection misses a node) is visible to
        # a human reading the report even when nothing else changed.
        "timestamp_trail_count": timestamp_trail_count,
        "diff": diff,
        "overlay": overlay,
    }
    lines = [
        f"Current spec: {report['current_spec']}",
        f"Timestamp value surfaces: {timestamp_trail_count}",
        *render_report(diff, overlay),
    ]

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        lines.append(f"(JSON report written to {report_path})")

    print("\n".join(lines))

    if not diff["has_structural_changes"] and overlay["healthy"]:
        return 0
    if args.no_strict:
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    description = (__doc__ or "Attio SDK OpenAPI spec drift detection").splitlines()[0]
    parser = argparse.ArgumentParser(description=description)
    sub = parser.add_subparsers(dest="command", required=True)

    diff_cmd = sub.add_parser("diff", help="Structural diff between two spec files")
    diff_cmd.add_argument("old")
    diff_cmd.add_argument("new")
    diff_cmd.add_argument("--json", action="store_true", help="Emit JSON")
    diff_cmd.set_defaults(func=cmd_diff)

    overlay_cmd = sub.add_parser(
        "check-overlay",
        help="Verify overlay targets resolve against a spec",
    )
    overlay_cmd.add_argument("spec", nargs="?", help="Spec file (default: current)")
    overlay_cmd.add_argument(
        "overlay",
        nargs="?",
        help="Overlay file (default: overlay.yaml)",
    )
    overlay_cmd.set_defaults(func=cmd_check_overlay)

    check_cmd = sub.add_parser(
        "check",
        help="Fetch latest spec, diff vs current, verify overlay",
    )
    check_cmd.add_argument("--report", metavar="PATH", help="Write a JSON report")
    check_cmd.add_argument(
        "--no-strict",
        action="store_true",
        help="Exit 0 on drift or overlay problems (report only); "
        "environmental errors still fail with exit 2",
    )
    check_cmd.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
