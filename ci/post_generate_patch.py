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

Patch: ``scripts/publish.sh`` and ``scripts/release.sh`` wrappers

    Speakeasy regenerates ``scripts/`` with its own templates, which in the
    2026-10 regeneration silently reverted ``scripts/publish.sh`` to a naive
    ``uv build && uv publish --token`` script, dropping the dual
    attio/gtm-attio release pipeline. ``.genignore`` now excludes ``scripts/``
    from generation, and this script additionally rewrites both wrappers to
    their canonical delegating form (the real implementations live in
    ``ci/publish.sh`` / ``ci/release.sh``, which the generator never
    touches) so a regeneration can never again ship the naive script — worst
    case it is restored here, loudly.

    Note: the pipeline's Dagger generation path exports only ``src/`` back
    to the host, so on that path this script sees the host's unmodified
    ``scripts/`` — the wrapper restoration is only exercised after host-CLI
    generation (the default) or when run standalone.

Patch: ``src/attio/models/input_value_union.py``

    The 0.25.1 breaking change (commit 07e4d5f) migrated ``InputValue18``
    (the timestamp variant) from ``value: date`` to ``value: str`` so
    callers must pass Attio's ISO 8601 timestamp strings. Direct
    construction of ``InputValue18(value=date(...))`` correctly raises
    ``ValidationError`` after the change, but a dict payload validated
    through ``List[InputValueUnion]`` (the element type of
    ``default_value.template`` on attribute create/update requests) did
    not: the all-optional variants ``InputValue5`` (``domain``),
    ``InputValue6`` (``email_address``), and ``InputValue12`` (``name``)
    have no required fields and inherit the Pydantic default ``extra=
    'ignore'``, so union resolution silently fell through to one of them,
    dropped the unknown ``value`` key, and serialized ``"template": [{}]`` —
    sending an empty object as the default value instead of raising.

    The overlay can't express this fix: setting ``additionalProperties:
    false`` on those three schema members would document the intent, but
    Speakeasy 1.800.1 does not translate it into ``extra='forbid'`` (the
    variants that already carry ``additionalProperties: false`` in the spec
    still generate with the default ``extra='ignore'``), so the generated
    code is unchanged. This patch instead injects
    ``model_config = pydantic.ConfigDict(extra="forbid")`` into the three
    all-optional classes so a payload whose keys match no union member
    exhausts the variants and raises ``ValidationError`` instead of being
    silently absorbed. Legitimate single-key payloads (``{"domain": ...}``,
    ``{"email_address": ...}``, ``{"first_name": ..., "last_name": ...}``)
    continue to validate and serialize identically.

Patch: ``src/attio/types/basemodel.py``

    The ``extra='forbid'`` patch on the ``InputValue`` catch-all variants
    makes ``InputValueUnion`` raise for a malformed template item, but the
    public attribute-create/attribute-patch models wrap ``default_value`` in
    ``OptionalNullable[DefaultValueUnion]``, whose ``Unset`` fallback is a
    zero-field model with the default ``extra='ignore'``. ``Unset`` therefore
    accepts any mapping, so the now-surfaced inner union error is swallowed
    and the request proceeds with ``default_value`` silently omitted rather
    than raising. This patch injects a ``@model_validator(mode="before")``
    onto ``Unset`` that rejects any value that is not the ``UNSET`` singleton
    (or the empty-dict no-arg construction form), so a mapping that fails the
    wrapped type exhausts the ``OptionalNullable`` union and surfaces the
    ``ValidationError`` instead of being silently dropped.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "src" / "attio" / "models" / "get_v2_selfop.py"
TARGET_INPUT_VALUE_UNION = (
    REPO_ROOT / "src" / "attio" / "models" / "input_value_union.py"
)
TARGET_BASEMODEL = REPO_ROOT / "src" / "attio" / "types" / "basemodel.py"

