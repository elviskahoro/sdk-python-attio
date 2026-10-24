# ActivityRecords

## Overview

### Available Operations

* [post_v2_activities_activity_records_query](#post_v2_activities_activity_records_query) - List activity records
* [post_v2_activities_activity_records](#post_v2_activities_activity_records) - Create an activity record
* [put_v2_activities_activity_records](#put_v2_activities_activity_records) - Upsert an activity record
* [get_v2_activities_activity_records_record_id_](#get_v2_activities_activity_records_record_id_) - Get an activity record
* [patch_v2_activities_activity_records_record_id_](#patch_v2_activities_activity_records_record_id_) - Update an activity record (append multiselect values)
* [put_v2_activities_activity_records_record_id_](#put_v2_activities_activity_records_record_id_) - Update an activity record (overwrite multiselect values)
* [delete_v2_activities_activity_records_record_id_](#delete_v2_activities_activity_records_record_id_) - Delete an activity record

## post_v2_activities_activity_records_query

Lists activity records, with the option to filter and sort results.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/activities/{activity}/records/query" method="post" path="/v2/activities/{activity}/records/query" example="Filter by attribute" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.post_v2_activities_activity_records_query(activity="phone_calls", filter_={
        "direction": "Outbound",
    }, sorts=[
        {
            "direction": "desc",
            "attribute": "timestamp",
        },
    ], limit=500.0, offset=0.0)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                           | Type                                                                                                                                                                                                | Required                                                                                                                                                                                            | Description                                                                                                                                                                                         | Example                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `activity`                                                                                                                                                                                          | *str*                                                                                                                                                                                               | :heavy_check_mark:                                                                                                                                                                                  | N/A                                                                                                                                                                                                 | phone_calls                                                                                                                                                                                         |
| `filter_`                                                                                                                                                                                           | Dict[str, *Any*]                                                                                                                                                                                    | :heavy_minus_sign:                                                                                                                                                                                  | An object used to filter results to a subset of results. Cannot be used together with `filter_view_id`. See the [full guide to filtering and sorting here](/rest-api/guides/filtering-and-sorting). | {<br/>"name": "Ada Lovelace"<br/>}                                                                                                                                                                  |
| `sorts`                                                                                                                                                                                             | List[[models.PostV2ActivitiesActivityRecordsQuerySortUnion](../../models/postv2activitiesactivityrecordsquerysortunion.md)]                                                                         | :heavy_minus_sign:                                                                                                                                                                                  | An object used to sort results. See the [full guide to filtering and sorting here](/rest-api/guides/filtering-and-sorting).                                                                         | [<br/>{<br/>"direction": "asc",<br/>"attribute": "name",<br/>"field": "last_name"<br/>}<br/>]                                                                                                       |
| `limit`                                                                                                                                                                                             | *Optional[float]*                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                  | The maximum number of results to return. Defaults to 500. See the [full guide to pagination here](/rest-api/guides/pagination).                                                                     | 500                                                                                                                                                                                                 |
| `offset`                                                                                                                                                                                            | *Optional[float]*                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                  | The number of results to skip over before returning. Defaults to 0. See the [full guide to pagination here](/rest-api/guides/pagination).                                                           | 0                                                                                                                                                                                                   |
| `retries`                                                                                                                                                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                    | :heavy_minus_sign:                                                                                                                                                                                  | Configuration to override the default retry behavior of the client.                                                                                                                                 |                                                                                                                                                                                                     |

### Response

**[models.PostV2ActivitiesActivityRecordsQueryResponse](../../models/postv2activitiesactivityrecordsqueryresponse.md)**

### Errors

| Error Type                                               | Status Code                                              | Content Type                                             |
| -------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------- |
| errors.PostV2ActivitiesActivityRecordsQueryFilterError   | 400                                                      | application/json                                         |
| errors.PostV2ActivitiesActivityRecordsQueryNotFoundError | 404                                                      | application/json                                         |
| errors.SDKDefaultError                                   | 4XX, 5XX                                                 | \*/\*                                                    |

## post_v2_activities_activity_records

Creates a new activity record, for example one specific phone call.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read-write`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/activities/{activity}/records" method="post" path="/v2/activities/{activity}/records" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.post_v2_activities_activity_records(activity="phone_calls", data={
        "values": {
            "41252299-f8c7-4b5e-99c9-4ff8321d2f96": [
                "Text value",
            ],
            "multiselect_attribute": [
                "Select option 1",
                "Select option 2",
            ],
        },
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                       | Type                                                                                                            | Required                                                                                                        | Description                                                                                                     | Example                                                                                                         |
| --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `activity`                                                                                                      | *str*                                                                                                           | :heavy_check_mark:                                                                                              | N/A                                                                                                             | phone_calls                                                                                                     |
| `data`                                                                                                          | [models.PostV2ActivitiesActivityRecordsDataRequest](../../models/postv2activitiesactivityrecordsdatarequest.md) | :heavy_check_mark:                                                                                              | N/A                                                                                                             |                                                                                                                 |
| `retries`                                                                                                       | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                | :heavy_minus_sign:                                                                                              | Configuration to override the default retry behavior of the client.                                             |                                                                                                                 |

### Response

**[models.PostV2ActivitiesActivityRecordsResponse](../../models/postv2activitiesactivityrecordsresponse.md)**

### Errors

| Error Type                                                         | Status Code                                                        | Content Type                                                       |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| errors.PostV2ActivitiesActivityRecordsInvalidRequestError          | 400                                                                | application/json                                                   |
| errors.PostV2ActivitiesActivityRecordsAuthError                    | 403                                                                | application/json                                                   |
| errors.PostV2ActivitiesActivityRecordsNotFoundError                | 404                                                                | application/json                                                   |
| errors.PostV2ActivitiesActivityRecordsConcurrentWriteConflictError | 409                                                                | application/json                                                   |
| errors.SDKDefaultError                                             | 4XX, 5XX                                                           | \*/\*                                                              |

## put_v2_activities_activity_records

Use this endpoint to create or update an activity record. A matching attribute is used to search for existing activity records. If a record is found with the same value for the matching attribute, that record will be updated. If no record with the same value for the matching attribute is found, a new record will be created instead. If you would like to avoid matching, please use the create activity record endpoint.

If the matching attribute is a multiselect attribute, new values will be added and existing values will not be deleted. For any other multiselect attribute, all values will be either created or deleted as necessary to match the list of supplied values.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read-write`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="put_/v2/activities/{activity}/records" method="put" path="/v2/activities/{activity}/records" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.put_v2_activities_activity_records(activity="phone_calls", matching_attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", data={
        "values": {
            "41252299-f8c7-4b5e-99c9-4ff8321d2f96": [
                "Text value",
            ],
            "multiselect_attribute": [
                "Select option 1",
                "Select option 2",
            ],
        },
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                     | Type                                                                                                          | Required                                                                                                      | Description                                                                                                   | Example                                                                                                       |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `activity`                                                                                                    | *str*                                                                                                         | :heavy_check_mark:                                                                                            | N/A                                                                                                           | phone_calls                                                                                                   |
| `matching_attribute`                                                                                          | *str*                                                                                                         | :heavy_check_mark:                                                                                            | N/A                                                                                                           | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                          |
| `data`                                                                                                        | [models.PutV2ActivitiesActivityRecordsDataRequest](../../models/putv2activitiesactivityrecordsdatarequest.md) | :heavy_check_mark:                                                                                            | N/A                                                                                                           |                                                                                                               |
| `retries`                                                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                              | :heavy_minus_sign:                                                                                            | Configuration to override the default retry behavior of the client.                                           |                                                                                                               |

### Response

**[models.PutV2ActivitiesActivityRecordsResponse](../../models/putv2activitiesactivityrecordsresponse.md)**

### Errors

| Error Type                                                        | Status Code                                                       | Content Type                                                      |
| ----------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| errors.PutV2ActivitiesActivityRecordsInvalidRequestError          | 400                                                               | application/json                                                  |
| errors.PutV2ActivitiesActivityRecordsAuthError                    | 403                                                               | application/json                                                  |
| errors.PutV2ActivitiesActivityRecordsNotFoundError                | 404                                                               | application/json                                                  |
| errors.PutV2ActivitiesActivityRecordsConcurrentWriteConflictError | 409                                                               | application/json                                                  |
| errors.SDKDefaultError                                            | 4XX, 5XX                                                          | \*/\*                                                             |

## get_v2_activities_activity_records_record_id_

Gets a single activity record by its `record_id`.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/activities/{activity}/records/{record_id}" method="get" path="/v2/activities/{activity}/records/{record_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.get_v2_activities_activity_records_record_id_(activity="phone_calls", record_id="5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `activity`                                                          | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | phone_calls                                                         |
| `record_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2ActivitiesActivityRecordsRecordIDResponse](../../models/getv2activitiesactivityrecordsrecordidresponse.md)**

### Errors

| Error Type                                                 | Status Code                                                | Content Type                                               |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| errors.GetV2ActivitiesActivityRecordsRecordIDNotFoundError | 404                                                        | application/json                                           |
| errors.SDKDefaultError                                     | 4XX, 5XX                                                   | \*/\*                                                      |

## patch_v2_activities_activity_records_record_id_

Use this endpoint to update activity records by `record_id`. If the update payload includes multiselect attributes, the values supplied will be created and prepended to the list of values that already exist (if any). Use the `PUT` endpoint to overwrite or remove multiselect attribute values.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read-write`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/activities/{activity}/records/{record_id}" method="patch" path="/v2/activities/{activity}/records/{record_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.patch_v2_activities_activity_records_record_id_(activity="phone_calls", record_id="5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26", data={
        "values": {
            "41252299-f8c7-4b5e-99c9-4ff8321d2f96": [
                "Text value",
            ],
            "multiselect_attribute": [
                "Select option 1",
                "Select option 2",
            ],
        },
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                         | Type                                                                                                                              | Required                                                                                                                          | Description                                                                                                                       | Example                                                                                                                           |
| --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `activity`                                                                                                                        | *str*                                                                                                                             | :heavy_check_mark:                                                                                                                | N/A                                                                                                                               | phone_calls                                                                                                                       |
| `record_id`                                                                                                                       | *str*                                                                                                                             | :heavy_check_mark:                                                                                                                | N/A                                                                                                                               | 5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26                                                                                              |
| `data`                                                                                                                            | [models.PatchV2ActivitiesActivityRecordsRecordIDDataRequest](../../models/patchv2activitiesactivityrecordsrecordiddatarequest.md) | :heavy_check_mark:                                                                                                                | N/A                                                                                                                               |                                                                                                                                   |
| `retries`                                                                                                                         | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                  | :heavy_minus_sign:                                                                                                                | Configuration to override the default retry behavior of the client.                                                               |                                                                                                                                   |

### Response

**[models.PatchV2ActivitiesActivityRecordsRecordIDResponse](../../models/patchv2activitiesactivityrecordsrecordidresponse.md)**

### Errors

| Error Type                                                                  | Status Code                                                                 | Content Type                                                                |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| errors.PatchV2ActivitiesActivityRecordsRecordIDInvalidRequestError          | 400                                                                         | application/json                                                            |
| errors.PatchV2ActivitiesActivityRecordsRecordIDUnauthorizedError            | 403                                                                         | application/json                                                            |
| errors.PatchV2ActivitiesActivityRecordsRecordIDNotFoundError                | 404                                                                         | application/json                                                            |
| errors.PatchV2ActivitiesActivityRecordsRecordIDConcurrentWriteConflictError | 409                                                                         | application/json                                                            |
| errors.SDKDefaultError                                                      | 4XX, 5XX                                                                    | \*/\*                                                                       |

## put_v2_activities_activity_records_record_id_

Use this endpoint to update activity records by `record_id`. If the update payload includes multiselect attributes, the values supplied will overwrite/remove the list of values that already exist (if any). Use the `PATCH` endpoint to append multiselect values without removing those that already exist.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read-write`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="put_/v2/activities/{activity}/records/{record_id}" method="put" path="/v2/activities/{activity}/records/{record_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.put_v2_activities_activity_records_record_id_(activity="phone_calls", record_id="5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26", data={
        "values": {
            "41252299-f8c7-4b5e-99c9-4ff8321d2f96": [
                "Text value",
            ],
            "multiselect_attribute": [
                "Select option 1",
                "Select option 2",
            ],
        },
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                     | Type                                                                                                                          | Required                                                                                                                      | Description                                                                                                                   | Example                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `activity`                                                                                                                    | *str*                                                                                                                         | :heavy_check_mark:                                                                                                            | N/A                                                                                                                           | phone_calls                                                                                                                   |
| `record_id`                                                                                                                   | *str*                                                                                                                         | :heavy_check_mark:                                                                                                            | N/A                                                                                                                           | 5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26                                                                                          |
| `data`                                                                                                                        | [models.PutV2ActivitiesActivityRecordsRecordIDDataRequest](../../models/putv2activitiesactivityrecordsrecordiddatarequest.md) | :heavy_check_mark:                                                                                                            | N/A                                                                                                                           |                                                                                                                               |
| `retries`                                                                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                              | :heavy_minus_sign:                                                                                                            | Configuration to override the default retry behavior of the client.                                                           |                                                                                                                               |

### Response

**[models.PutV2ActivitiesActivityRecordsRecordIDResponse](../../models/putv2activitiesactivityrecordsrecordidresponse.md)**

### Errors

| Error Type                                                                | Status Code                                                               | Content Type                                                              |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| errors.PutV2ActivitiesActivityRecordsRecordIDInvalidRequestError          | 400                                                                       | application/json                                                          |
| errors.PutV2ActivitiesActivityRecordsRecordIDUnauthorizedError            | 403                                                                       | application/json                                                          |
| errors.PutV2ActivitiesActivityRecordsRecordIDNotFoundError                | 404                                                                       | application/json                                                          |
| errors.PutV2ActivitiesActivityRecordsRecordIDConcurrentWriteConflictError | 409                                                                       | application/json                                                          |
| errors.SDKDefaultError                                                    | 4XX, 5XX                                                                  | \*/\*                                                                     |

## delete_v2_activities_activity_records_record_id_

Deletes a single activity record by its `record_id`.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_record:read-write`, `activity_configuration:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/activities/{activity}/records/{record_id}" method="delete" path="/v2/activities/{activity}/records/{record_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activity_records.delete_v2_activities_activity_records_record_id_(activity="phone_calls", record_id="5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `activity`                                                          | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | phone_calls                                                         |
| `record_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 5f4f2d9c-2b3e-4a83-9c76-1de3a3f14f26                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2ActivitiesActivityRecordsRecordIDResponse](../../models/deletev2activitiesactivityrecordsrecordidresponse.md)**

### Errors

| Error Type                                                        | Status Code                                                       | Content Type                                                      |
| ----------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| errors.DeleteV2ActivitiesActivityRecordsRecordIDUnauthorizedError | 403                                                               | application/json                                                  |
| errors.DeleteV2ActivitiesActivityRecordsRecordIDNotFoundError     | 404                                                               | application/json                                                  |
| errors.SDKDefaultError                                            | 4XX, 5XX                                                          | \*/\*                                                             |