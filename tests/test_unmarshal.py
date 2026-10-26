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
    (
        "attio.errors.patch_v2_objects_object_records_record_id_op",
        "PatchV2ObjectsObjectRecordsRecordIDInvalidRequestErrorData",
    ),
    (
        "attio.errors.put_v2_objects_object_records_record_id_op",
        "PutV2ObjectsObjectRecordsRecordIDInvalidRequestErrorData",
    ),
    (
        "attio.errors.patch_v2_activities_activity_records_record_id_op",
        "PatchV2ActivitiesActivityRecordsRecordIDInvalidRequestErrorData",
    ),
    (
        "attio.errors.put_v2_activities_activity_records_record_id_op",
        "PutV2ActivitiesActivityRecordsRecordIDInvalidRequestErrorData",
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


@pytest.mark.parametrize(
    "code",
    ["duplicate_values", "limit_reached", "multiple_match_results"],
)
@pytest.mark.parametrize(
    "module_name,class_name",
    [
        (
            "attio.errors.post_v2_objects_object_recordsop",
            "PostV2ObjectsObjectRecordsInvalidRequestErrorData",
        ),
        (
            "attio.errors.put_v2_objects_object_recordsop",
            "PutV2ObjectsObjectRecordsInvalidRequestErrorData",
        ),
        (
            "attio.errors.post_v2_activities_activity_recordsop",
            "PostV2ActivitiesActivityRecordsInvalidRequestErrorData",
        ),
        (
            "attio.errors.put_v2_activities_activity_recordsop",
            "PutV2ActivitiesActivityRecordsInvalidRequestErrorData",
        ),
    ],
)
def test_records_create_upsert_invalid_request_accepts_new_spec_codes(
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


# The record_id PUT/PATCH and entries PUT/PATCH endpoints carry their 400
# code unions natively in the spec (no overlay action), so their generated
# CodeUnions must accept every member the pinned spec's anyOf carries.
UNION_CODE_MODELS = [
    (
        "attio.errors.put_v2_objects_object_records_record_id_op",
        "PutV2ObjectsObjectRecordsRecordIDInvalidRequestErrorData",
        [
            "missing_value",
            "merge_in_progress",
            "particle_gate_violation",
            "value_not_found",
            "validation_type",
            "duplicate_values",
            "limit_reached",
            "multiple_match_results",
        ],
    ),
    (
        "attio.errors.patch_v2_objects_object_records_record_id_op",
        "PatchV2ObjectsObjectRecordsRecordIDInvalidRequestErrorData",
        [
            "missing_value",
            "merge_in_progress",
            "particle_gate_violation",
            "value_not_found",
            "validation_type",
            "duplicate_values",
            "limit_reached",
            "multiple_match_results",
        ],
    ),
    (
        "attio.errors.put_v2_activities_activity_records_record_id_op",
        "PutV2ActivitiesActivityRecordsRecordIDInvalidRequestErrorData",
        [
            "missing_value",
            "particle_gate_violation",
            "value_not_found",
            "validation_type",
            "duplicate_values",
            "limit_reached",
            "multiple_match_results",
        ],
    ),
    (
        "attio.errors.patch_v2_activities_activity_records_record_id_op",
        "PatchV2ActivitiesActivityRecordsRecordIDInvalidRequestErrorData",
        [
            "missing_value",
            "particle_gate_violation",
            "value_not_found",
            "validation_type",
            "duplicate_values",
            "limit_reached",
            "multiple_match_results",
        ],
    ),
    (
        "attio.errors.put_v2_lists_list_entriesop",
        "PutV2ListsListEntriesInvalidRequestErrorData",
        ["multiple_match_results", "merge_in_progress", "validation_type"],
    ),
    (
        "attio.errors.put_v2_lists_list_entries_entry_id_op",
        "PutV2ListsListEntriesEntryIDInvalidRequestErrorData",
        ["immutable_value", "merge_in_progress", "validation_type"],
    ),
    (
        "attio.errors.patch_v2_lists_list_entries_entry_id_op",
        "PatchV2ListsListEntriesEntryIDInvalidRequestErrorData",
        ["immutable_value", "merge_in_progress", "validation_type"],
    ),
]


@pytest.mark.parametrize("module_name,class_name,codes", UNION_CODE_MODELS)
def test_record_id_and_entries_invalid_request_accepts_spec_union_codes(
    module_name: str, class_name: str, codes: list[str]
) -> None:
    module = importlib.import_module(module_name)
    model_cls = getattr(module, class_name)

    for code in codes:
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


# 400 codes the 2026-10-26 upstream spec added to the record and entry write
# endpoints. The overlay flattens the four create/upsert endpoints to single
# enums, while the {record_id} PATCH/PUT and entries PUT/PATCH endpoints carry
# the new codes natively via their anyOf unions. Pinned alongside the
# hand-applied regeneration of generated/src/attio/ so a regression that walks
# any of these Literals back fails loudly.
NEW_UPSTREAM_400_CODES = [
    (
        "attio.errors.post_v2_objects_object_recordsop",
        "PostV2ObjectsObjectRecordsInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.put_v2_objects_object_recordsop",
        "PutV2ObjectsObjectRecordsInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.post_v2_activities_activity_recordsop",
        "PostV2ActivitiesActivityRecordsInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.put_v2_activities_activity_recordsop",
        "PutV2ActivitiesActivityRecordsInvalidRequestErrorData",
        ("duplicate_values", "limit_reached"),
    ),
    (
        "attio.errors.patch_v2_objects_object_records_record_id_op",
        "PatchV2ObjectsObjectRecordsRecordIDInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.put_v2_objects_object_records_record_id_op",
        "PutV2ObjectsObjectRecordsRecordIDInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.patch_v2_activities_activity_records_record_id_op",
        "PatchV2ActivitiesActivityRecordsRecordIDInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.put_v2_activities_activity_records_record_id_op",
        "PutV2ActivitiesActivityRecordsRecordIDInvalidRequestErrorData",
        ("duplicate_values", "limit_reached", "multiple_match_results"),
    ),
    (
        "attio.errors.put_v2_lists_list_entriesop",
        "PutV2ListsListEntriesInvalidRequestErrorData",
        ("validation_type",),
    ),
    (
        "attio.errors.patch_v2_lists_list_entries_entry_id_op",
        "PatchV2ListsListEntriesEntryIDInvalidRequestErrorData",
        ("validation_type",),
    ),
    (
        "attio.errors.put_v2_lists_list_entries_entry_id_op",
        "PutV2ListsListEntriesEntryIDInvalidRequestErrorData",
        ("validation_type",),
    ),
]


@pytest.mark.parametrize(
    "module_name,class_name,codes",
    NEW_UPSTREAM_400_CODES,
    ids=[module.split(".")[-1] for module, _, _ in NEW_UPSTREAM_400_CODES],
)
def test_invalid_request_error_models_accept_new_upstream_codes(
    module_name: str, class_name: str, codes: tuple[str, ...]
) -> None:
    module = importlib.import_module(module_name)
    model_cls = getattr(module, class_name)

    for code in codes:
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