# scripts/ wrappers -> the ci/ implementation each wrapper must delegate to.
WRAPPER_IMPLS = {
    REPO_ROOT / "scripts" / "publish.sh": "ci/publish.sh",
    REPO_ROOT / "scripts" / "release.sh": "ci/release.sh",
}

_WRAPPER_TEMPLATE = """#!/usr/bin/env bash
# Thin wrapper — do not add logic here.
#
# `speakeasy run` regenerates scripts/ with its own templates (see
# .genignore), so this file deliberately only delegates to the real
# implementation in ci/, which the generator never touches.
# ci/post_generate_patch.py restores this wrapper after every regeneration
# in case it is ever overwritten anyway.
set -euo pipefail
exec bash "$(dirname "$0")/../{impl}" "$@"
"""

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


# The all-optional ``InputValue`` variants have no required fields and
# inherit the Pydantic default ``extra='ignore'``, which makes them silent
# catch-alls in ``InputValueUnion``: a dict payload whose keys match no
# value-typed member (e.g. ``{"value": <date>}`` after the 0.25.1 timestamp
# migration to ``str``) validates as an empty one of these and serializes
# to ``{}``. Forbidding extras makes the union exhaust its members and
# raise ``ValidationError`` instead. See the module docstring for context.
INPUT_VALUE_FORBID_EXTRA_CLASSES = ("InputValue5", "InputValue6", "InputValue12")
_FORBID_EXTRA_MARKER = 'model_config = pydantic.ConfigDict(extra="forbid")'


def _ensure_pydantic_import(text: str) -> str:
    """Ensure ``import pydantic`` is present for ``pydantic.ConfigDict``.

    The generated ``input_value_union.py`` already imports ``pydantic``
    (it uses ``pydantic.Field``); this fails loudly if a future
    regeneration drops the import, since the injected line would then
    reference an undefined name.
    """
    if not any(
        line == "import pydantic" or line.startswith("import pydantic ")
        for line in text.splitlines()
    ):
        msg = (
            "the generated input_value_union.py no longer has an "
            "`import pydantic` line; the post-generation patch must be "
            "updated."
        )
        raise RuntimeError(msg)
    return text


def _inject_forbid_extra(text: str, class_name: str) -> str:
    """Inject ``extra="forbid"`` as the first body line of ``class_name``.

    Idempotent: returns the text unchanged when the class already carries
    the ``extra="forbid"`` config. Raises ``RuntimeError`` if the class
    declaration is missing (layout drift) or if the class already carries a
    different ``model_config`` (so a future regeneration that emits its own
    config is surfaced loudly rather than silently overridden).
    """
    lines = text.splitlines(keepends=False)
    class_line = f"class {class_name}(BaseModel):"
    start = next(
        (i for i, line in enumerate(lines) if line == class_line),
        None,
    )
    if start is None:
        msg = (
            f"class {class_name} not found in the generated "
            "input_value_union.py; the post-generation patch must be "
            "updated for the new generated layout."
        )
        raise RuntimeError(msg)
    end = _class_body_end(lines, start)
    existing_idx = next(
        (
            i
            for i in range(start + 1, end)
            if lines[i].lstrip().startswith("model_config")
        ),
        None,
    )
    if existing_idx is not None:
        if _FORBID_EXTRA_MARKER in lines[existing_idx]:
            return text
        msg = (
            f"class {class_name} in input_value_union.py already carries a "
            f"model_config that is not `extra=\"forbid\"` "
            f"({lines[existing_idx].strip()!r}); the post-generation patch "
            "must be updated."
        )
        raise RuntimeError(msg)
    lines.insert(start + 1, f"    {_FORBID_EXTRA_MARKER}")
    return "\n".join(lines) + "\n"


