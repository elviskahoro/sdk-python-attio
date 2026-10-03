import pydantic
import pytest
from pydantic import TypeAdapter

from attio.models.get_v2_selfop import AttioCom, GetV2SelfResponse, ResponseBody

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

INACTIVE_PAYLOAD = {"active": False}


def test_union_resolves_active_payload_to_attio_com():
    result = TypeAdapter(GetV2SelfResponse).validate_python(ACTIVE_PAYLOAD)
    assert isinstance(result, AttioCom)


def test_union_resolves_inactive_payload_to_response_body():
    result = TypeAdapter(GetV2SelfResponse).validate_python(INACTIVE_PAYLOAD)
    assert isinstance(result, ResponseBody)


def test_attio_com_rejects_active_false():
    with pytest.raises(pydantic.ValidationError):
        AttioCom(**{**ACTIVE_PAYLOAD, "active": False})


def test_response_body_rejects_active_true():
    with pytest.raises(pydantic.ValidationError):
        ResponseBody(active=True)
