# Activities

## Overview

### Available Operations

* [get_v2_activities](#get_v2_activities) - List activities
* [post_v2_activities](#post_v2_activities) - Create an activity
* [get_v2_activities_activity_](#get_v2_activities_activity_) - Get an activity
* [patch_v2_activities_activity_](#patch_v2_activities_activity_) - Update an activity
* [delete_v2_activities_activity_](#delete_v2_activities_activity_) - Delete an activity

## get_v2_activities

Lists all system-defined and user-defined activities in your workspace.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/activities" method="get" path="/v2/activities" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activities.get_v2_activities(limit=100, cursor="eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  | Example                                                                      |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `limit`                                                                      | *Optional[int]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | 100                                                                          |
| `cursor`                                                                     | *Optional[str]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |                                                                              |

### Response

**[models.GetV2ActivitiesResponse](../../models/getv2activitiesresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_activities

Creates a new custom activity in your workspace. Your workspace must have the custom activities billing feature enabled. Public apps may instead create activities with the integration activities billing feature.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/activities" method="post" path="/v2/activities" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activities.post_v2_activities(data={
        "api_slug": "site_visits",
        "singular_noun": "Site visit",
        "plural_noun": "Site visits",
        "extends": "interactions",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data`                                                              | [models.PostV2ActivitiesData](../../models/postv2activitiesdata.md) | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2ActivitiesResponse](../../models/postv2activitiesresponse.md)**

### Errors

| Error Type                               | Status Code                              | Content Type                             |
| ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| errors.PostV2ActivitiesAuthError         | 403                                      | application/json                         |
| errors.PostV2ActivitiesSlugConflictError | 409                                      | application/json                         |
| errors.SDKDefaultError                   | 4XX, 5XX                                 | \*/\*                                    |

## get_v2_activities_activity_

Gets a single activity by its `activity_id` or slug.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/activities/{activity}" method="get" path="/v2/activities/{activity}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activities.get_v2_activities_activity_(activity="phone_calls")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `activity`                                                          | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | phone_calls                                                         |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2ActivitiesActivityResponse](../../models/getv2activitiesactivityresponse.md)**

### Errors

| Error Type                                  | Status Code                                 | Content Type                                |
| ------------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| errors.GetV2ActivitiesActivityNotFoundError | 404                                         | application/json                            |
| errors.SDKDefaultError                      | 4XX, 5XX                                    | \*/\*                                       |

## patch_v2_activities_activity_

Updates a single activity by its `activity_id` or slug. The schema an activity extends is fixed after creation, so `extends` cannot be changed.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/activities/{activity}" method="patch" path="/v2/activities/{activity}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activities.patch_v2_activities_activity_(activity="phone_calls", data={
        "api_slug": "site_visits",
        "singular_noun": "Site visit",
        "plural_noun": "Site visits",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                             | Type                                                                                  | Required                                                                              | Description                                                                           | Example                                                                               |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `activity`                                                                            | *str*                                                                                 | :heavy_check_mark:                                                                    | N/A                                                                                   | phone_calls                                                                           |
| `data`                                                                                | [models.PatchV2ActivitiesActivityData](../../models/patchv2activitiesactivitydata.md) | :heavy_check_mark:                                                                    | N/A                                                                                   |                                                                                       |
| `retries`                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                      | :heavy_minus_sign:                                                                    | Configuration to override the default retry behavior of the client.                   |                                                                                       |

### Response

**[models.PatchV2ActivitiesActivityResponse](../../models/patchv2activitiesactivityresponse.md)**

### Errors

| Error Type                                          | Status Code                                         | Content Type                                        |
| --------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------- |
| errors.PatchV2ActivitiesActivityValidationTypeError | 400                                                 | application/json                                    |
| errors.PatchV2ActivitiesActivityUnauthorizedError   | 403                                                 | application/json                                    |
| errors.PatchV2ActivitiesActivityNotFoundError       | 404                                                 | application/json                                    |
| errors.PatchV2ActivitiesActivitySlugConflictError   | 409                                                 | application/json                                    |
| errors.SDKDefaultError                              | 4XX, 5XX                                            | \*/\*                                               |

## delete_v2_activities_activity_

Deletes a single activity by its `activity_id` or slug, along with all of its records. Archived activities can also be deleted.

This endpoint should be used with caution as it has the potential to remove a large amount of potentially valuable data.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `activity_configuration:read-write`, `activity_record:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/activities/{activity}" method="delete" path="/v2/activities/{activity}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.activities.delete_v2_activities_activity_(activity="phone_calls")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `activity`                                                          | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | phone_calls                                                         |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2ActivitiesActivityResponse](../../models/deletev2activitiesactivityresponse.md)**

### Errors

| Error Type                                                   | Status Code                                                  | Content Type                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| errors.DeleteV2ActivitiesActivitySystemEditUnauthorizedError | 400                                                          | application/json                                             |
| errors.DeleteV2ActivitiesActivityUnauthorizedError           | 403                                                          | application/json                                             |
| errors.DeleteV2ActivitiesActivityNotFoundError               | 404                                                          | application/json                                             |
| errors.SDKDefaultError                                       | 4XX, 5XX                                                     | \*/\*                                                        |