"""SDK-side guard: every generated ``*BadRequestCode`` Literal must accept
each 400 ``code`` value the pinned spec lists for its endpoint, plus every
extra ``overlay.yaml`` advertises for it (``validation_type`` arrives via
both overlay shapes: appends on flat enums and anyOf flatten-replaces).

Complements ``test_overlay_error_code_coverage.py`` and ``check-overlay``
(overlay side): this catches overlay/generator regressions that only show up
in the generated models, e.g. a dropped ``validation_type`` overlay action
(the PR #81 shape) leaving a Literal that makes a real 400 response raise
``ResponseValidationError``.
"""

from __future__ import annotations

import ast
import functools
import importlib.util
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "generated" / "src" / "attio" / "models"
_SUFFIX = "BadRequestCode"
_PLAIN_SUFFIX = "Code"


def _load_spec_diff() -> Any:
    path = REPO_ROOT / "ci" / "spec_diff.py"
    spec = importlib.util.spec_from_file_location("attio_sdk_code_spec_diff", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _class_stem(method: str, path: str) -> str:
    """Speakeasy class prefix: ``post /v2/lists/{list}`` -> ``PostV2ListsList``."""
    parts = []
    for seg in path.strip("/").split("/"):
        seg = seg.strip("{}")
        parts.append(
            "".join(
                "ID" if tok == "id" else tok.capitalize()
                for tok in seg.split("_")
                if tok
            )
        )
    return method.title() + "".join(parts)


def _spec_codes(spec_diff: Any, node: Any) -> set[str]:
    """Flattened 400 ``code`` values for a response-400 schema node."""
    if not isinstance(node, dict):
        return set()
    union = spec_diff._union_error_codes(node)
    if union is not None:
        return set(union)
    if isinstance(node.get("enum"), list):
        return {str(v) for v in node["enum"]}
    return set()


@functools.cache
def _spec_codes_by_stem() -> dict[str, set[str]]:
    spec_diff = _load_spec_diff()
    spec = spec_diff.load_spec(spec_diff.current_spec_path())
    out: dict[str, set[str]] = {}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if not isinstance(op, dict):
                continue
            schema = (
                op.get("responses", {})
                .get("400", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            variants = schema.get("anyOf") or schema.get("oneOf") or [schema]
            codes: set[str] = set()
            for variant in variants:
                code = (variant.get("properties") or {}).get("code")
                codes |= _spec_codes(spec_diff, code)
            out[_class_stem(method, path)] = codes
    return out


_OVERLAY_400_CODE_TARGET_RE = re.compile(
    r"\$(?:\.paths)?(?:\[)?'?(?P<path>/v2/[^']+)'?\]?\."
    r"(?P<method>post|put|patch|delete|get)"
    r"\.responses\['400'\]"
    r"\.content\['application/json'\]\.schema\.properties\.code(?:\.enum)?$"
)


@functools.cache
def _overlay_codes_by_stem() -> dict[str, set[str]]:
    """400 ``code`` values ``overlay.yaml`` advertises, keyed by class stem.

    Both action shapes count: an ``update: [values]`` list appends to a flat
    ``.code.enum``, and an ``update: {enum: [...]}`` mapping replaces an
    anyOf union's values outright (its paired ``remove`` deletes the union
    first). The replace shape carries the full enum, so unioning these
    values with the spec's is correct for both shapes.
    """
    with (REPO_ROOT / "overlay.yaml").open() as fh:
        doc = yaml.safe_load(fh) or {}
    out: dict[str, set[str]] = {}
    for action in doc.get("actions") or []:
        match = _OVERLAY_400_CODE_TARGET_RE.search(action.get("target") or "")
        if not match:
            continue
        update = action.get("update")
        if isinstance(update, list):
            codes = {v for v in update if isinstance(v, str)}
        elif isinstance(update, dict) and isinstance(update.get("enum"), list):
            codes = {str(v) for v in update["enum"]}
        else:
            continue
        if codes:
            stem = _class_stem(match.group("method"), match.group("path"))
            out[stem] = out.get(stem, set()) | codes
    return out


def _stem(name: str) -> str:
    base = name.removesuffix(_SUFFIX)
    return base if base != name else name.removesuffix(_PLAIN_SUFFIX)


def _literals() -> dict[str, tuple[str, set[str]]]:
    """``{class name: (file name, literal values)}`` for every 400-code Literal.

    Speakeasy names some of them ``*Code`` instead of ``*BadRequestCode``; a
    plain ``*Code`` Literal only counts when the overlay advertises 400 codes
    for its endpoint (other ``*Code`` Literals sit on endpoints with no
    overlay-advertised 400 codes, e.g. the spec-native ``PostV2MeetingsCode``).
    """
    overlay_stems = _overlay_codes_by_stem()
    found: dict[str, tuple[str, set[str]]] = {}
    for file in sorted(MODELS_DIR.glob("*.py")):
        for node in ast.parse(file.read_text(encoding="utf-8")).body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and (
                    node.targets[0].id.endswith(_SUFFIX)
                    or (
                        node.targets[0].id.endswith(_PLAIN_SUFFIX)
                        and _stem(node.targets[0].id) in overlay_stems
                    )
                )
                and isinstance(node.value, ast.Subscript)
            ):
                values = {
                    n.value
                    for n in ast.walk(node.value.slice)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                }
                found[node.targets[0].id] = (file.name, values)
    return found


LITERALS = _literals()

EXPECTED_LITERALS = frozenset(
    {
        "PatchV2ListsListBadRequestCode",
        "PatchV2TargetIdentifierAttributesAttributeOptionsOptionBadRequestCode",
        "PatchV2TargetIdentifierAttributesAttributeStatusesStatusBadRequestCode",
        "PostV2ActivitiesActivityRecordsBadRequestCode",
        "PostV2ListsBadRequestCode",
        "PostV2CommentsCode",
        "PostV2ListsListEntriesBadRequestCode",
        "PostV2ObjectsObjectRecordsBadRequestCode",
        "PostV2ObjectsRecordsSearchCode",
        "PutV2ActivitiesActivityRecordsBadRequestCode",
        "PutV2ListsListEntriesEntryIDAttributesAttributeValuesBadRequestCode",
        "PutV2ObjectsObjectRecordsBadRequestCode",
        "PutV2ObjectsObjectRecordsRecordIDAttributesAttributeValuesBadRequestCode",
    }
)


def test_bad_request_code_literals_match_expected() -> None:
    """Fence the alias set so a removed/renamed Literal can't silently drop
    its parametrized case; update EXPECTED_LITERALS when one is added."""
    found = set(LITERALS)
    assert found == EXPECTED_LITERALS, (
        f"missing: {sorted(EXPECTED_LITERALS - found)}; "
        f"unexpected: {sorted(found - EXPECTED_LITERALS)}"
    )


def test_every_overlay_endpoint_has_a_discovered_literal() -> None:
    discovered = {_stem(name) for name in LITERALS}
    missing = sorted(set(_overlay_codes_by_stem()) - discovered)
    assert not missing, (
        f"overlay.yaml advertises 400 codes for {missing} but no generated "
        "*BadRequestCode/*Code Literal was found for them; the SDK side is "
        "unguarded - update _literals or _class_stem."
    )


@pytest.mark.parametrize("name", sorted(LITERALS))
def test_literal_covers_spec_codes(name: str) -> None:
    file_name, sdk_codes = LITERALS[name]
    stem = _stem(name)
    spec_codes = _spec_codes_by_stem().get(stem)
    assert spec_codes is not None, (
        f"{name} ({file_name}) matches no spec operation; Speakeasy naming "
        "changed or the endpoint was removed - update _class_stem."
    )
    expected = spec_codes | _overlay_codes_by_stem().get(stem, set())
    dropped = sorted(expected - sdk_codes)
    assert not dropped, (
        f"{name} ({file_name}) drops code(s) {', '.join(dropped)} that the "
        "pinned spec or overlay.yaml advertises for this endpoint; SDK has "
        f"{sorted(sdk_codes)}. A real 400 response with that code would "
        "raise ResponseValidationError."
    )
