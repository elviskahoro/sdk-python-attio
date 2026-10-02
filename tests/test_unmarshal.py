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


# --- Activity-record responses containing a timestamp attribute value ---
#
# The activity-record `values` field is a discriminated union keyed on
# `attribute_type`; the `"timestamp"` variant's `value` must stay `str` because
# Attio returns full UTC timestamps such as "2023-01-02T15:00:00.000000000Z".
# The overlay (overlay.yaml) strips the upstream `format: date` on the
# activity-record response paths so Speakeasy emits `value: str`. With `date`,
# pydantic raises `date_from_datetime_inexact` on any non-midnight timestamp
# (the normal server representation) and the SDK throws `ResponseValidationError`.

ACTIVITY_RECORD_RESPONSES = [
    (
        "attio.models.post_v2_activities_activity_recordsop",
        "PostV2ActivitiesActivityRecordsResponse",
        False,
    ),
    (
        "attio.models.get_v2_activities_activity_records_record_id_op",
        "GetV2ActivitiesActivityRecordsRecordIDResponse",
        False,
    ),
    (
        "attio.models.put_v2_activities_activity_records_record_id_op",
        "PutV2ActivitiesActivityRecordsRecordIDResponse",
        False,
    ),
    (
        "attio.models.patch_v2_activities_activity_records_record_id_op",
        "PatchV2ActivitiesActivityRecordsRecordIDResponse",
        False,
    ),
    (
        "attio.models.post_v2_activities_activity_records_queryop",
        "PostV2ActivitiesActivityRecordsQueryResponse",
        True,
    ),
]

ACTIVITY_RECORD_TIMESTAMP_VALUE_MODELS = [
    (
        "attio.models.post_v2_activities_activity_recordsop",
        "PostV2ActivitiesActivityRecordsValueTimestamp",
    ),
    (
        "attio.models.get_v2_activities_activity_records_record_id_op",
        "GetV2ActivitiesActivityRecordsRecordIDValueTimestamp",
    ),
    (
        "attio.models.put_v2_activities_activity_records_record_id_op",
        "PutV2ActivitiesActivityRecordsRecordIDValueTimestamp",
    ),
    (
        "attio.models.patch_v2_activities_activity_records_record_id_op",
        "PatchV2ActivitiesActivityRecordsRecordIDValueTimestamp",
    ),
    (
        "attio.models.post_v2_activities_activity_records_queryop",
        "PostV2ActivitiesActivityRecordsQueryValueTimestamp",
    ),
]

_NON_MIDNIGHT_TS = "2023-01-02T15:00:00.000000000Z"


def _activity_record_response_body(timestamp_value: str, as_list: bool) -> dict:
    record = {
        "id": {"workspace_id": "ws", "activity_id": "act", "record_id": "rec"},
        "created_at": "2023-01-02T15:00:00.000000000Z",
        "values": {
            "meeting_time": [
                {
                    "active_from": "2023-01-02T15:00:00.000000000Z",
                    "active_until": None,
                    "created_by_actor": {"type": "system"},
                    "attribute_type": "timestamp",
                    "value": timestamp_value,
                }
            ]
        },
    }
    return {"data": [record] if as_list else record}


def _mock_http_response_200(body: str) -> SimpleNamespace:
    return SimpleNamespace(text=body, status_code=200, headers={})


@pytest.mark.parametrize("module_name,class_name,as_list", ACTIVITY_RECORD_RESPONSES)
def test_activity_record_response_deserializes_non_midnight_timestamp(
    module_name: str, class_name: str, as_list: bool
) -> None:
    module = importlib.import_module(module_name)
    response_cls = getattr(module, class_name)

    body = json.dumps(_activity_record_response_body(_NON_MIDNIGHT_TS, as_list))
    http_res = _mock_http_response_200(body)

    parsed = unmarshal_json_response(response_cls, http_res)
    record = parsed.data[0] if as_list else parsed.data
    value = record.values["meeting_time"][0]

    assert value.attribute_type == "timestamp"
    assert value.value == _NON_MIDNIGHT_TS


@pytest.mark.parametrize("module_name,class_name", ACTIVITY_RECORD_TIMESTAMP_VALUE_MODELS)
def test_activity_record_timestamp_value_is_str(
    module_name: str, class_name: str
) -> None:
    module = importlib.import_module(module_name)
    value_cls = getattr(module, class_name)

    # Direct regression guard: the overlay must make Speakeasy emit `value: str`,
    # not `date`. With `date`, a non-midnight timestamp raises `date_from_datetime_inexact`.
    assert value_cls.model_fields["value"].annotation is str
