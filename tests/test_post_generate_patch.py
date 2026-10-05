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
COMMITTED_INPUT_VALUE_UNION = (
    REPO_ROOT / "src" / "attio" / "models" / "input_value_union.py"
)
FIXTURE_INPUT_VALUE_UNION_UNPATCHED = (
    REPO_ROOT / "tests" / "fixtures" / "input_value_union_unpatched.txt"
)
FORBID_EXTRA_CLASSES = ("InputValue5", "InputValue6", "InputValue12")
_FORBID_EXTRA_MARKER = 'model_config = pydantic.ConfigDict(extra="forbid")'

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
    before_ivu = COMMITTED_INPUT_VALUE_UNION.read_text()
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
    assert COMMITTED_INPUT_VALUE_UNION.read_text() == before_ivu


# ---------------------------------------------------------------------------
# input_value_union.py: extra='forbid' on the all-optional InputValue variants
# ---------------------------------------------------------------------------


def test_input_value_union_fixture_is_actually_unpatched() -> None:
    """The fixture is a verbatim snapshot of the freshly generated
    ``input_value_union.py`` before the post-generation patch runs."""
    text = FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text()
    assert _FORBID_EXTRA_MARKER not in text
    assert 'extra="forbid"' not in text
    for class_name in FORBID_EXTRA_CLASSES:
        assert f"class {class_name}(BaseModel):" in text
    # The three all-optional variants must have no required fields in the
    # fixture (otherwise they wouldn't be silent catch-alls).
    for class_name, expected_field in (
        ("InputValue5", "domain"),
        ("InputValue6", "email_address"),
        ("InputValue12", "first_name"),
    ):
        assert f"{expected_field}: Optional[str] = None" in text


def test_committed_input_value_union_carries_forbid_config() -> None:
    text = COMMITTED_INPUT_VALUE_UNION.read_text()
    assert "import pydantic" in text
    assert text.count(_FORBID_EXTRA_MARKER) == len(FORBID_EXTRA_CLASSES)
    for class_name in FORBID_EXTRA_CLASSES:
        assert f"class {class_name}(BaseModel):" in text


def test_patch_input_value_union_is_noop_on_committed_file(tmp_path: Path) -> None:
    target = tmp_path / "input_value_union.py"
    target.write_text(COMMITTED_INPUT_VALUE_UNION.read_text())

    changed = PGP.patch_input_value_union(target)

    assert changed is False
    assert target.read_text() == COMMITTED_INPUT_VALUE_UNION.read_text()


def test_patch_input_value_union_applies_to_unpatched_and_matches_committed(
    tmp_path: Path,
) -> None:
    target = tmp_path / "input_value_union.py"
    target.write_text(FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text())

    changed = PGP.patch_input_value_union(target)

    assert changed is True
    assert target.read_text() == COMMITTED_INPUT_VALUE_UNION.read_text()


def test_patch_input_value_union_is_idempotent_after_application(tmp_path: Path) -> None:
    target = tmp_path / "input_value_union.py"
    target.write_text(FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text())

    first_changed = PGP.patch_input_value_union(target)
    first_text = target.read_text()

    second_changed = PGP.patch_input_value_union(target)

    assert first_changed is True
    assert second_changed is False
    assert target.read_text() == first_text


def test_patch_input_value_union_output_rejects_date_template_value(
    tmp_path: Path,
) -> None:
    """The bug: ``{"value": <date>}`` validated through ``List[
    InputValueUnion]`` silently fell through to an all-optional variant and
    serialized to ``{}``. After the patch the union raises."""
    target = tmp_path / "input_value_union.py"
    target.write_text(FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text())
    assert PGP.patch_input_value_union(target) is True

    mod = _import_model_file(target, "patched_input_value_union_reject")
    ta = pydantic.TypeAdapter(mod.InputValueUnion)
    from datetime import date

    with pytest.raises(pydantic.ValidationError):
        ta.validate_python({"value": date(2023, 1, 2)})


def test_patch_input_value_union_output_accepts_legitimate_payloads(
    tmp_path: Path,
) -> None:
    """Single-key payloads that match a real union member must still
    validate and serialize identically to the stock tree."""
    target = tmp_path / "input_value_union.py"
    target.write_text(FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text())
    assert PGP.patch_input_value_union(target) is True

    mod = _import_model_file(target, "patched_input_value_union_accept")
    ta = pydantic.TypeAdapter(mod.InputValueUnion)

    assert ta.validate_python({"domain": "x.com"}).model_dump() == {"domain": "x.com"}
    assert ta.validate_python({"email_address": "a@b.com"}).model_dump() == {
        "email_address": "a@b.com"
    }
    assert ta.validate_python(
        {"first_name": "A", "last_name": "B"}
    ).model_dump() == {"first_name": "A", "last_name": "B"}
    assert ta.validate_python({"value": "2023-01-02T13:00:00Z"}).model_dump() == {
        "value": "2023-01-02T13:00:00Z"
    }
    assert ta.validate_python({"value": 5.0}).model_dump() == {"value": 5.0}
    assert ta.validate_python({"value": True}).model_dump() == {"value": True}


