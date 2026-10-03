# Transcripts

## Overview

Transcripts contain the speech segments and speaker information for a call recording. They are linked to call recordings.

### Available Operations

* [get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript](#get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript) - Deprecated: Get call transcript

## get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript

Deprecated: prefer using `GET /v2/meetings/:meeting_id/call_recordings/:call_recording_id` to get the transcript for a call recording.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `call_recording:read`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/meetings/{meeting_id}/call_recordings/{call_recording_id}/transcript" method="get" path="/v2/meetings/{meeting_id}/call_recordings/{call_recording_id}/transcript" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.transcripts.get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", call_recording_id="e8f2a3b7-9b4d-4c5e-8a1f-3d7b2c5e8f9a", cursor="eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  | Example                                                                      |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `meeting_id`                                                                 | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          | cb59ab17-ad15-460c-a126-0715617c0853                                         |
| `call_recording_id`                                                          | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          | e8f2a3b7-9b4d-4c5e-8a1f-3d7b2c5e8f9a                                         |
| `cursor`                                                                     | *Optional[str]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |                                                                              |

### Response

**[models.GetV2MeetingsMeetingIDCallRecordingsCallRecordingIDTranscriptResponse](../../models/getv2meetingsmeetingidcallrecordingscallrecordingidtranscriptresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |