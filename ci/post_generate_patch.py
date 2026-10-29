#!/usr/bin/env python3
"""Re-apply manual patches to Speakeasy-generated SDK source.

``speakeasy run`` rewrites ``generated/`` from the OpenAPI overlay, so any
hand-edit to a generated file is lost on the next regeneration. This script
idempotently re-injects the edits that ``overlay.yaml`` cannot express, and
the generation pipeline (``ci/pipeline.py``) runs it after every generation
so the tree the tests, build, and PR commit consume already carries them.

Run it standalone after a direct ``speakeasy run``::

    python ci/post_generate_patch.py

It is safe to run on an already-patched tree (a no-op then).

Patch: ``generated/src/attio/models/get_v2_selfop.py``

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

    Note: the pipeline's Dagger generation path exports only ``generated/`` back
    to the host, so on that path this script sees the host's unmodified
    ``scripts/`` — the wrapper restoration is only exercised after host-CLI
    generation (the default) or when run standalone.

Patch: ``pyproject.toml`` and ``README.md``

    Speakeasy owns both files, so this script also restores the standalone
    ``gtm-attio`` console entry point and its user-facing CLI documentation.

Patch: ``generated/src/attio/_hooks/sdkhooks.py`` and ``generated/src/attio/_hooks/__init__.py``

    ``registration.py`` is a one-time-generated, maintainer-editable
    scaffolding file (not tracked in ``.speakeasy/gen.lock``) whose header
    instructs maintainers to register lifecycle hooks inside the
    ``init_hooks`` function. The 2026-03-28 regeneration commit (``dc8cebc``)
    overwrote ``sdkhooks.py`` — a "DO NOT EDIT" generated file — with a clean
    Speakeasy template that lacked both the ``from .registration import
    init_hooks`` import and the ``init_hooks(self)`` call in
    ``SDKHooks.__init__``, orphaning ``init_hooks``: hooks a maintainer
    added to ``registration.py`` were silently never registered. The same
    commit also dropped the ``from .registration import *`` re-export from
    the hooks package ``__init__.py``. This script idempotently restores
    all three lines after every generation so the maintainership seam
    survives; nothing changes for end users because the shipped
    ``init_hooks`` stub is empty (the call is a no-op until a maintainer
    adds hook registrations).

Patch: ``generated/src/attio/models/__init__.py`` 0.26.1 model rename aliases

    The 2026-10-03 regeneration renamed public model symbols that had already
    shipped in the 0.26.1 patch release: the activity-record
    ``ForbiddenCodeUnion`` names (POST and PUT, plus their ``TypedDict``
    twins) became ``CodeUnion`` names, and
    ``PutV2ListsListEntriesCodeMultipleMatchResults`` became the unprefixed
    ``CodeMultipleMatchResults``. Dropping public names in a patch release
    breaks ``from attio.models import ...`` (and the per-module import) with
    ``ImportError`` for users upgrading from 0.26.1, so after every
    generation this script re-injects ``OldName = NewName`` module-level
    aliases into the renamed operation modules and restores the old names in
    the three export structures of ``models/__init__.py`` (the
    ``TYPE_CHECKING`` import block, ``__all__``, and ``_dynamic_imports``).
    Retire the aliases deliberately in a major release by removing the
    ``MODEL_RENAME_ALIASES`` entries.

Patch: ``generated/src/attio/utils/enums.py`` and ``generated/src/attio/utils/__init__.py``

    The 2026-10-25 regeneration (``df87959``) emitted ``utils/enums.py``,
    a 134-line ``OpenEnumMeta(enum.EnumMeta)`` metaclass, and re-exported
    it from ``utils/__init__.py`` (the ``TYPE_CHECKING`` import, ``__all__``,
    and ``_dynamic_imports`` entries). No generated enum ever used
    ``metaclass=OpenEnumMeta`` (the SDK's only enum, ``OAuth2Scope``, is a
    plain ``Enum``), and unknown-variant handling lives in
    ``types/basemodel.py`` + ``utils/serializers.py``, so the metaclass was
    dead code. This patch deletes ``utils/enums.py`` and strips the three
    re-export lines from ``utils/__init__.py`` after every regeneration so
    the removal survives. It is a no-op on the committed (already-stripped)
    tree. If a future spec/config ever emits a generated enum with
    ``metaclass=OpenEnumMeta`` (i.e. some module outside ``utils/enums.py``
    references it as a metaclass), this raises ``RuntimeError`` rather than
    deleting a file the SDK then needs.

Patch: ``generated/src/attio/utils/security.py`` empty-value guard

    The 0.26.4 template (2.952.5) returned early from ``security
    value handling when a security value is the empty string, so
    ``oauth2=""`` left the ``Authorization`` header absent and a custom HTTP
    client's own auth survived. The pinned 1.800.1 CLI emits the older
    template without the guard, so this patch re-inserts ``if value == "":
    return`` before ``header_name`` is resolved in ``handle_security_scheme``.
    It is idempotent and raises ``RuntimeError`` if the anchor drifts.

Patch: ``generated/src/attio/utils/datetimes.py`` duration adapter annotation

    Template 2.952.5 emitted ``_DURATION_ADAPTER: TypeAdapter[timedelta] =
    TypeAdapter(timedelta)``; the pinned 1.800.1 CLI (template 2.943.0) drops
    the annotation, which makes ``mypy generated/src`` fail with ``Need type
    annotation`` under newer pydantic releases (2.14+). This patch restores
    the annotation after every generation. Retire it when a re-pin brings
    back a template that emits the annotation.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "generated" / "src" / "attio" / "models" / "get_v2_selfop.py"
SDKHOOKS_PATH = REPO_ROOT / "generated" / "src" / "attio" / "_hooks" / "sdkhooks.py"
HOOKS_INIT_PATH = REPO_ROOT / "generated" / "src" / "attio" / "_hooks" / "__init__.py"
MODELS_DIR = REPO_ROOT / "generated" / "src" / "attio" / "models"
MODELS_INIT_PATH = MODELS_DIR / "__init__.py"
GENERATED_SRC_DIR = REPO_ROOT / "generated" / "src" / "attio"
UTILS_INIT_PATH = REPO_ROOT / "generated" / "src" / "attio" / "utils" / "__init__.py"
UTILS_ENUMS_PATH = REPO_ROOT / "generated" / "src" / "attio" / "utils" / "enums.py"

# Anchors and lines for the SDKHooks init_hooks wiring patch (see
# ``ensure_init_hooks_wiring`` / ``ensure_hooks_package_reexport``).
_REGISTRATION_IMPORT_LINE = "from .registration import init_hooks"
_REGISTRATION_REEXPORT_LINE = "from .registration import *"
_INIT_HOOKS_CALL = "init_hooks(self)"
_AFTER_ERROR_HOOKS_ANCHOR = "self.after_error_hooks: List[AfterErrorHook] = []"

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

CLI_SCRIPT_LINE = 'gtm-attio = "attio_cli.main:main"'
README_CLI_START = "<!-- Start Standalone CLI [cli] -->"
README_CLI_END = "<!-- End Standalone CLI [cli] -->"
README_CLI_SECTION = """<!-- Start Standalone CLI [cli] -->
## Standalone CLI