def test_patch_input_value_union_output_forbids_unknown_keys_on_catchall_variants(
    tmp_path: Path,
) -> None:
    """Each all-optional variant must reject keys outside its own schema."""
    target = tmp_path / "input_value_union.py"
    target.write_text(FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text())
    assert PGP.patch_input_value_union(target) is True

    mod = _import_model_file(target, "patched_input_value_union_catchall")
    from datetime import date

    with pytest.raises(pydantic.ValidationError):
        mod.InputValue5.model_validate({"domain": "x.com", "value": date(2023, 1, 2)})
    with pytest.raises(pydantic.ValidationError):
        mod.InputValue6.model_validate({"email_address": "a@b.com", "extra": 1})
    with pytest.raises(pydantic.ValidationError):
        mod.InputValue12.model_validate({"first_name": "A", "unknown": "k"})


def test_patch_input_value_union_no_longer_emits_empty_template_item() -> None:
    """End-to-end against the committed SDK: the public attribute-create
    request model must not serialize ``"template":[{}]`` for a date-typed
    default value. The union-level error is swallowed by the
    ``OptionalNullable`` wrapper around ``default_value`` (orthogonal to
    this fix), so the offending template is dropped rather than sent as a
    corrupt empty object — strictly better than the pre-fix corruption."""
    from datetime import date

    from attio.models.post_v2_target_identifier_attributesop import (
        PostV2TargetIdentifierAttributesData,
    )

    out = PostV2TargetIdentifierAttributesData.model_validate(
        {
            "title": "t",
            "description": None,
            "api_slug": "ts",
            "type": "timestamp",
            "is_required": False,
            "is_unique": False,
            "is_multiselect": False,
            "config": {},
            "default_value": {
                "type": "static",
                "template": [{"value": date(2023, 1, 2)}],
            },
        }
    ).model_dump_json()
    assert '"template":[{}]' not in out
    assert '"template": [{}]' not in out


def test_patch_input_value_union_patch_endpoint_no_longer_emits_empty_template_item() -> None:
    """Same regression pin for the PATCH attribute endpoint, which embeds
    the same ``template: List[InputValueUnion]`` field."""
    from datetime import date

    from attio.models.patch_v2_target_identifier_attributes_attribute_op import (
        PatchV2TargetIdentifierAttributesAttributeData,
    )

    out = PatchV2TargetIdentifierAttributesAttributeData.model_validate(
        {
            "description": None,
            "is_required": False,
            "is_unique": False,
            "is_multiselect": False,
            "config": {},
            "default_value": {
                "type": "static",
                "template": [{"value": date(2023, 1, 2)}],
            },
        }
    ).model_dump_json()
    assert '"template":[{}]' not in out
    assert '"template": [{}]' not in out


def test_committed_sdk_accepts_legitimate_template_defaults() -> None:
    """Regression guard: legitimate single-key template entries continue
    to round-trip through the committed SDK for the attribute-create
    endpoint (README documents ``{"value": 5.0}`` for the numeric case)."""
    from attio.models.post_v2_target_identifier_attributesop import (
        PostV2TargetIdentifierAttributesData,
    )

    iso = PostV2TargetIdentifierAttributesData.model_validate(
        {
            "title": "t",
            "description": None,
            "api_slug": "ts",
            "type": "timestamp",
            "is_required": False,
            "is_unique": False,
            "is_multiselect": False,
            "config": {},
            "default_value": {
                "type": "static",
                "template": [{"value": "2023-01-02T13:00:00Z"}],
            },
        }
    ).model_dump_json()
    assert '"value":"2023-01-02T13:00:00Z"' in iso

    num = PostV2TargetIdentifierAttributesData.model_validate(
        {
            "title": "n",
            "description": None,
            "api_slug": "num",
            "type": "number",
            "is_required": False,
            "is_unique": False,
            "is_multiselect": False,
            "config": {},
            "default_value": {"type": "static", "template": [{"value": 5.0}]},
        }
    ).model_dump_json()
    assert '"value":5.0' in num


def test_patch_input_value_union_raises_when_class_missing(tmp_path: Path) -> None:
    text = FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text().replace(
        "class InputValue5(BaseModel):", "class InputValue5Renamed(BaseModel):", 1
    )
    target = tmp_path / "input_value_union.py"
    target.write_text(text)

    with pytest.raises(RuntimeError, match="class InputValue5 not found"):
        PGP.patch_input_value_union(target)


def test_patch_input_value_union_raises_when_pydantic_import_missing(
    tmp_path: Path,
) -> None:
    text = FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text().replace(
        "import pydantic\n", "", 1
    )
    target = tmp_path / "input_value_union.py"
    target.write_text(text)

    with pytest.raises(RuntimeError, match="import pydantic"):
        PGP.patch_input_value_union(target)


def test_patch_input_value_union_raises_on_drift_model_config_present(
    tmp_path: Path,
) -> None:
    """A future Speakeasy version that emits its own ``model_config`` on
    one of the catch-all variants must surface loudly rather than be
    silently overridden."""
    text = FIXTURE_INPUT_VALUE_UNION_UNPATCHED.read_text().replace(
        "class InputValue5(BaseModel):\n    domain:",
        'class InputValue5(BaseModel):\n    model_config = pydantic.ConfigDict(extra="ignore")\n    domain:',
        1,
    )
    target = tmp_path / "input_value_union.py"
    target.write_text(text)

    with pytest.raises(RuntimeError, match=r'model_config that is not'):
        PGP.patch_input_value_union(target)


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
