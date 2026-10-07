"""Tests for the regeneration-safe post-generation patch (``ci/post_generate_patch.py``).

The patch re-injects the ``active`` value discriminators that ``overlay.yaml``
strips from the GET /v2/self ``anyOf``. These tests pin three properties:

* idempotence on the already-patched committed model,
* correct transformation of a freshly generated (unpatched) snapshot into the
  canonical committed state, and
* fail-fast errors when the generated layout no longer matches the anchors.

``tests/fixtures/get_v2_selfop_unpatched.txt`` is a verbatim snapshot of the
generated ``src/attio/models/get_v2_selfop.py`` immediately after a
``speakeasy run`` against the 2026-10-03 spec (which added the required
``token_level`` field), before the patch is applied. Refresh it whenever the
generated model changes: copy the committed file, strip the two
``_validate_active`` blocks and the injected blank line after each, and
revert the ``model_serializer, model_validator`` import to plain
``model_serializer``.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pydantic
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PATCH_SCRIPT = REPO_ROOT / "ci" / "post_generate_patch.py"
COMMITTED_MODEL = REPO_ROOT / "src" / "attio" / "models" / "get_v2_selfop.py"
FIXTURE_UNPATCHED = REPO_ROOT / "tests" / "fixtures" / "get_v2_selfop_unpatched.txt"

ACTIVE_PAYLOAD = {
    "active": True,
    "scope": "x",
    "client_id": "c",
    "token_type": "Bearer",
    "token_level": "workspace",  # nosec B105 - test fixture, not a credential
    "exp": None,
    "iat": 1.0,
    "sub": "s",
    "aud": "a",
    "iss": "attio.com",
    "workspace_id": "w",
    "workspace_name": "wn",
    "workspace_slug": "ws",
    "workspace_logo_url": None,
}


def _load_patch_module():
    spec = importlib.util.spec_from_file_location(
        "attio_test_post_generate_patch", PATCH_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PGP = _load_patch_module()


def _import_model_file(path: Path, module_name: str):
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_fixture_is_actually_unpatched() -> None:
    text = FIXTURE_UNPATCHED.read_text()
    assert "_validate_active" not in text
    assert "model_validator" not in text
    assert "class AttioCom(BaseModel):" in text
    assert "class ResponseBody(BaseModel):" in text


def test_committed_model_carries_the_validators() -> None:
    text = COMMITTED_MODEL.read_text()
    assert text.count("_validate_active") == 2
    assert "from pydantic import model_serializer, model_validator" in text
    assert "active must be true for AttioCom" in text
    assert "active must be false for ResponseBody" in text


def test_patch_is_noop_on_already_patched_committed_file(tmp_path: Path) -> None:
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(COMMITTED_MODEL.read_text())

    changed = PGP.patch_get_v2_selfop(target)

    assert changed is False
    assert target.read_text() == COMMITTED_MODEL.read_text()


def test_patch_applies_to_unpatched_and_matches_committed(tmp_path: Path) -> None:
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(FIXTURE_UNPATCHED.read_text())

    changed = PGP.patch_get_v2_selfop(target)

    assert changed is True
    assert target.read_text() == COMMITTED_MODEL.read_text()


def test_patch_is_idempotent_after_application(tmp_path: Path) -> None:
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(FIXTURE_UNPATCHED.read_text())

    first_changed = PGP.patch_get_v2_selfop(target)
    first_text = target.read_text()

    second_changed = PGP.patch_get_v2_selfop(target)

    assert first_changed is True
    assert second_changed is False
    assert target.read_text() == first_text


def test_project_script_is_restored_idempotently(tmp_path: Path) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text('[project]\nname = "attio"\n\n[tool.test]\n')

    assert PGP.ensure_project_script(target) is True
    assert 'gtm-attio = "attio_cli.main:main"' in target.read_text()
    assert PGP.ensure_project_script(target) is False


def test_existing_project_script_is_corrected(tmp_path: Path) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text(
        '[project.scripts]\ngtm-attio = "old.module:main"\n\n[tool.test]\n'
    )

    assert PGP.ensure_project_script(target) is True
    assert target.read_text().count("gtm-attio =") == 1
    assert 'gtm-attio = "attio_cli.main:main"' in target.read_text()


def test_readme_cli_section_is_restored_idempotently(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text(
        "## Table of Contents\n"
        "  * [SDK Installation](#sdk-installation)\n\n"
        "<!-- End SDK Installation [installation] -->\n"
        "## IDE Support\n"
    )

    assert PGP.ensure_readme_cli_section(target) is True
    content = target.read_text()
    assert "uvx gtm-attio people upsert" in content
    assert "  * [Standalone CLI](#standalone-cli)" in content
    assert PGP.ensure_readme_cli_section(target) is False


def test_existing_readme_section_is_replaced_in_place(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text(
        "## Table of Contents\n"
        "  * [SDK Installation](#sdk-installation)\n\n"
        "<!-- Start Standalone CLI [cli] -->\nold section\n"
        "<!-- End Standalone CLI [cli] -->\n"
    )

    assert PGP.ensure_readme_cli_section(target) is True
    content = target.read_text()
    assert "old section" not in content
    assert content.count(PGP.README_CLI_START) == 1
    assert "  * [Standalone CLI](#standalone-cli)" in content


def test_readme_section_without_installation_marker_is_appended(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("# SDK\n\nIntroductory content.\n")

    assert PGP.ensure_readme_cli_section(target) is True
    content = target.read_text()
    assert content.startswith("# SDK\n")
    assert content.endswith(PGP.README_CLI_SECTION + "\n")


def test_existing_readme_section_adds_missing_toc_link(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text(
        "## Table of Contents\n"
        "  * [SDK Installation](#sdk-installation)\n\n"
        + PGP.README_CLI_SECTION
    )

    assert PGP.ensure_readme_cli_section(target) is True
    assert target.read_text().count("  * [Standalone CLI](#standalone-cli)") == 1


def test_readme_cli_section_matches_regeneration_template() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    start = readme.index(PGP.README_CLI_START)
    end = readme.index(PGP.README_CLI_END, start) + len(PGP.README_CLI_END)
    assert readme[start:end] == PGP.README_CLI_SECTION


def test_patch_output_behaves_correctly(tmp_path: Path) -> None:
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(FIXTURE_UNPATCHED.read_text())

    assert PGP.patch_get_v2_selfop(target) is True

    mod = _import_model_file(target, "patched_get_v2_selfop_behavior")

    with pytest.raises(pydantic.ValidationError):
        mod.AttioCom(**{**ACTIVE_PAYLOAD, "active": False})
    with pytest.raises(pydantic.ValidationError):
        mod.ResponseBody(active=True)

    assert mod.AttioCom(**ACTIVE_PAYLOAD).active is True
    assert mod.ResponseBody(active=False).active is False


def test_patch_raises_when_attio_com_class_missing(tmp_path: Path) -> None:
    text = FIXTURE_UNPATCHED.read_text().replace(
        "class AttioCom(BaseModel):", "class AttioComRenamed(BaseModel):", 1
    )
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(text)

    with pytest.raises(RuntimeError, match="class AttioCom not found"):
        PGP.patch_get_v2_selfop(target)


def test_patch_raises_when_response_body_class_missing(tmp_path: Path) -> None:
    text = FIXTURE_UNPATCHED.read_text().replace(
        "class ResponseBody(BaseModel):", "class ResponseBodyRenamed(BaseModel):", 1
    )
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(text)

    with pytest.raises(RuntimeError, match="class ResponseBody not found"):
        PGP.patch_get_v2_selfop(target)


def test_patch_raises_when_pydantic_import_missing(tmp_path: Path) -> None:
    text = FIXTURE_UNPATCHED.read_text().replace(
        "from pydantic import model_serializer\n", "", 1
    )
    target = tmp_path / "get_v2_selfop.py"
    target.write_text(text)

    with pytest.raises(RuntimeError, match="model_serializer"):
        PGP.patch_get_v2_selfop(target)


def test_script_subprocess_is_noop_on_committed_tree() -> None:
    before = COMMITTED_MODEL.read_text()
    result = subprocess.run(
        [sys.executable, str(PATCH_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "unchanged" in result.stdout
    assert COMMITTED_MODEL.read_text() == before


# ---------------------------------------------------------------------------
# scripts/ wrapper restoration
# ---------------------------------------------------------------------------


def _stage_wrapper_tree(tmp_path: Path) -> None:
    """Create a repo-like tree with real implementations in ci/."""
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci" / "publish.sh").write_text("#!/usr/bin/env bash\ntrue\n")
    (tmp_path / "ci" / "release.sh").write_text("#!/usr/bin/env bash\ntrue\n")
    (tmp_path / "scripts").mkdir()


def _patch_wrappers_to(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PGP, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        PGP,
        "WRAPPER_IMPLS",
        {
            tmp_path / "scripts" / "publish.sh": "ci/publish.sh",
            tmp_path / "scripts" / "release.sh": "ci/release.sh",
        },
    )


def test_restore_script_wrappers_rewrites_speakeasy_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The 2026-10 regression shape: Speakeasy's naive publish template must
    be replaced by the canonical delegating wrapper."""
    _stage_wrapper_tree(tmp_path)
    _patch_wrappers_to(tmp_path, monkeypatch)
    (tmp_path / "scripts" / "publish.sh").write_text(
        "#!/usr/bin/env bash\nuv build\nuv publish --token $PYPI_TOKEN\n"
    )
    canonical_release = tmp_path / "scripts" / "release.sh"
    canonical_release.write_text(PGP._WRAPPER_TEMPLATE.format(impl="ci/release.sh"))
    canonical_release.chmod(0o755)

    restored = PGP.restore_script_wrappers()

    assert [p.name for p in restored] == ["publish.sh"]
    canonical = PGP._WRAPPER_TEMPLATE.format(impl="ci/publish.sh")
    assert (tmp_path / "scripts" / "publish.sh").read_text() == canonical
    assert (tmp_path / "scripts" / "publish.sh").stat().st_mode & 0o111


