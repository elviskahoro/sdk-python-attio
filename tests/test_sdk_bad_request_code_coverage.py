"""SDK-side guard: every generated ``*BadRequestCode`` Literal must accept
each 400 ``code`` value the pinned spec lists for its endpoint.

Complements ``test_overlay_error_code_coverage.py`` and ``check-overlay``
(overlay side): this catches overlay/generator regressions that only show up
in the generated models, e.g. a dropped ``validation_type`` that would make a
real 400 response raise ``ResponseValidationError``.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "generated" / "src" / "attio" / "models"
_SUFFIX = "BadRequestCode"


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


def _literals() -> dict[str, tuple[str, set[str]]]:
    """``{class name: (file name, literal values)}`` for every BadRequestCode."""
    found: dict[str, tuple[str, set[str]]] = {}
    for file in sorted(MODELS_DIR.glob("*.py")):
        for node in ast.parse(file.read_text(encoding="utf-8")).body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id.endswith(_SUFFIX)
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


def test_bad_request_code_literals_discovered() -> None:
    assert LITERALS, f"no *{_SUFFIX} Literals found under {MODELS_DIR}"


@pytest.mark.parametrize("name", sorted(LITERALS))
def test_literal_covers_spec_codes(name: str) -> None:
    file_name, sdk_codes = LITERALS[name]
    stem = name.removesuffix(_SUFFIX)
    spec_codes = _spec_codes_by_stem().get(stem)
    assert spec_codes is not None, (
        f"{name} ({file_name}) matches no spec operation; Speakeasy naming "
        "changed or the endpoint was removed - update _class_stem."
    )
    dropped = sorted(spec_codes - sdk_codes)
    assert not dropped, (
        f"{name} ({file_name}) drops code(s) {', '.join(dropped)} that the "
        f"pinned spec lists for this endpoint; SDK has {sorted(sdk_codes)}. "
        "A real 400 response with that code would raise ResponseValidationError."
    )