Install and run the agent-friendly CLI without cloning this repository:

```bash
export ATTIO_API_KEY="your-attio-api-key"
uvx gtm-attio people upsert person@example.com \\
  --first-name Ada --last-name Lovelace
```

The CLI also reads `ATTIO_API_KEY` from `.env.local` or `.env` in the current
directory. Environment variables take precedence. Search/list commands are
read-only. Add, update, and upsert commands write directly to Attio without a
confirmation prompt; every command prints a JSON reliability envelope.

Both the `attio` and `gtm-attio` distribution artifacts expose the
`gtm-attio` command for compatibility. They are alternate names for packages
that provide the same `attio` import namespace; install only one distribution
in a Python environment.

People commands use email as their identity key. `search` is read-only; `add`
fails if the email already exists; `update` requires exactly one matching
person. `upsert` creates or updates as before. Common write options include
repeatable `--add-email`, `--replace-emails`, `--job-title`, `--phone`,
`--phone-country-code`, `--linkedin`, `--company` (company domain), `--notes`,
and `--strict`. Prefix international phone numbers with `+`; local numbers
require `--phone-country-code` (ISO-3166-1 alpha-2). Pair `--location` with
`--country-code`; `--location-mode city|raw` controls its mapping.

```bash
uvx gtm-attio people upsert --json '{"email":"person@example.com","first_name":"Ada","job_title":"Mathematician"}'
```

