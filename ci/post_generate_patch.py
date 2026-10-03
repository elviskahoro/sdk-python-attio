#!/usr/bin/env python3
"""Re-apply manual patches to Speakeasy-generated SDK source.

``speakeasy run`` rewrites ``src/`` from the OpenAPI overlay, so any
hand-edit to a generated file is lost on the next regeneration. This script
idempotently re-injects the edits that ``overlay.yaml`` cannot express, and
the generation pipeline (``ci/pipeline.py``) runs it after every generation
so the tree the tests, build, and PR commit consume already carries them.

Run it standalone after a direct ``speakeasy run``::

    python ci/post_generate_patch.py

It is safe to run on an already-patched tree (a no-op then).

Patch: ``src/attio/models/get_v2_selfop.py``

    The GET /v2/self ``anyOf`` discriminates the active and inactive token
    variants with single-value boolean enums on ``active`` (``[true]`` and
    ``[false]``). ``overlay.yaml`` removes those enums because under
    ``constFieldCasing: upper`` Speakeasy would render the field as an
    ``ACTIVE``-aliased const and ``response.active`` would raise
    ``AttributeError`` for live tokens. Dropping the enum fixes the
    attribute name but discards the value check the spec defines, so the
    matching ``@model_validator(mode="after")`` checks on ``AttioCom``
    (``active`` must be ``True``) and ``ResponseBody`` (``active`` must be
    ``False``) are re-added here to restore the discriminating invariant.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "src" / "attio" / "models" / "get_v2_selfop.py"

ATTIO_COM_VALIDATOR_LINES = [
    '    @model_validator(mode="after")',
    "    def _validate_active(self):",
    "        if self.active is not True:",
    '            raise ValueError("active must be true for AttioCom")',
    "        return self",
]

RESPONSE_BODY_VALIDATOR_LINES = [
    '    @model_validator(mode="after")',
    "    def _validate_active(self):",
    "        if self.active is not False:",
    '            raise ValueError("active must be false for ResponseBody")',
    "        return self",
]


def _class_body_end(lines: list[str], class_start: int) -> int:
    """Return the index of the first top-level line after the class, or EOF."""
    for i in range(class_start + 1, len(lines)):
        line = lines[i]
        if line and not line[0].isspace() and not line.startswith("#"):
            return i
    return len(lines)


def _ensure_import(text: str) -> str:
    """Ensure ``model_validator`` is imported alongside ``model_serializer``."""
    line = next(
        (
            l
            for l in text.splitlines()
            if l.startswith("from pydantic import ") and "model_serializer" in l
        ),
        None,
    )
    if line is None:
        msg = (
            "the generated GET /v2/self model no longer has the expected "
            "`from pydantic import model_serializer` import line; the "
            "post-generation patch must be updated."
        )
        raise RuntimeError(msg)
    if "model_validator" in line:
        return text
    new_line = line.replace("model_serializer", "model_serializer, model_validator", 1)
    return text.replace(line, new_line, 1)


def _inject_into_class(text: str, class_name: str, method_lines: list[str]) -> str:
    """Inject ``method_lines`` into ``class_name`` unless it already has one.

    When the class has a ``@model_serializer`` decorator, the validator is
    inserted immediately before it so validators read before the serializer;
    otherwise it is appended at the end of the class body.
    """
    lines = text.splitlines(keepends=False)
    start = next(
        (i for i, l in enumerate(lines) if l.startswith(f"class {class_name}(")),
        None,
    )
    if start is None:
        msg = (
            f"class {class_name} not found in the generated GET /v2/self "
            "model; the post-generation patch must be updated for the new "
            "generated layout."
        )
        raise RuntimeError(msg)
    end = _class_body_end(lines, start)
    if any("_validate_active" in l for l in lines[start:end]):
        return text
    serializer_idx = next(
        (
            i
            for i in range(start + 1, end)
            if lines[i].lstrip().startswith("@model_serializer(")
        ),
        None,
    )
    if serializer_idx is not None:
        block = [*method_lines, ""]
        insert_at = serializer_idx
    else:
        block = ["", *method_lines]
        insert_at = end
        while insert_at - 1 > start and lines[insert_at - 1].strip() == "":
            insert_at -= 1
    lines[insert_at:insert_at] = block
    return "\n".join(lines) + "\n"


def patch_get_v2_selfop(path: Path) -> bool:
    """Re-inject the active-value validators into ``path``.

    Returns ``True`` if ``path`` was modified, ``False`` if it was already
    patched. Raises ``RuntimeError`` if the generated layout no longer
    matches the anchors the patch relies on, so a regeneration that breaks
    it fails loudly instead of silently shipping an unguarded model.
    """
    text = path.read_text()
    original = text
    text = _ensure_import(text)
    text = _inject_into_class(text, "AttioCom", ATTIO_COM_VALIDATOR_LINES)
    text = _inject_into_class(text, "ResponseBody", RESPONSE_BODY_VALIDATOR_LINES)
    if text == original:
        return False
    compile(text, str(path), "exec")
    path.write_text(text)
    return True


def main() -> int:
    changed = patch_get_v2_selfop(TARGET)
    rel = TARGET.relative_to(REPO_ROOT)
    if changed:
        print(f"post_generate_patch: patched {rel}")
    else:
        print(f"post_generate_patch: unchanged {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
