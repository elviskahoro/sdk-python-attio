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

Patch: ``pyproject.toml`` and ``README.md``

    Speakeasy owns both files, so this script also restores the standalone
    ``gtm-attio`` console entry point and its user-facing CLI documentation.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "src" / "attio" / "models" / "get_v2_selfop.py"

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

    print("\n".join(messages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