```bash
uvx gtm-attio people search person@example.com
uvx gtm-attio people add person@example.com --first-name Ada --last-name Lovelace
uvx gtm-attio people update person@example.com --job-title Mathematician
```

Company commands use validated JSON. The `domain` is the exact identity and is
written to Attio's `domains` attribute; `values` contains other Attio record
attribute values in the API's `{attribute_slug: [value, ...]}` format. Add
rejects an existing domain and update requires exactly one match:

```bash
uvx gtm-attio companies search --json '{"domain":"example.com"}'
uvx gtm-attio companies add --json '{"domain":"example.com","values":{"name":[{"value":"Example Inc"}]}}'
uvx gtm-attio companies update --json '{"domain":"example.com","values":{"description":["Prospect"]}}'
```

Notes attach to one existing record. List is read-only; add and update write
immediately. Updates target a note ID and only replace the supplied fields:

```bash
uvx gtm-attio notes list --json '{"parent_object":"people","parent_record_id":"RECORD_ID"}'
uvx gtm-attio notes add --json '{"parent_object":"people","parent_record_id":"RECORD_ID","title":"Discovery call","content":"Discussed the launch plan.","format":"plaintext"}'
uvx gtm-attio notes update --json '{"note_id":"NOTE_ID","content":"Updated call notes."}'
```

