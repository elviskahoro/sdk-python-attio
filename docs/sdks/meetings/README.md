# Meetings

## Overview

Meetings are events synced from your calendar, added manually or added from third-party integrations.

### Available Operations

* [get_v2_meetings](#get_v2_meetings) - List meetings
* [post_v2_meetings](#post_v2_meetings) - Create a meeting
* [get_v2_meetings_meeting_id_](#get_v2_meetings_meeting_id_) - Get a meeting
* [patch_v2_meetings_meeting_id_](#patch_v2_meetings_meeting_id_) - Update a meeting (append linked records)
* [put_v2_meetings_meeting_id_](#put_v2_meetings_meeting_id_) - Update a meeting (overwrite linked records)
* [delete_v2_meetings_meeting_id_](#delete_v2_meetings_meeting_id_) - Delete a meeting

## get_v2_meetings

Lists all meetings in the workspace using a deterministic sort order. When both the `participants` and `linked_record_id` filters are supplied, they are combined with OR: meetings that match either filter are returned.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `record_permission:read`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/meetings" method="get" path="/v2/meetings" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meetings.get_v2_meetings(limit=50, participants="", sort="start_asc", timezone="UTC")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                               | Type                                                                    | Required                                                                | Description                                                             | Example                                                                 |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `limit`                                                                 | *Optional[int]*                                                         | :heavy_minus_sign:                                                      | N/A                                                                     | 50                                                                      |
| `cursor`                                                                | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `linked_object`                                                         | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `linked_record_id`                                                      | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `participants`                                                          | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `sort`                                                                  | [Optional[models.GetV2MeetingsSort]](../../models/getv2meetingssort.md) | :heavy_minus_sign:                                                      | The order in which to sort the meetings. Defaults to start_asc.         |                                                                         |
| `ends_from`                                                             | *OptionalNullable[str]*                                                 | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `starts_before`                                                         | *OptionalNullable[str]*                                                 | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `timezone`                                                              | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | N/A                                                                     |                                                                         |
| `retries`                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)        | :heavy_minus_sign:                                                      | Configuration to override the default retry behavior of the client.     |                                                                         |

### Response

**[models.GetV2MeetingsResponse](../../models/getv2meetingsresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_meetings

Creates a new meeting. [See here](/rest-api/guides/syncing-meetings) for guidance on avoiding duplicate meetings.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read-write`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/meetings" method="post" path="/v2/meetings" -->
```python
from attio import SDK
from attio.utils import parse_datetime


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meetings.post_v2_meetings(data={
        "title": "Onboarding Session",
        "description": "Getting you up to speed with the platform and answering any questions you have.",
        "start": {
            "date_": "2027-11-27",
        },
        "end": {
            "datetime_": parse_datetime("2027-11-27T15:00:00Z"),
            "timezone": "America/New_York",
        },
        "is_all_day": False,
        "participants": [],
        "linked_records": [
            {
                "object": "people",
                "record_id": "891dcbfc-9141-415d-9b2a-2238a6cc012d",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data`                                                              | [models.PostV2MeetingsData](../../models/postv2meetingsdata.md)     | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2MeetingsResponse](../../models/postv2meetingsresponse.md)**

### Errors

| Error Type                               | Status Code                              | Content Type                             |
| ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| errors.PostV2MeetingsValidationTypeError | 400                                      | application/json                         |
| errors.SDKDefaultError                   | 4XX, 5XX                                 | \*/\*                                    |

## get_v2_meetings_meeting_id_

Get a single meeting by ID.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/meetings/{meeting_id}" method="get" path="/v2/meetings/{meeting_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meetings.get_v2_meetings_meeting_id_(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `meeting_id`                                                        | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | cb59ab17-ad15-460c-a126-0715617c0853                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2MeetingsMeetingIDResponse](../../models/getv2meetingsmeetingidresponse.md)**

### Errors

| Error Type                                 | Status Code                                | Content Type                               |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------------ |
| errors.GetV2MeetingsMeetingIDNotFoundError | 404                                        | application/json                           |
| errors.SDKDefaultError                     | 4XX, 5XX                                   | \*/\*                                      |

## patch_v2_meetings_meeting_id_

Links records to a meeting. The records supplied are added to the meeting's existing linked records, and records which are already linked are ignored. Use the `PUT` endpoint to replace or remove linked records.

No other meeting fields can be updated. Attio automatically links the meeting participants' companies to the meeting; this behavior is asynchronous.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read-write`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/meetings/{meeting_id}" method="patch" path="/v2/meetings/{meeting_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meetings.patch_v2_meetings_meeting_id_(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", data={
        "linked_records": [
            {
                "object": "people",
                "record_id": "891dcbfc-9141-415d-9b2a-2238a6cc012d",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                           | Type                                                                                | Required                                                                            | Description                                                                         | Example                                                                             |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `meeting_id`                                                                        | *str*                                                                               | :heavy_check_mark:                                                                  | N/A                                                                                 | cb59ab17-ad15-460c-a126-0715617c0853                                                |
| `data`                                                                              | [models.PatchV2MeetingsMeetingIDData](../../models/patchv2meetingsmeetingiddata.md) | :heavy_check_mark:                                                                  | N/A                                                                                 |                                                                                     |
| `retries`                                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                    | :heavy_minus_sign:                                                                  | Configuration to override the default retry behavior of the client.                 |                                                                                     |

### Response

**[models.PatchV2MeetingsMeetingIDResponse](../../models/patchv2meetingsmeetingidresponse.md)**

### Errors

| Error Type                                         | Status Code                                        | Content Type                                       |
| -------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------- |
| errors.PatchV2MeetingsMeetingIDInvalidRequestError | 400                                                | application/json                                   |
| errors.PatchV2MeetingsMeetingIDNotFoundError       | 404                                                | application/json                                   |
| errors.SDKDefaultError                             | 4XX, 5XX                                           | \*/\*                                              |

## put_v2_meetings_meeting_id_

Replaces a meeting's linked records with the records supplied. Any record which is currently linked and is not in the request is unlinked, including records which Attio linked automatically from the meeting's participants. Passing an empty array unlinks every record. Use the `PATCH` endpoint to add linked records without removing the records which already exist.

No other meeting fields can be updated. Attio automatically links the meeting participants' companies to the meeting; this behavior is asynchronous, so a company which is linked after this request completes is not removed by it.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read-write`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="put_/v2/meetings/{meeting_id}" method="put" path="/v2/meetings/{meeting_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meetings.put_v2_meetings_meeting_id_(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853", data={
        "linked_records": [
            {
                "object": "people",
                "record_id": "891dcbfc-9141-415d-9b2a-2238a6cc012d",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                       | Type                                                                            | Required                                                                        | Description                                                                     | Example                                                                         |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `meeting_id`                                                                    | *str*                                                                           | :heavy_check_mark:                                                              | N/A                                                                             | cb59ab17-ad15-460c-a126-0715617c0853                                            |
| `data`                                                                          | [models.PutV2MeetingsMeetingIDData](../../models/putv2meetingsmeetingiddata.md) | :heavy_check_mark:                                                              | N/A                                                                             |                                                                                 |
| `retries`                                                                       | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                | :heavy_minus_sign:                                                              | Configuration to override the default retry behavior of the client.             |                                                                                 |

### Response

**[models.PutV2MeetingsMeetingIDResponse](../../models/putv2meetingsmeetingidresponse.md)**

### Errors

| Error Type                                       | Status Code                                      | Content Type                                     |
| ------------------------------------------------ | ------------------------------------------------ | ------------------------------------------------ |
| errors.PutV2MeetingsMeetingIDInvalidRequestError | 400                                              | application/json                                 |
| errors.PutV2MeetingsMeetingIDNotFoundError       | 404                                              | application/json                                 |
| errors.SDKDefaultError                           | 4XX, 5XX                                         | \*/\*                                            |

## delete_v2_meetings_meeting_id_

Deletes a single meeting by ID.

Meetings created by calendar sync cannot be deleted through the API. Delete the underlying calendar event, or disconnect the calendar, instead.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `meeting:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/meetings/{meeting_id}" method="delete" path="/v2/meetings/{meeting_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meetings.delete_v2_meetings_meeting_id_(meeting_id="cb59ab17-ad15-460c-a126-0715617c0853")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `meeting_id`                                                        | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | cb59ab17-ad15-460c-a126-0715617c0853                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2MeetingsMeetingIDResponse](../../models/deletev2meetingsmeetingidresponse.md)**

### Errors

| Error Type                                                  | Status Code                                                 | Content Type                                                |
| ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| errors.DeleteV2MeetingsMeetingIDSystemEditUnauthorizedError | 400                                                         | application/json                                            |
| errors.DeleteV2MeetingsMeetingIDNotFoundError               | 404                                                         | application/json                                            |
| errors.SDKDefaultError                                      | 4XX, 5XX                                                    | \*/\*                                                       |