"""The generated SDK must never import hand-written code.

tach.toml keeps ``generated/`` outside the module graph (tach is flaky with
``generated/src`` as a second source root), so this test enforces the one-way
dependency: ``attio`` may not import ``attio_cli``, ``ci`` or ``tests``.
"""

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED_PACKAGE = REPO_ROOT / "generated" / "src" / "attio"
FORBIDDEN = {"attio_cli", "ci", "tests", "scripts"}


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_generated_sdk_does_not_import_hand_written_code() -> None:
    files = sorted(GENERATED_PACKAGE.rglob("*.py"))
    assert files, f"no generated sources found under {GENERATED_PACKAGE}"

    violations = [
        f"{path.relative_to(REPO_ROOT)}: imports {sorted(roots & FORBIDDEN)}"
        for path in files
        if (roots := _imported_roots(ast.parse(path.read_text(encoding="utf-8"))))
        & FORBIDDEN
    ]

    assert not violations, "\n".join(violations)