The output envelope reports `success`, `partial_success`, `action`,
`record_id`, `warnings`, `skipped_fields`, `errors`, and `meta`. Missing
optional workspace attributes are retried without that field and reported as
warnings for people writes. Search/list results are in `meta.results`. Invalid
optional person values are skipped and reported; `--strict` turns those
mismatches and invalid values into errors. Ambiguous person/company writes
always fail without modifying a record.
Successful and partial-success operations exit 0, runtime failures exit 1,
and command-line usage errors exit 2.
<!-- End Standalone CLI [cli] -->"""

# Public model symbols renamed after they shipped, as ``{module: {old: new}}``.
# Empty: the 0.26.1 aliases were retired in the breaking 0.27.0 spec-drift
# release (error classes were renamed too, without aliases).
# ``ensure_module_aliases`` / ``ensure_models_init_aliases`` re-inject the old
# names as aliases of the new ones after every generation so the patch
# release keeps ``from attio.models import <old>`` (and the per-module
# import) working.
MODEL_RENAME_ALIASES: dict[str, dict[str, str]] = {}


def ensure_project_script(path: Path) -> bool:
    """Ensure the ``gtm-attio`` console entry point exists in pyproject.toml."""
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    header = "[project.scripts]"
    try:
        header_index = next(i for i, line in enumerate(lines) if line.strip() == header)
    except StopIteration:
        updated = text.rstrip() + "\n\n[project.scripts]\n" + CLI_SCRIPT_LINE + "\n"
        path.write_text(updated)
        return True

    next_header = next(
        (
            i
            for i in range(header_index + 1, len(lines))
            if lines[i].lstrip().startswith("[")
        ),
        len(lines),
    )
    existing = next(
        (
            i
            for i in range(header_index + 1, next_header)
            if lines[i].lstrip().startswith("gtm-attio =")
        ),
        None,
    )
    if existing is not None and lines[existing].strip() == CLI_SCRIPT_LINE:
        return False
    if existing is not None:
        lines[existing] = CLI_SCRIPT_LINE + "\n"
    else:
        lines.insert(header_index + 1, CLI_SCRIPT_LINE + "\n")
    path.write_text("".join(lines))
    return True


def ensure_readme_cli_section(path: Path) -> bool:
    """Restore the CLI documentation and its table-of-contents link."""
    text = path.read_text()
    if README_CLI_START in text and README_CLI_END in text:
        start = text.index(README_CLI_START)
        end = text.index(README_CLI_END, start) + len(README_CLI_END)
        updated = text[:start] + README_CLI_SECTION + text[end:]
    else:
        marker = "<!-- End SDK Installation [installation] -->"
        if marker in text:
            index = text.index(marker) + len(marker)
            updated = text[:index] + "\n\n" + README_CLI_SECTION + text[index:]
        else:
            updated = text.rstrip() + "\n\n" + README_CLI_SECTION + "\n"

    toc_label = "  * [Standalone CLI](#standalone-cli)"
    if toc_label not in updated:
        installation_line = "  * [SDK Installation](#sdk-installation)"
        if installation_line in updated:
            updated = updated.replace(
                installation_line,
                installation_line + "\n" + toc_label,
                1,
            )
    if updated == text:
        return False
    path.write_text(updated)
    return True


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
            import_line
            for import_line in text.splitlines()
            if import_line.startswith("from pydantic import ")
            and "model_serializer" in import_line
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
        (
            i
            for i, line_text in enumerate(lines)
            if line_text.startswith(f"class {class_name}(")
        ),
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
    if any("_validate_active" in body_line for body_line in lines[start:end]):
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


def ensure_init_hooks_wiring(path: Path) -> bool:
    """Re-inject the ``init_hooks`` maintenanceship seam into ``sdkhooks.py``.

    ``speakeasy run`` rewrites ``generated/src/attio/_hooks/sdkhooks.py`` from a clean
    template that lacks the ``from .registration import init_hooks`` import
    and the ``init_hooks(self)`` call in ``SDKHooks.__init__``. Without
    them the customization seam in ``registration.py`` (which the generator
    never overwrites) is orphaned, so hooks a maintainer registers there are
    silently discarded. This idempotently restores both lines after every
    generation.

    Returns ``True`` if ``path`` was modified, ``False`` if already wired.
    Raises ``RuntimeError`` if the generated layout no longer matches the
    anchors the patch relies on, so a regeneration that breaks it fails
    loudly instead of silently shipping disconnected hooks.
    """
    text = path.read_text()
    original = text

    # Import: insert `from .registration import init_hooks` right after the
    # `from .types import (...)` block (the multi-line import's closing
    # paren is the anchor), matching the pre-dc8cebc placement.
    if _REGISTRATION_IMPORT_LINE not in text:
        lines = text.splitlines(keepends=False)
        types_open_idx = next(
            (
                i
                for i, line in enumerate(lines)
                if line.startswith("from .types import (")
            ),
            None,
        )
        if types_open_idx is None:
            msg = (
                "the generated SDKHooks no longer has the expected "
                "`from .types import (` import block; the post-generation "
                "patch must be updated for the new generated layout."
            )
            raise RuntimeError(msg)
        close_idx = next(
            (
                i
                for i in range(types_open_idx + 1, len(lines))
                if lines[i].rstrip() == ")"
            ),
            None,
        )
        if close_idx is None:
            msg = (
                "the generated `from .types import (...)` block in "
                "sdkhooks.py has no closing `)`; the post-generation patch "
                "must be updated."
            )
            raise RuntimeError(msg)
        trailing = "\n" if text.endswith("\n") else ""
        lines.insert(close_idx + 1, _REGISTRATION_IMPORT_LINE)
        text = "\n".join(lines) + trailing

    # Call: append `init_hooks(self)` as the last line of SDKHooks.__init__,
    # immediately after the after_error_hooks assignment (the final init).
    if _INIT_HOOKS_CALL not in text:
        if _AFTER_ERROR_HOOKS_ANCHOR not in text:
            msg = (
                "the generated SDKHooks.__init__ no longer has the expected "
                "`self.after_error_hooks: List[AfterErrorHook] = []` "
                "anchor; the post-generation patch must be updated for the "
                "new generated layout."
            )
            raise RuntimeError(msg)
        text = text.replace(
            _AFTER_ERROR_HOOKS_ANCHOR,
            _AFTER_ERROR_HOOKS_ANCHOR + "\n        " + _INIT_HOOKS_CALL,
            1,
        )

    if text == original:
        return False
    compile(text, str(path), "exec")
    path.write_text(text)
    return True


def ensure_hooks_package_reexport(path: Path) -> bool:
    """Restore the ``from .registration import *`` re-export in the hooks package.

    The 2026-03-28 regeneration dropped this line from
    ``generated/src/attio/_hooks/__init__.py``, so ``from attio._hooks import
    init_hooks`` no longer resolved. The direct path
    ``from attio._hooks.registration import init_hooks`` still works, so the
    re-export is not load-bearing today, but restoring it keeps the package
    seam complete. Idempotent; raises if the ``from .types import *`` anchor
    is gone.
    """
    text = path.read_text()
    if _REGISTRATION_REEXPORT_LINE in text:
        return False
    anchor = "from .types import *"
    if anchor not in text:
        msg = (
            "generated/src/attio/_hooks/__init__.py no longer has the "
            "expected `from .types import *` anchor; the post-generation "
            "patch must be updated for the new generated layout."
        )
        raise RuntimeError(msg)
    text = text.replace(anchor, anchor + "\n" + _REGISTRATION_REEXPORT_LINE, 1)
    compile(text, str(path), "exec")
    path.write_text(text)
    return True


_ALIAS_LINE_LIMIT = 88


def _alias_assignment(old: str, new: str) -> list[str]:
    """Return the ``old = new`` alias statement, wrapped at 88 columns."""
    if len(f"{old} = {new}") <= _ALIAS_LINE_LIMIT:
        return [f"{old} = {new}"]
    return [f"{old} = (", f"    {new}", ")"]


def _ensure_module_alias(text: str, old: str, new: str) -> str:
    """Inject ``old = new`` right after the ``new`` symbol's definition.

    The definition statement is anchored on a line starting with
    ``<new> = ``; a line ending in ``(`` opens a block that closes on a lone
    ``)`` line, anything else is a single-line statement. Two blank lines
    separate the alias from the definition, matching the generated layout.
    """
    lines = text.splitlines(keepends=False)
    if any(line.startswith(f"{old} = ") for line in lines):
        return text
    start = next(
        (i for i, line in enumerate(lines) if line.startswith(f"{new} = ")),
        None,
    )
    if start is None:
        msg = (
            f"the generated model no longer defines `{new}`, the rename "
            f"target of the 0.26.1 alias `{old}`; the post-generation patch "
            "must be updated for the new generated layout."
        )
        raise RuntimeError(msg)
    end = start
    if lines[start].rstrip().endswith("("):
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].rstrip() == ")"),
            None,
        )
        if end is None:
            msg = (
                f"the definition of `{new}` opens a block with no closing "
                "`)` line; the post-generation patch must be updated."
            )
            raise RuntimeError(msg)
    lines[end + 1 : end + 1] = ["", "", *_alias_assignment(old, new)]
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + trailing


def ensure_module_aliases(path: Path, module: str) -> bool:
    """Re-inject the 0.26.1 rename aliases into a generated operation module.

    Returns ``True`` if ``path`` was modified, ``False`` if it already
    carries every alias. Raises ``RuntimeError`` when the module no longer
    defines a rename target, so a regeneration that breaks the anchors
    fails loudly instead of silently shipping broken imports.
    """
    text = path.read_text()
    original = text
    for old, new in MODEL_RENAME_ALIASES[module].items():
        text = _ensure_module_alias(text, old, new)
    if text == original:
        return False
    compile(text, str(path), "exec")
    path.write_text(text)
    return True


def _find_structure_start(lines: list[str], prefix: str, structure: str) -> int:
    """Return the index of the first line starting with ``prefix``."""
    start = next(
        (i for i, line in enumerate(lines) if line.startswith(prefix)),
        None,
    )
    if start is None:
        msg = (
            f"models/__init__.py no longer has the expected `{structure}` "
            "structure; the post-generation patch must be updated for the "
            "new generated layout."
        )
        raise RuntimeError(msg)
    return start


def _find_structure_end(
    lines: list[str],
    start: int,
    closer: str,
    structure: str,
) -> int:
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].rstrip() == closer),
        None,
    )
    if end is None:
        msg = (
            f"models/__init__.py has a `{structure}` structure with no "
            f"closing `{closer}` line; the post-generation patch must be "
            "updated."
        )
        raise RuntimeError(msg)
    return end


def _ensure_init_import_entry(lines: list[str], module: str, old: str) -> None:
    """Add ``old`` to the module's ``TYPE_CHECKING`` import block, sorted."""
    entry = f"        {old},"
    if entry in lines:
        return
    header = f"    from .{module} import ("
    start = next((i for i, line in enumerate(lines) if line == header), None)
    if start is None:
        msg = (
            f"models/__init__.py no longer imports from `.{module}`; the "
            "post-generation patch must be updated for the new generated "
            "layout."
        )
        raise RuntimeError(msg)
    end = _find_structure_end(lines, start, "    )", f"from .{module} import")
    for i in range(start + 1, end):
        if lines[i].strip().removesuffix(",") > old:
            lines.insert(i, entry)
            return
    lines.insert(end, entry)


