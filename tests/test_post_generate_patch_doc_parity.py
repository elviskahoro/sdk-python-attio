"""Keep regeneration guidance aligned with post-generation patch targets."""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PATCH_SCRIPT = REPO_ROOT / "ci" / "post_generate_patch.py"
DOCUMENTATION_FILES = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / ".agents" / "skills" / "update-sdk" / "SKILL.md",
    REPO_ROOT / ".github" / "workflows" / "spec-update-check.yml",
)


def _patch_targets() -> set[str]:
    source = PATCH_SCRIPT.read_text(encoding="utf-8")
    module_docstring = ast.get_docstring(ast.parse(source))
    assert module_docstring is not None

    headings = re.findall(r"^Patch: (.+)$", module_docstring, re.MULTILINE)
    assert headings, "post_generate_patch.py must document its patch targets"

    targets: set[str] = set()
    for heading in headings:
        heading_targets = re.findall(r"``([^`]+)``", heading)
        assert heading_targets, f"patch heading has no backticked target: {heading}"
        targets.update(heading_targets)
    return targets


def test_regeneration_docs_cover_every_post_generation_patch_target() -> None:
    targets = _patch_targets()

    for path in DOCUMENTATION_FILES:
        documentation = path.read_text(encoding="utf-8")
        missing = sorted(target for target in targets if target not in documentation)
        assert not missing, f"{path.relative_to(REPO_ROOT)} omits patch targets: {missing}"
