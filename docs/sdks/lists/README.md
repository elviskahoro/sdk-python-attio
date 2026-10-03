# Lists

## Overview

Lists are used to model a particular process. A list contains many records of a single object type, where each record is represented by an entry. Entries contain their own data from attributes defined on the list and also data from their parent record. See our [objects and lists guide](/docs/objects-and-lists) for more information.

### Available Operations

* [get_v2_lists](#get_v2_lists) - List all lists
* [post_v2_lists](#post_v2_lists) - Create a list
* [get_v2_lists_list_](#get_v2_lists_list_) - Get a list
* [patch_v2_lists_list_](#patch_v2_lists_list_) - Update a list
* [get_v2_lists_list_views](#get_v2_lists_list_views) - List views for list

## get_v2_lists

List all lists that your access token has access to. lists are returned in the order that they are sorted in the sidebar.

Required scopes: `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/lists" method="get" path="/v2/lists" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.lists.get_v2_lists()

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.GetV2ListsResponse](../../models/getv2listsresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_lists

Creates a new list.

Once you have your list, add attributes to it using the [Create attribute](/rest-api/endpoint-reference/attributes/create-an-attribute) API, and add records to it using the [Add records to list](/rest-api/endpoint-reference/entries/create-an-entry-add-record-to-list) API. 

New lists must specify which records can be added with the `parent_object` parameter which accepts either an object slug or an object ID. Permissions for the list are controlled with the `workspace_access` and `workspace_member_access` parameters.

Please note that new lists must have either `workspace_access` set to `"full-access"` or one or more element of `workspace_member_access` with a `"full-access"` level. It is also possible to receive a `403` billing error if your workspace is not on a plan that supports either advanced workspace or workspace member-level access for lists.

Required scopes: `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/lists" method="post" path="/v2/lists" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.lists.post_v2_lists(data={
        "name": "Enterprise Sales",
        "api_slug": "enterprise_sales",
        "parent_object": "people",
        "workspace_access": "read-and-write",
        "workspace_member_access": [
            {
                "workspace_member_id": "50cf242c-7fa3-4cad-87d0-75b1af71c57b",
                "level": "read-and-write",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data`                                                              | [models.PostV2ListsData](../../models/postv2listsdata.md)           | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2ListsResponse](../../models/postv2listsresponse.md)**

### Errors

| Error Type                            | Status Code                           | Content Type                          |
| ------------------------------------- | ------------------------------------- | ------------------------------------- |
| errors.PostV2ListsInvalidRequestError | 400                                   | application/json                      |
| errors.BillingError                   | 403                                   | application/json                      |
| errors.PostV2ListsNotFoundError       | 404                                   | application/json                      |
| errors.PostV2ListsSlugConflictError   | 409                                   | application/json                      |
| errors.SDKDefaultError                | 4XX, 5XX                              | \*/\*                                 |

## get_v2_lists_list_

Gets a single list in your workspace that your access token has access to.

Required scopes: `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/lists/{list}" method="get" path="/v2/lists/{list}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.lists.get_v2_lists_list_(list_id="33ebdbe9-e529-47c9-b894-0ba25e9c15c0")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `list_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2ListsListResponse](../../models/getv2listslistresponse.md)**

### Errors

| Error Type                         | Status Code                        | Content Type                       |
| ---------------------------------- | ---------------------------------- | ---------------------------------- |
| errors.GetV2ListsListNotFoundError | 404                                | application/json                   |
| errors.SDKDefaultError             | 4XX, 5XX                           | \*/\*                              |

## patch_v2_lists_list_

Updates an existing list. Permissions for the list are controlled with the `workspace_access` and `workspace_member_access` parameters. Please note that lists must have either `workspace_access` set to `"full-access"` or one or more element of `workspace_member_access` with a `"full-access"` level. It is also possible to receive a `403` billing error if your workspace is not on a plan that supports either advanced workspace or workspace member level access for lists. Changing the parent object of a list is not possible through the API as it can have unintended side-effects that should be considered carefully. If you wish to carry out a parent object change you should do so through the UI.

Required scopes: `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/lists/{list}" method="patch" path="/v2/lists/{list}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.lists.patch_v2_lists_list_(list_id="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", data={
        "name": "Enterprise Sales",
        "api_slug": "enterprise_sales",
        "workspace_access": "read-and-write",
        "workspace_member_access": [
            {
                "workspace_member_id": "50cf242c-7fa3-4cad-87d0-75b1af71c57b",
                "level": "read-and-write",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `list_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                |
| `data`                                                              | [models.PatchV2ListsListData](../../models/patchv2listslistdata.md) | :heavy_check_mark:                                                  | N/A                                                                 |                                                                     |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.PatchV2ListsListResponse](../../models/patchv2listslistresponse.md)**

### Errors

| Error Type                                 | Status Code                                | Content Type                               |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------------ |
| errors.PatchV2ListsListInvalidRequestError | 400                                        | application/json                           |
| errors.PatchV2ListsListNotFoundError       | 404                                        | application/json                           |
| errors.SDKDefaultError                     | 4XX, 5XX                                   | \*/\*                                      |

## get_v2_lists_list_views

Lists saved views for a list. Results are ordered by view ID (`id.view_id` ascending).

Required scopes: `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/lists/{list}/views" method="get" path="/v2/lists/{list}/views" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.lists.get_v2_lists_list_views(list_id="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", show_archived=False, limit=500, cursor="eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  | Example                                                                      |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `list_id`                                                                    | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                         |
| `show_archived`                                                              | *Optional[bool]*                                                             | :heavy_minus_sign:                                                           | N/A                                                                          | false                                                                        |
| `limit`                                                                      | *Optional[int]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | 500                                                                          |
| `cursor`                                                                     | *Optional[str]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |                                                                              |

### Response

**[models.GetV2ListsListViewsResponse](../../models/getv2listslistviewsresponse.md)**

### Errors

| Error Type                              | Status Code                             | Content Type                            |
| --------------------------------------- | --------------------------------------- | --------------------------------------- |
| errors.GetV2ListsListViewsNotFoundError | 404                                     | application/json                        |
| errors.SDKDefaultError                  | 4XX, 5XX                                | \*/\*                                   |