def _ensure_init_all_entry(lines: list[str], old: str) -> None:
    """Add ``old`` to ``__all__`` at its sorted position."""
    entry = f'    "{old}",'
    if entry in lines:
        return
    start = _find_structure_start(lines, "__all__", "__all__")
    end = _find_structure_end(lines, start, "]", "__all__")
    for i in range(start + 1, end):
        if lines[i].strip().removesuffix(",").strip('"') > old:
            lines.insert(i, entry)
            return
    lines.insert(end, entry)


def _ensure_init_dynamic_entry(lines: list[str], module: str, old: str) -> None:
    """Add ``old`` to the module's ``_dynamic_imports`` group, sorted."""
    entry = f'    "{old}": ".{module}",'
    if entry in lines:
        return
    start = _find_structure_start(lines, "_dynamic_imports", "_dynamic_imports")
    end = _find_structure_end(lines, start, "}", "_dynamic_imports")
    group_suffix = f': ".{module}",'
    group_start = next(
        (i for i in range(start + 1, end) if lines[i].endswith(group_suffix)),
        None,
    )
    if group_start is None:
        msg = (
            f"models/__init__.py has no `_dynamic_imports` group for "
            f"`.{module}`; the post-generation patch must be updated for "
            "the new generated layout."
        )
        raise RuntimeError(msg)
    group_end = group_start
    while group_end < end and lines[group_end].endswith(group_suffix):
        group_end += 1
    for i in range(group_start, group_end):
        if lines[i].split('"')[1] > old:
            lines.insert(i, entry)
            return
    lines.insert(group_end, entry)


