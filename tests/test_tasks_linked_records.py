"""Tests for the tasks ``linked_records`` request-body serialization.

Background
----------
The upstream OpenAPI spec models a *dynamic* JSON key (the matching-attribute
slug/ID) as a literal placeholder property named ``[slug_or_id_of_matching_attribute]``.
Speakeasy faithfully generated a fixed ``pydantic.Field(alias="[slug_or_id_of_matching_attribute]")``,
so the literal placeholder (square brackets and all) was emitted verbatim as the
wire JSON key. The user's real attribute slug could never be sent, and the
documented/example shape (real slug as key, e.g. ``email_addresses``) failed
union validation entirely.

The fix removes the broken matching-attribute variant from the ``linked_records``
union (via ``overlay.yaml`` and mirrored in the generated models until the next
``speakeasy run``), so the SDK fails fast with a validation error instead of
silently emitting a placeholder-keyed body. Linking by record ID and by
email/domain string remain available.

These tests guard against the variant silently returning (via overlay drift or
a partial edit) and against the surviving linking modes regressing.
"""

import glob
import json
import os
import re

import pydantic
import pytest

from attio.models.patch_v2_tasks_task_id_op import (
    PatchV2TasksTaskIDRequestBody,
    PatchV2TasksTaskIDRequest,
)
from attio.models.post_v2_tasksop import PostV2TasksRequest
from attio.utils.serializers import marshal_json

PLACEHOLDER_KEY = "[slug_or_id_of_matching_attribute]"


def _post_request(linked_records):
    """Build a POST /v2/tasks request body the way ``Tasks.post_v2_tasks`` does."""
    return PostV2TasksRequest(
        data={
            "content": "Follow up",
            "format": "plaintext",
            "deadline_at": None,
            "is_completed": False,
            "linked_records": linked_records,
            "assignees": [],
        }
    )


def _post_body(linked_records):
    """Serialize a full POST /v2/tasks request body the way the SDK does on the wire."""
    return marshal_json(_post_request(linked_records), PostV2TasksRequest)


def _patch_request(linked_records):
    """Build a PATCH /v2/tasks/{task_id} request body the way ``Tasks.patch_v2_tasks_task_id_`` does."""
    return PatchV2TasksTaskIDRequest(
        task_id="abc123",
        request_body=PatchV2TasksTaskIDRequestBody(
            data={"linked_records": linked_records}
        ),
    )


def _patch_body(linked_records):
    """Serialize a full PATCH /v2/tasks/{task_id} request body the way the SDK does on the wire."""
    return marshal_json(_patch_request(linked_records).request_body, PatchV2TasksTaskIDRequestBody)


# ---------------------------------------------------------------------------
# The broken matching-attribute variant is rejected at validation time
# (fail-fast) instead of silently emitting a placeholder-keyed body.
# ---------------------------------------------------------------------------

def test_post_matching_attribute_variant_is_rejected() -> None:
    # Previously validated and serialized to {"...[slug_or_id_of_matching_attribute]":[...]}.
    with pytest.raises(pydantic.ValidationError):
        _post_request(
            [
                {
                    "target_object": "people",
                    "slug_or_id_of_matching_attribute": [
                        {"email_address": "alice@website.com"}
                    ],
                }
            ]
        )


def test_patch_matching_attribute_variant_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError):
        _patch_request(
            [
                {
                    "target_object": "people",
                    "slug_or_id_of_matching_attribute": [
                        {"email_address": "alice@website.com"}
                    ],
                }
            ]
        )


# ---------------------------------------------------------------------------
# The surviving variants still validate and serialize to their intended
# shapes (no regression), and never emit the placeholder key.
# ---------------------------------------------------------------------------

def test_post_by_record_id_variant_serializes_without_placeholder() -> None:
    body = _post_body([{"target_object": "people", "target_record_id": "abc123"}])
    assert PLACEHOLDER_KEY not in body
    assert json.loads(body) == {
        "data": {
            "content": "Follow up",
            "format": "plaintext",
            "deadline_at": None,
            "is_completed": False,
            "linked_records": [
                {"target_object": "people", "target_record_id": "abc123"}
            ],
            "assignees": [],
        }
    }


def test_post_by_email_domain_string_variant_serializes_without_placeholder() -> None:
    body = _post_body(["alice@website.com", "fundstack.com"])
    assert PLACEHOLDER_KEY not in body
    assert json.loads(body)["data"]["linked_records"] == [
        "alice@website.com",
        "fundstack.com",
    ]


def test_patch_by_record_id_variant_serializes_without_placeholder() -> None:
    body = _patch_body([{"target_object": "people", "target_record_id": "abc123"}])
    assert PLACEHOLDER_KEY not in body
    assert json.loads(body) == {
        "data": {
            "linked_records": [
                {"target_object": "people", "target_record_id": "abc123"}
            ]
        }
    }


# ---------------------------------------------------------------------------
# The overlay (the repo's regen-time lever) is in place and its targets
# resolve against the active OpenAPI spec, so the next ``speakeasy run``
# removes the broken variant rather than letting the live models diverge
# from the spec. Guards against the overlay action being dropped or its
# JSONPath indices drifting when the spec is updated.
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _active_spec_path() -> str:
    root = _repo_root()
    workflow = os.path.join(root, ".speakeasy", "workflow.yaml")
    if os.path.exists(workflow):
        text = open(workflow, encoding="utf-8").read()
        match = re.search(r"location:\s+openapi/(api-\d+\.json)", text)
        if match:
            return os.path.join(root, "openapi", match.group(1))
    candidates = [
        f
        for f in sorted(glob.glob(os.path.join(root, "openapi", "api-*.json")))
        if "-overlay" not in os.path.basename(f)
    ]
    if candidates:
        return candidates[-1]
    raise FileNotFoundError("No OpenAPI spec found under openapi/")


def _overlay_text() -> str:
    with open(os.path.join(_repo_root(), "overlay.yaml"), encoding="utf-8") as fh:
        return fh.read()


def _matching_attribute_variant(spec, path):
    method = "post" if path == "/v2/tasks" else "patch"
    linked_records = (
        spec["paths"][path][method]["requestBody"]["content"]["application/json"][
            "schema"
        ]["properties"]["data"]["properties"]["linked_records"]
    )
    return linked_records["anyOf"][1]["items"]["anyOf"][1]


def test_overlay_removes_broken_variant_for_post_and_patch() -> None:
    overlay = _overlay_text()
    post_target = (
        "$.paths['/v2/tasks'].post.requestBody.content['application/json']."
        "schema.properties.data.properties.linked_records.anyOf[1].items.anyOf[1]"
    )
    patch_target = (
        "$.paths['/v2/tasks/{task_id}'].patch.requestBody.content['application/json']."
        "schema.properties.data.properties.linked_records.anyOf[1].items.anyOf[1]"
    )
    assert post_target in overlay
    assert patch_target in overlay
    assert overlay.count("remove: true") >= 2


def test_overlay_targets_resolve_to_broken_variant_in_spec() -> None:
    spec = json.load(open(_active_spec_path(), encoding="utf-8"))
    for path in ("/v2/tasks", "/v2/tasks/{task_id}"):
        variant = _matching_attribute_variant(spec, path)
        assert PLACEHOLDER_KEY in variant["properties"], path
        assert PLACEHOLDER_KEY in variant["required"], path
        # The sibling by-record-ID variant is the one we keep.
        method = "post" if path == "/v2/tasks" else "patch"
        kept = (
            spec["paths"][path][method]["requestBody"]["content"]["application/json"][
                "schema"
            ]["properties"]["data"]["properties"]["linked_records"]["anyOf"][1][
                "items"
            ]["anyOf"][0]
        )
        assert kept["required"] == ["target_object", "target_record_id"], path
