import importlib
import json
from types import SimpleNamespace

import pytest

from attio import errors
from attio.errors.post_v2_objects_object_recordsop import (
    PostV2ObjectsObjectRecordsInvalidRequestErrorData,
)
from attio.utils.unmarshal_json_response import unmarshal_json_response


INVALID_REQUEST_MODELS = [
    (
        "attio.errors.patch_v2_target_identifier_attributes_attribute_options_option_op",
        "PatchV2TargetIdentifierAttributesAttributeOptionsOptionInvalidRequestErrorData",
    ),
    (
        "attio.errors.patch_v2_target_identifier_attributes_attribute_statuses_status_op",
        "PatchV2TargetIdentifierAttributesAttributeStatusesStatusInvalidRequestErrorData",
    ),
    (
        "attio.errors.post_v2_objects_object_recordsop",
        "PostV2ObjectsObjectRecordsInvalidRequestErrorData",
    ),
    (
        "attio.errors.post_v2_objects_records_searchop",
        "PostV2ObjectsRecordsSearchInvalidRequestErrorData",
    ),
    ("attio.errors.post_v2_listsop", "PostV2ListsInvalidRequestErrorData"),
    ("attio.errors.patch_v2_lists_list_op", "PatchV2ListsListInvalidRequestErrorData"),
    (
        "attio.errors.post_v2_lists_list_entriesop",
        "PostV2ListsListEntriesInvalidRequestErrorData",
    ),
    ("attio.errors.post_v2_commentsop", "PostV2CommentsInvalidRequestErrorData"),
    (
        "attio.errors.post_v2_activities_activity_recordsop",
        "PostV2ActivitiesActivityRecordsInvalidRequestErrorData",
    ),
    (
        "attio.errors.put_v2_activities_activity_recordsop",
        "PutV2ActivitiesActivityRecordsInvalidRequestErrorData",
    ),
]


def _mock_http_response(body: str) -> SimpleNamespace:
    return SimpleNamespace(text=body, status_code=400, headers={})


@pytest.mark.parametrize("module_name,class_name", INVALID_REQUEST_MODELS)
@pytest.mark.parametrize("code", ["value_not_found", "validation_type"])
def test_invalid_request_error_models_accept_both_codes(
    module_name: str, class_name: str, code: str
) -> None:
    module = importlib.import_module(module_name)
    model_cls = getattr(module, class_name)

    body = json.dumps(
        {
            "status_code": 400,
            "type": "invalid_request_error",
            "code": code,
            "message": f"message for {code}",
        }
    )
    http_res = _mock_http_response(body)

    parsed = unmarshal_json_response(model_cls, http_res)

    assert parsed.type == "invalid_request_error"
    assert parsed.code == code


@pytest.mark.parametrize("code", ["value_not_found", "merge_in_progress"])
def test_put_records_invalid_request_accepts_merge_codes(code: str) -> None:
    from attio.errors.put_v2_objects_object_recordsop import (
        PutV2ObjectsObjectRecordsInvalidRequestErrorData,
    )

    body = json.dumps(
        {
            "status_code": 400,
            "type": "invalid_request_error",
            "code": code,
            "message": f"message for {code}",
        }
    )
    http_res = _mock_http_response(body)

    parsed = unmarshal_json_response(
        PutV2ObjectsObjectRecordsInvalidRequestErrorData, http_res
    )

    assert parsed.type == "invalid_request_error"
    assert parsed.code == code


@pytest.mark.parametrize(
    "code",
    [
        "value_not_found",
        "matching_attribute_definition_not_unique",
        "multiple_match_results",
        "particle_gate_violation",
        "validation_type",
    ],
)
def test_put_activities_activity_records_invalid_request_accepts_upsert_codes(
    code: str,
) -> None:
    from attio.errors.put_v2_activities_activity_recordsop import (
        PutV2ActivitiesActivityRecordsInvalidRequestErrorData,
    )

    body = json.dumps(
        {
            "status_code": 400,
            "type": "invalid_request_error",
            "code": code,
            "message": f"message for {code}",
        }
    )
    http_res = _mock_http_response(body)

    parsed = unmarshal_json_response(
        PutV2ActivitiesActivityRecordsInvalidRequestErrorData, http_res
    )

    assert parsed.type == "invalid_request_error"
    assert parsed.code == code


def test_post_records_invalid_request_rejects_unknown_code() -> None:
    body = json.dumps(
        {
            "status_code": 400,
            "type": "invalid_request_error",
            "code": "uniqueness_conflict",
            "message": "unexpected code for this schema",
        }
    )
    http_res = _mock_http_response(body)

    with pytest.raises(errors.ResponseValidationError):
        unmarshal_json_response(PostV2ObjectsObjectRecordsInvalidRequestErrorData, http_res)