def ensure_models_init_aliases(path: Path) -> bool:
    """Restore the 0.26.1 rename aliases to the ``models/__init__.py`` exports.

    Every old name is added to the three export structures (the
    ``TYPE_CHECKING`` import block, ``__all__``, and ``_dynamic_imports``)
    at its sorted position so both ``from attio.models import <old>`` and
    ``dir(attio.models)`` keep working. Idempotent; raises ``RuntimeError``
    when an anchor structure drifts.
    """
    text = path.read_text()
    lines = text.splitlines(keepends=False)
    for module, aliases in MODEL_RENAME_ALIASES.items():
        for old in aliases:
            _ensure_init_import_entry(lines, module, old)
            _ensure_init_all_entry(lines, old)
            _ensure_init_dynamic_entry(lines, module, old)
    updated = "\n".join(lines) + "\n"
    if updated == text:
        return False
    compile(updated, str(path), "exec")
    path.write_text(updated)
    return True


def ensure_model_rename_aliases() -> list[str]:
    """Apply every 0.26.1 rename-alias patch; return the restored files."""
    restored: list[str] = []
    for module in MODEL_RENAME_ALIASES:
        path = MODELS_DIR / f"{module}.py"
        if ensure_module_aliases(path, module):
            restored.append(path.name)
    if ensure_models_init_aliases(MODELS_INIT_PATH):
        restored.append(MODELS_INIT_PATH.name)
    return restored


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


