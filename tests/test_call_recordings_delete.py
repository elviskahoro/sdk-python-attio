"""Tests for the call-recording DELETE handler's 204 success path.

Regression coverage for the bug where a successful ``204 No Content`` response
from ``DELETE /v2/meetings/{meeting_id}/call_recordings/{call_recording_id}``
was reported as an SDK error instead of returning the empty success model.

A ``204`` response carries no body (RFC 9110 sec. 15.4.5). Two legal on-the-wire
shapes exist and both must be handled:
  * no ``content-type`` header (the common case for a bodyless ``204``)
  * ``content-type: application/json`` with an empty body (a server that mirrors
    the client's ``Accept: application/json`` request header)

The success branch therefore matches on status code only and returns an empty
``DeleteV2MeetingsMeetingIDCallRecordingsCallRecordingIDResponse`` model without
attempting to unmarshal a response body that does not exist. These tests guard
against a future ``speakeasy run`` reintroducing the previously generated
``match_response(http_res, "204", "application/json")`` +
``unmarshal_json_response(...)`` pattern, which cannot succeed for a real
bodyless ``204``.
"""

import httpx
import pytest

from attio import SDK, models


MEETING_ID = "00000000-0000-0000-0000-000000000001"
CALL_RECORDING_ID = "00000000-0000-0000-0000-000000000002"

SUCCESS_MODEL = models.DeleteV2MeetingsMeetingIDCallRecordingsCallRecordingIDResponse


def _sync_sdk(handler) -> SDK:
    return SDK(
        oauth2="test-token",
        client=httpx.Client(
            transport=httpx.MockTransport(handler), follow_redirects=True
        ),
    )


def _async_sdk(handler) -> SDK:
    return SDK(
        oauth2="test-token",
        async_client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler), follow_redirects=True
        ),
    )


def _204_no_content_type(request: httpx.Request) -> httpx.Response:
    assert request.method == "DELETE"
    return httpx.Response(204, content=b"", request=request)


def _204_json_content_type_empty_body(request: httpx.Request) -> httpx.Response:
    assert request.method == "DELETE"
    return httpx.Response(
        204,
        headers={"content-type": "application/json"},
        content=b"",
        request=request,
    )


def test_delete_sync_returns_empty_model_for_bodyless_204_without_content_type():
    with _sync_sdk(_204_no_content_type) as sdk:
        res = sdk.call_recordings.delete_v2_meetings_meeting_id_call_recordings_call_recording_id_(
            meeting_id=MEETING_ID,
            call_recording_id=CALL_RECORDING_ID,
        )

    assert isinstance(res, SUCCESS_MODEL)


def test_delete_sync_returns_empty_model_for_204_with_json_content_type_and_empty_body():
    with _sync_sdk(_204_json_content_type_empty_body) as sdk:
        res = sdk.call_recordings.delete_v2_meetings_meeting_id_call_recordings_call_recording_id_(
            meeting_id=MEETING_ID,
            call_recording_id=CALL_RECORDING_ID,
        )

    assert isinstance(res, SUCCESS_MODEL)


@pytest.mark.asyncio
async def test_delete_async_returns_empty_model_for_bodyless_204_without_content_type():
    async with _async_sdk(_204_no_content_type) as sdk:
        res = await sdk.call_recordings.delete_v2_meetings_meeting_id_call_recordings_call_recording_id__async(
            meeting_id=MEETING_ID,
            call_recording_id=CALL_RECORDING_ID,
        )

    assert isinstance(res, SUCCESS_MODEL)
