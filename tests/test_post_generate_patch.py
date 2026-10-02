"""Tests for the regeneration-safe post-generation patch (``ci/post_generate_patch.py``).

The patch re-injects the ``active`` value discriminators that ``overlay.yaml``
strips from the GET /v2/self ``anyOf``. These tests pin three properties:

* idempotence on the already-patched committed model,
* correct transformation of a freshly generated (unpatched) snapshot into the
  canonical committed state, and
* fail-fast errors when the generated layout no longer matches the anchors.

``tests/fixtures/get_v2_selfop_unpatched.txt`` is a verbatim snapshot of the
generated ``src/attio/models/get_v2_selfop.py`` immediately after a
``speakeasy run`` (commit ``0773aa5``), before the patch is applied.
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