# Lines the OpenEnumMeta removal strips from ``utils/__init__.py`` (the
# ``TYPE_CHECKING`` import, the ``__all__`` entry, and the
# ``_dynamic_imports`` lazy-loader mapping). Each is alphabetically sorted
# into its structure by the generator, so removing the literal line is the
# inverse of the regeneration that re-adds it.
_OPEN_ENUM_META_INIT_LINES = (
    "    from .enums import OpenEnumMeta",
    '    "OpenEnumMeta",',
    '    "OpenEnumMeta": ".enums",',
)


def remove_open_enum_meta() -> list[str]:
    """Delete the unused ``OpenEnumMeta`` metaclass module and its re-exports.

    ``speakeasy run`` re-emits ``generated/src/attio/utils/enums.py`` (the
    ``OpenEnumMeta`` metaclass) and the three matching re-export lines in
    ``generated/src/attio/utils/__init__.py`` on every regeneration. No
    generated enum uses ``metaclass=OpenEnumMeta`` (the SDK's only enum,
    ``OAuth2Scope``, is a plain ``Enum``), so the module is dead code; this
    re-applies the removal after every generation so it is not silently
    undone.

    Returns the list of paths it touched. It is a no-op (returns ``[]``) on
    the committed, already-stripped tree. Raises ``RuntimeError`` if a
    regenerated enum outside ``utils/enums.py`` references
    ``metaclass=OpenEnumMeta`` — a future open-enum spec/config would emit
    exactly that, and deleting the module the SDK then needs must fail
    loudly instead of shipping a broken tree.
    """
    touched: list[str] = []

    if UTILS_ENUMS_PATH.exists():
        for path in GENERATED_SRC_DIR.rglob("*.py"):
            if path == UTILS_ENUMS_PATH:
                continue
            text = path.read_text(encoding="utf-8")
            if "metaclass=OpenEnumMeta" in text:
                msg = (
                    f"{path.relative_to(REPO_ROOT)} references "
                    "`metaclass=OpenEnumMeta`; a future spec/config now uses "
                    "the open-enum metaclass, so the post-generation patch "
                    "must not delete utils/enums.py. Remove the "
                    "remove_open_enum_meta patch from ci/post_generate_patch.py."
                )
                raise RuntimeError(msg)
        UTILS_ENUMS_PATH.unlink()
        touched.append(str(UTILS_ENUMS_PATH.relative_to(REPO_ROOT)))

    init_text = UTILS_INIT_PATH.read_text(encoding="utf-8")
    original = init_text
    for line in _OPEN_ENUM_META_INIT_LINES:
        init_text = init_text.replace(line + "\n", "", 1)
    if init_text != original:
        compile(init_text, str(UTILS_INIT_PATH), "exec")
        UTILS_INIT_PATH.write_text(init_text, encoding="utf-8")
        touched.append(str(UTILS_INIT_PATH.relative_to(REPO_ROOT)))

    return touched


