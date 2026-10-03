# CallRecordings

## Overview

Call recordings store video, audio, transcript and speaker information for calls. They are linked to meetings.

### Available Operations

* [get_v2_meetings_meeting_id_call_recordings](#get_v2_meetings_meeting_id_call_recordings) - List call recordings
* [post_v2_meetings_meeting_id_call_recordings](#post_v2_meetings_meeting_id_call_recordings) - Create call recording
* [get_v2_meetings_meeting_id_call_recordings_call_recording_id_](#get_v2_meetings_meeting_id_call_recordings_call_recording_id_) - Get call recording
* [delete_v2_meetings_meeting_id_call_recordings_call_recording_id_](#delete_v2_meetings_meeting_id_call_recordings_call_recording_id_) - Delete call recording

## get_v2_meetings_meeting_id_call_recordings

List all call recordings for a meeting.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `call_recording:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/meetings/{meeting_id}/call_recordings" method="get" path="/v2/meetings/{meeting_id}/call_recordings" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.call_recordings.get_v2_meetings_meeting_id_call_recordings(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", limit=50, cursor="eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  | Example                                                                      |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `meeting_id`                                                                 | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          | cb59ab17-ad15-460c-a126-0715617c0853                                         |
| `limit`                                                                      | *Optional[int]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | 50                                                                           |
| `cursor`                                                                     | *Optional[str]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |                                                                              |

### Response

**[models.GetV2MeetingsMeetingIDCallRecordingsResponse](../../models/getv2meetingsmeetingidcallrecordingsresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_meetings_meeting_id_call_recordings

Create a call recording for a meeting. This endpoint is rate limited to 1 request per second.

A `transcript` should always be provided — it is technically optional for backwards compatibility, but a call recording created without one will be missing summaries and other transcript-derived features. `video_url` is optional, and a transcript-only call recording (with no video) is fully supported.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `call_recording:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/meetings/{meeting_id}/call_recordings" method="post" path="/v2/meetings/{meeting_id}/call_recordings" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.call_recordings.post_v2_meetings_meeting_id_call_recordings(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", data={
        "video_url": "https://example.com/recording.mp4",
        "transcript": [
            {
                "speech": "Hello everyone, welcome to the meeting.",
                "start_time": 0.5123,
                "end_time": 3.2123,
                "speaker": {
                    "name": "Simon Mitchell",
                    "email_address": "person@company.com",
                },
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                   | Type                                                                                                                        | Required                                                                                                                    | Description                                                                                                                 | Example                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `meeting_id`                                                                                                                | *str*                                                                                                                       | :heavy_check_mark:                                                                                                          | N/A                                                                                                                         | cb59ab17-ad15-460c-a126-0715617c0853                                                                                        |
| `data`                                                                                                                      | [models.PostV2MeetingsMeetingIDCallRecordingsDataRequest](../../models/postv2meetingsmeetingidcallrecordingsdatarequest.md) | :heavy_check_mark:                                                                                                          | N/A                                                                                                                         |                                                                                                                             |
| `retries`                                                                                                                   | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                            | :heavy_minus_sign:                                                                                                          | Configuration to override the default retry behavior of the client.                                                         |                                                                                                                             |

### Response

**[models.PostV2MeetingsMeetingIDCallRecordingsResponse](../../models/postv2meetingsmeetingidcallrecordingsresponse.md)**

### Errors

| Error Type                                                      | Status Code                                                     | Content Type                                                    |
| --------------------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------- |
| errors.PostV2MeetingsMeetingIDCallRecordingsValidationTypeError | 400                                                             | application/json                                                |
| errors.PostV2MeetingsMeetingIDCallRecordingsAuthError           | 403                                                             | application/json                                                |
| errors.PostV2MeetingsMeetingIDCallRecordingsNotFoundError       | 404                                                             | application/json                                                |
| errors.SDKDefaultError                                          | 4XX, 5XX                                                        | \*/\*                                                           |

## get_v2_meetings_meeting_id_call_recordings_call_recording_id_

Get a single call recording by ID.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `call_recording:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/meetings/{meeting_id}/call_recordings/{call_recording_id}" method="get" path="/v2/meetings/{meeting_id}/call_recordings/{call_recording_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.call_recordings.get_v2_meetings_meeting_id_call_recordings_call_recording_id_(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", call_recording_id="e8f2a3b7-9b4d-4c5e-8a1f-3d7b2c5e8f9a")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `meeting_id`                                                        | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | cb59ab17-ad15-460c-a126-0715617c0853                                |
| `call_recording_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | e8f2a3b7-9b4d-4c5e-8a1f-3d7b2c5e8f9a                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2MeetingsMeetingIDCallRecordingsCallRecordingIDResponse](../../models/getv2meetingsmeetingidcallrecordingscallrecordingidresponse.md)**

### Errors

| Error Type                                                              | Status Code                                                             | Content Type                                                            |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| errors.GetV2MeetingsMeetingIDCallRecordingsCallRecordingIDNotFoundError | 404                                                                     | application/json                                                        |
| errors.SDKDefaultError                                                  | 4XX, 5XX                                                                | \*/\*                                                                   |

## delete_v2_meetings_meeting_id_call_recordings_call_recording_id_

Deletes the specified call recording. This will remove the call recording and all associated data.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `call_recording:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/meetings/{meeting_id}/call_recordings/{call_recording_id}" method="delete" path="/v2/meetings/{meeting_id}/call_recordings/{call_recording_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.call_recordings.delete_v2_meetings_meeting_id_call_recordings_call_recording_id_(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", call_recording_id="e8f2a3b7-9b4d-4c5e-8a1f-3d7b2c5e8f9a")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `meeting_id`                                                        | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | cb59ab17-ad15-460c-a126-0715617c0853                                |
| `call_recording_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | e8f2a3b7-9b4d-4c5e-8a1f-3d7b2c5e8f9a                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2MeetingsMeetingIDCallRecordingsCallRecordingIDResponse](../../models/deletev2meetingsmeetingidcallrecordingscallrecordingidresponse.md)**

### Errors

| Error Type                                                                 | Status Code                                                                | Content Type                                                               |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| errors.DeleteV2MeetingsMeetingIDCallRecordingsCallRecordingIDNotFoundError | 404                                                                        | application/json                                                           |
| errors.SDKDefaultError                                                     | 4XX, 5XX                                                                   | \*/\*                                                                      |