def patch_input_value_union(path: Path) -> bool:
    """Re-inject ``extra="forbid"`` into the all-optional InputValue variants.

    Returns ``True`` if ``path`` was modified, ``False`` if it was already
    patched. Raises ``RuntimeError`` if the generated layout no longer
    matches the anchors the patch depends on, so a regeneration that breaks
    it fails loudly instead of silently shipping the silent-catch-all bug
    back into the tree.
    """
    text = path.read_text()
    original = text
    text = _ensure_pydantic_import(text)
    for class_name in INPUT_VALUE_FORBID_EXTRA_CLASSES:
        text = _inject_forbid_extra(text, class_name)
    if text == original:
        return False
    compile(text, str(path), "exec")
    path.write_text(text)
    return True


# ``Unset`` is the permissive zero-field fallback in ``OptionalNullable[T]``.
# With the default ``extra='ignore'`` it accepts any mapping, so a payload that
# fails the wrapped type ``T`` silently serializes as the unset sentinel and
# the field is dropped from the request instead of raising. The injected
# ``@model_validator(mode="before")`` rejects any value that is not the
# ``UNSET`` singleton (or the empty-dict no-arg construction form), so the
# union exhausts its members and surfaces the real error. See the module
# docstring for context.
_UNSET_VALIDATOR_LINES = [
    '    @model_validator(mode="before")',
    "    @classmethod",
    "    def _reject_non_unset(cls, value: Any) -> Any:",
    '        r"""Reject values that are not the ``UNSET`` sentinel.',
    "",
    "        ``Unset`` is the permissive zero-field fallback in",
    "        ``OptionalNullable[T]``. Without this validator it accepts any",
    "        mapping (extra keys are ignored), so a payload that fails the",
    "        wrapped type ``T`` silently serializes as the unset sentinel and",
    "        the field is dropped from the request instead of raising a",
    "        ``ValidationError``. Restricting construction to the ``Unset``",
    "        instance (and the empty-dict no-arg form) makes the union exhaust",
    "        its members and surface the real error.",
    '        """',
    "        if isinstance(value, Unset) or value == {}:",
    "            return value",
    "        raise ValueError(",
    '            "expected the UNSET sentinel; got a value that should have "',
    '            "matched the wrapped type"',
    "        )",
    "",
]


def _ensure_basemodel_import(text: str) -> str:
    """Ensure ``model_validator`` is imported in ``basemodel.py``.

    The generated file imports ``ConfigDict, model_serializer`` from
    ``pydantic``; this adds ``model_validator`` to that import. Fails loudly
    if the expected import line is missing.
    """
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
            "the generated basemodel.py no longer has the expected "
            "`from pydantic import model_serializer` import line; the "
            "post-generation patch must be updated."
        )
        raise RuntimeError(msg)
    if "model_validator" in line:
        return text
    new_line = line.replace("model_serializer", "model_serializer, model_validator", 1)
    return text.replace(line, new_line, 1)


def _inject_unset_validator(text: str) -> str:
    """Insert the ``_reject_non_unset`` validator into the ``Unset`` class.

    The validator is anchored before the existing ``@model_serializer``
    decorator so source order reads validators-then-serializer. Idempotent:
    returns the text unchanged when ``Unset`` already carries the validator.
    Raises ``RuntimeError`` if the ``Unset`` class declaration or the
    ``@model_serializer`` anchor is missing (layout drift).
    """
    lines = text.splitlines(keepends=False)
    start = next(
        (i for i, l in enumerate(lines) if l.startswith("class Unset(")),
        None,
    )
    if start is None:
        msg = (
            "class Unset not found in basemodel.py; the post-generation "
            "patch must be updated for the new generated layout."
        )
        raise RuntimeError(msg)
    end = _class_body_end(lines, start)
    if any("_reject_non_unset" in l for l in lines[start:end]):
        return text
    serializer_idx = next(
        (
            i
            for i in range(start + 1, end)
            if lines[i].lstrip().startswith("@model_serializer(")
        ),
        None,
    )
    if serializer_idx is None:
        msg = (
            "class Unset in basemodel.py no longer carries the "
            "@model_serializer decorator the patch anchors to; the "
            "post-generation patch must be updated."
        )
        raise RuntimeError(msg)
    lines[serializer_idx:serializer_idx] = _UNSET_VALIDATOR_LINES
    return "\n".join(lines) + "\n"