def test_restore_script_wrappers_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stage_wrapper_tree(tmp_path)
    _patch_wrappers_to(tmp_path, monkeypatch)
    for impl in ("ci/publish.sh", "ci/release.sh"):
        name = Path(impl).name
        wrapper = tmp_path / "scripts" / name
        wrapper.write_text(PGP._WRAPPER_TEMPLATE.format(impl=impl))
        wrapper.chmod(0o755)

    assert PGP.restore_script_wrappers() == []


def test_restore_script_wrappers_repairs_lost_exec_bit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The generator writes non-executable files: canonical text with a
    lost exec bit must be repaired, not skipped."""
    _stage_wrapper_tree(tmp_path)
    _patch_wrappers_to(tmp_path, monkeypatch)
    wrapper = tmp_path / "scripts" / "publish.sh"
    wrapper.write_text(PGP._WRAPPER_TEMPLATE.format(impl="ci/publish.sh"))
    wrapper.chmod(0o644)
    (tmp_path / "scripts" / "release.sh").write_text(
        PGP._WRAPPER_TEMPLATE.format(impl="ci/release.sh")
    )
    (tmp_path / "scripts" / "release.sh").chmod(0o755)

    restored = PGP.restore_script_wrappers()

    assert [p.name for p in restored] == ["publish.sh"]
    assert wrapper.stat().st_mode & 0o111


def test_restore_script_wrappers_fails_when_implementation_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stage_wrapper_tree(tmp_path)
    (tmp_path / "ci" / "publish.sh").unlink()
    _patch_wrappers_to(tmp_path, monkeypatch)
    (tmp_path / "scripts" / "publish.sh").write_text("#!/usr/bin/env bash\ntrue\n")

    with pytest.raises(RuntimeError, match="ci/publish.sh is missing"):
        PGP.restore_script_wrappers()


def test_committed_script_wrappers_are_canonical() -> None:
    """The repo's ``scripts/*.sh`` must stay byte-identical to the canonical
    wrapper template, regardless of which generation path last ran — the
    Dagger path exports only ``src/``, so this catches any drift the
    post-generation restoration never gets a chance to fix."""
    for wrapper, impl in (
        (REPO_ROOT / "scripts" / "publish.sh", "ci/publish.sh"),
        (REPO_ROOT / "scripts" / "release.sh", "ci/release.sh"),
    ):
        expected = PGP._WRAPPER_TEMPLATE.format(impl=impl)
        assert wrapper.read_text() == expected, wrapper
