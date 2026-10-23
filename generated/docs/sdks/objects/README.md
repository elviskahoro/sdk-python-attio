# Objects

## Overview

Objects are the core data models inside of Attio. They contain standard objects, such as [people](/rest-api/endpoint-reference/standard-objects/people/list-person-records), [companies](/rest-api/endpoint-reference/standard-objects/companies/list-company-records) or [deals](/docs/standard-objects-deals), and custom objects that are specific to your use-case. See our [objects and lists guide](/docs/objects-and-lists) for more information.

### Available Operations

* [get_v2_objects](#get_v2_objects) - List objects
* [post_v2_objects](#post_v2_objects) - Create an object
* [get_v2_objects_object_](#get_v2_objects_object_) - Get an object
* [patch_v2_objects_object_](#patch_v2_objects_object_) - Update an object
* [delete_v2_objects_object_](#delete_v2_objects_object_) - Delete an object
* [get_v2_objects_object_views](#get_v2_objects_object_views) - List views for object

## get_v2_objects

Lists all system-defined and user-defined objects in your workspace.

Required scopes: `object_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/objects" method="get" path="/v2/objects" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects()

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.GetV2ObjectsResponse](../../models/getv2objectsresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_objects

Creates a new custom object in your workspace.

Required scopes: `object_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/objects" method="post" path="/v2/objects" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.post_v2_objects(data={
        "api_slug": "people",
        "singular_noun": "Person",
        "plural_noun": "People",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data`                                                              | [models.PostV2ObjectsData](../../models/postv2objectsdata.md)       | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2ObjectsResponse](../../models/postv2objectsresponse.md)**

### Errors

| Error Type                            | Status Code                           | Content Type                          |
| ------------------------------------- | ------------------------------------- | ------------------------------------- |
| errors.QuotaExceededError             | 400                                   | application/json                      |
| errors.PostV2ObjectsUnauthorizedError | 403                                   | application/json                      |
| errors.PostV2ObjectsSlugConflictError | 409                                   | application/json                      |
| errors.SDKDefaultError                | 4XX, 5XX                              | \*/\*                                 |

## get_v2_objects_object_

Gets a single object by its `object_id` or slug.

Required scopes: `object_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/objects/{object}" method="get" path="/v2/objects/{object}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects_object_(object="people")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `object`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | people                                                              |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2ObjectsObjectResponse](../../models/getv2objectsobjectresponse.md)**

### Errors

| Error Type                             | Status Code                            | Content Type                           |
| -------------------------------------- | -------------------------------------- | -------------------------------------- |
| errors.GetV2ObjectsObjectNotFoundError | 404                                    | application/json                       |
| errors.SDKDefaultError                 | 4XX, 5XX                               | \*/\*                                  |

## patch_v2_objects_object_

Updates a single object. The object to be updated is identified by its `object_id`.

Required scopes: `object_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/objects/{object}" method="patch" path="/v2/objects/{object}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.patch_v2_objects_object_(object="people", data={
        "api_slug": "people",
        "singular_noun": "Person",
        "plural_noun": "People",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                   | Type                                                                        | Required                                                                    | Description                                                                 | Example                                                                     |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `object`                                                                    | *str*                                                                       | :heavy_check_mark:                                                          | N/A                                                                         | people                                                                      |
| `data`                                                                      | [models.PatchV2ObjectsObjectData](../../models/patchv2objectsobjectdata.md) | :heavy_check_mark:                                                          | N/A                                                                         |                                                                             |
| `retries`                                                                   | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)            | :heavy_minus_sign:                                                          | Configuration to override the default retry behavior of the client.         |                                                                             |

### Response

**[models.PatchV2ObjectsObjectResponse](../../models/patchv2objectsobjectresponse.md)**

### Errors

| Error Type                                     | Status Code                                    | Content Type                                   |
| ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| errors.PatchV2ObjectsObjectValidationTypeError | 400                                            | application/json                               |
| errors.PatchV2ObjectsObjectUnauthorizedError   | 403                                            | application/json                               |
| errors.PatchV2ObjectsObjectNotFoundError       | 404                                            | application/json                               |
| errors.PatchV2ObjectsObjectSlugConflictError   | 409                                            | application/json                               |
| errors.SDKDefaultError                         | 4XX, 5XX                                       | \*/\*                                          |

## delete_v2_objects_object_

Deletes a single object by its `object_id` or slug, along with all of its records. Only custom objects can be deleted; system objects, such as people and companies, cannot.

This endpoint should be used with caution as it has the potential to remove a large amount of potentially valuable data.

Required scopes: `object_configuration:read-write`, `record_permission:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/objects/{object}" method="delete" path="/v2/objects/{object}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.delete_v2_objects_object_(object="people")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `object`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | people                                                              |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2ObjectsObjectResponse](../../models/deletev2objectsobjectresponse.md)**

### Errors

| Error Type                                              | Status Code                                             | Content Type                                            |
| ------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| errors.DeleteV2ObjectsObjectSystemEditUnauthorizedError | 400                                                     | application/json                                        |
| errors.DeleteV2ObjectsObjectUnauthorizedError           | 403                                                     | application/json                                        |
| errors.DeleteV2ObjectsObjectNotFoundError               | 404                                                     | application/json                                        |
| errors.SDKDefaultError                                  | 4XX, 5XX                                                | \*/\*                                                   |

## get_v2_objects_object_views

Lists saved views for an object. Results are ordered by view ID (`id.view_id` ascending).

Required scopes: `object_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/objects/{object}/views" method="get" path="/v2/objects/{object}/views" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects_object_views(object="people", show_archived=False, limit=500, cursor="eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  | Example                                                                      |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `object`                                                                     | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          | people                                                                       |
| `show_archived`                                                              | *Optional[bool]*                                                             | :heavy_minus_sign:                                                           | N/A                                                                          | false                                                                        |
| `limit`                                                                      | *Optional[int]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | 500                                                                          |
| `cursor`                                                                     | *Optional[str]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |                                                                              |

### Response

**[models.GetV2ObjectsObjectViewsResponse](../../models/getv2objectsobjectviewsresponse.md)**

### Errors

| Error Type                                  | Status Code                                 | Content Type                                |
| ------------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| errors.GetV2ObjectsObjectViewsNotFoundError | 404                                         | application/json                            |
| errors.SDKDefaultError                      | 4XX, 5XX                                    | \*/\*                                       |