def patch_unset_reject_mappings(path: Path) -> bool:
    """Re-inject the ``_reject_non_unset`` validator into ``Unset``.

    Returns ``True`` if ``path`` was modified, ``False`` if it was already
    patched. Raises ``RuntimeError`` if the generated layout no longer
    matches the anchors the patch depends on, so a regeneration that breaks
    it fails loudly instead of silently shipping the silent-drop bug back
    into the tree.
    """
    text = path.read_text()
    original = text
    text = _ensure_basemodel_import(text)
    text = _inject_unset_validator(text)
    if text == original:
        return False
    compile(text, str(path), "exec")
    path.write_text(text)
    return True


def restore_script_wrappers() -> list[Path]:
    """Rewrite the ``scripts/*.sh`` wrappers to their canonical form.

    Speakeasy owns ``scripts/`` and rewrites it from its templates on every
    ``speakeasy run``; the wrappers must therefore contain nothing but the
    delegation to the real implementation under ``ci/``. Any other content
    (e.g. Speakeasy's naive ``uv build && uv publish`` publish script) is
    replaced here. Returns the list of wrappers that were rewritten; an
    already-canonical tree returns an empty list.
    """
    restored: list[Path] = []
    for wrapper, impl in WRAPPER_IMPLS.items():
        if not (REPO_ROOT / impl).is_file():
            msg = (
                f"{impl} is missing; cannot restore the "
                f"{wrapper.relative_to(REPO_ROOT)} wrapper it delegates to"
            )
            raise RuntimeError(msg)
        canonical = _WRAPPER_TEMPLATE.format(impl=impl)
        # Mode counts too: the generator writes non-executable files, so a
        # wrapper with the right text but a lost exec bit must be repaired,
        # not skipped.
        is_canonical = wrapper.exists() and wrapper.read_text() == canonical
        if is_canonical and wrapper.stat().st_mode & 0o111:
            continue
        # The generator may also have cleaned up scripts/ entirely; this
        # function is the fallback for .genignore not being honored, so it
        # must cope with the directory being gone too.
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(canonical)
        wrapper.chmod(0o755)
        restored.append(wrapper)
    return restored


def main() -> int:
    messages: list[str] = []

    # Wrappers first: a layout drift that makes patch_get_v2_selfop raise
    # must not skip the scripts/ restoration — that restore is the fallback
    # for .genignore not being honored, and aborting before it runs is how
    # a naive publish script survives in the tree.
    for wrapper in restore_script_wrappers():
        messages.append(
            f"post_generate_patch: restored wrapper {wrapper.relative_to(REPO_ROOT)}",
        )

    changed = patch_get_v2_selfop(TARGET)
    rel = TARGET.relative_to(REPO_ROOT)
    if changed:
        messages.append(f"post_generate_patch: patched {rel}")
    else:
        messages.append(f"post_generate_patch: unchanged {rel}")

    ivu_changed = patch_input_value_union(TARGET_INPUT_VALUE_UNION)
    ivu_rel = TARGET_INPUT_VALUE_UNION.relative_to(REPO_ROOT)
    if ivu_changed:
        messages.append(f"post_generate_patch: patched {ivu_rel}")
    else:
        messages.append(f"post_generate_patch: unchanged {ivu_rel}")

    bm_changed = patch_unset_reject_mappings(TARGET_BASEMODEL)
    bm_rel = TARGET_BASEMODEL.relative_to(REPO_ROOT)
    if bm_changed:
        messages.append(f"post_generate_patch: patched {bm_rel}")
    else:
        messages.append(f"post_generate_patch: unchanged {bm_rel}")

    print("\n".join(messages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