def ensure_security_empty_guard(path: Path) -> bool:
    """Re-insert the empty-string early-return in ``utils/security.py``."""
    text = path.read_text(encoding="utf-8")
    guard = '    if value == "":\n        return\n\n'
    anchor = "    header_name = security_metadata.get_field_name(field_name)\n"
    if guard + anchor in text:
        return False
    if text.count(anchor) != 1:
        msg = f"cannot locate empty-value guard anchor in {path}"
        raise RuntimeError(msg)
    updated = text.replace(anchor, guard + anchor)
    compile(updated, str(path), "exec")
    path.write_text(updated, encoding="utf-8")
    return True


def ensure_duration_adapter_annotation(path: Path) -> bool:
    """Restore the ``TypeAdapter[timedelta]`` annotation in ``datetimes.py``."""
    text = path.read_text(encoding="utf-8")
    plain = "_DURATION_ADAPTER = TypeAdapter(timedelta)\n"
    if plain not in text:
        if "_DURATION_ADAPTER: TypeAdapter[timedelta]" in text:
            return False
        msg = f"cannot locate _DURATION_ADAPTER assignment in {path}"
        raise RuntimeError(msg)
    updated = text.replace(
        plain,
        "_DURATION_ADAPTER: TypeAdapter[timedelta] = TypeAdapter(timedelta)\n",
    )
    compile(updated, str(path), "exec")
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    messages: list[str] = []

    for path, ensure, name in (
        (
            REPO_ROOT / "pyproject.toml",
            ensure_project_script,
            "pyproject.toml CLI entry point",
        ),
        (REPO_ROOT / "README.md", ensure_readme_cli_section, "README CLI section"),
    ):
        if ensure(path):
            messages.append(f"post_generate_patch: restored {name}")

    # Wrappers first: a layout drift that makes any later fallible patch raise
    # must not skip the scripts/ restoration — that restore is the fallback
    # for .genignore not being honored, and aborting before it runs is how
    # a naive publish script survives in the tree.
    for wrapper in restore_script_wrappers():
        messages.append(
            f"post_generate_patch: restored wrapper {wrapper.relative_to(REPO_ROOT)}",
        )

    for touched in remove_open_enum_meta():
        messages.append(f"post_generate_patch: removed {touched}")

    # Fallible hook-wiring patches run after wrapper restoration so a drifted
    # anchor raises here without leaving a naive publish script in the tree.
    for path, ensure, name in (
        (SDKHOOKS_PATH, ensure_init_hooks_wiring, "SDKHooks init_hooks wiring"),
        (
            HOOKS_INIT_PATH,
            ensure_hooks_package_reexport,
            "hooks package registration re-export",
        ),
    ):
        if ensure(path):
            messages.append(f"post_generate_patch: restored {name}")

    if ensure_security_empty_guard(
        GENERATED_SRC_DIR / "utils" / "security.py",
    ):
        messages.append("post_generate_patch: restored security empty-value guard")

    if ensure_duration_adapter_annotation(
        GENERATED_SRC_DIR / "utils" / "datetimes.py",
    ):
        messages.append("post_generate_patch: restored duration adapter annotation")

    for target in ensure_model_rename_aliases():
        messages.append(
            f"post_generate_patch: restored 0.26.1 rename aliases in {target}",
        )

    changed = patch_get_v2_selfop(TARGET)
    rel = TARGET.relative_to(REPO_ROOT)
    if changed:
        messages.append(f"post_generate_patch: patched {rel}")
    else:
        messages.append(f"post_generate_patch: unchanged {rel}")

    print("\n".join(messages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
