# Attributes

## Overview

Attributes model properties of objects and lists. Some attributes, such as the `name` attribute on a person, are system-defined, while others are user-defined. Attributes are one of [many types](/docs/attribute-types) such as text, location or select. See our [objects and lists guide](/docs/objects-and-lists) for more information.

### Available Operations

* [get_v2_target_identifier_attributes](#get_v2_target_identifier_attributes) - List attributes
* [post_v2_target_identifier_attributes](#post_v2_target_identifier_attributes) - Create an attribute
* [get_v2_target_identifier_attributes_attribute_](#get_v2_target_identifier_attributes_attribute_) - Get an attribute
* [patch_v2_target_identifier_attributes_attribute_](#patch_v2_target_identifier_attributes_attribute_) - Update an attribute
* [get_v2_target_identifier_attributes_attribute_options](#get_v2_target_identifier_attributes_attribute_options) - List select options
* [post_v2_target_identifier_attributes_attribute_options](#post_v2_target_identifier_attributes_attribute_options) - Create a select option
* [patch_v2_target_identifier_attributes_attribute_options_option_](#patch_v2_target_identifier_attributes_attribute_options_option_) - Update a select option
* [get_v2_target_identifier_attributes_attribute_statuses](#get_v2_target_identifier_attributes_attribute_statuses) - List statuses
* [post_v2_target_identifier_attributes_attribute_statuses](#post_v2_target_identifier_attributes_attribute_statuses) - Create a status
* [patch_v2_target_identifier_attributes_attribute_statuses_status_](#patch_v2_target_identifier_attributes_attribute_statuses_status_) - Update a status

## get_v2_target_identifier_attributes

Lists all attributes defined on a specific object or list. Attributes are returned in the order that they are sorted by in the UI.

When `target` is `objects`, the required scopes are `object_configuration:read`. When `target` is `lists`, the required scopes are `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/{target}/{identifier}/attributes" method="get" path="/v2/{target}/{identifier}/attributes" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.get_v2_target_identifier_attributes(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", limit=10, offset=5, show_archived=True)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                             | Type                                                                                                  | Required                                                                                              | Description                                                                                           | Example                                                                                               |
| ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `target`                                                                                              | [models.GetV2TargetIdentifierAttributesTarget](../../models/getv2targetidentifierattributestarget.md) | :heavy_check_mark:                                                                                    | Whether the attributes are on an object or a list.                                                    | lists                                                                                                 |
| `identifier`                                                                                          | *str*                                                                                                 | :heavy_check_mark:                                                                                    | N/A                                                                                                   | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                  |
| `limit`                                                                                               | *Optional[int]*                                                                                       | :heavy_minus_sign:                                                                                    | N/A                                                                                                   | 10                                                                                                    |
| `offset`                                                                                              | *Optional[int]*                                                                                       | :heavy_minus_sign:                                                                                    | N/A                                                                                                   | 5                                                                                                     |
| `show_archived`                                                                                       | *Optional[bool]*                                                                                      | :heavy_minus_sign:                                                                                    | N/A                                                                                                   | true                                                                                                  |
| `retries`                                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                      | :heavy_minus_sign:                                                                                    | Configuration to override the default retry behavior of the client.                                   |                                                                                                       |

### Response

**[models.GetV2TargetIdentifierAttributesResponse](../../models/getv2targetidentifierattributesresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_target_identifier_attributes

Creates a new attribute on either an object or a list.

For record-reference attributes, you can optionally create a bidirectional relationship by providing a `relationship` object. This will create two entangled attributes: one on the specified object and a reverse attribute on the related object.

To create an attribute on an object, you must also have the `object_configuration:read-write` scope.

To create an attribute on a list, you must also have the `list_configuration:read-write` scope.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/{target}/{identifier}/attributes" method="post" path="/v2/{target}/{identifier}/attributes" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.post_v2_target_identifier_attributes(target="lists", identifier="97052eb9-e65e-443f-a297-f2d9a4a7f795", data={
        "title": "Your Attribute",
        "description": "Lorem ipsum",
        "api_slug": "my-attribute",
        "type": "text",
        "is_required": True,
        "is_unique": True,
        "is_multiselect": True,
        "default_value": {
            "type": "static",
            "template": [
                {
                    "value": 5.0,
                },
            ],
        },
        "relationship": None,
        "config": {
            "currency": {
                "default_currency_code": "USD",
                "display_type": "symbol",
            },
            "record_reference": {
                "allowed_objects": [
                    "people",
                ],
            },
        },
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                               | Type                                                                                                    | Required                                                                                                | Description                                                                                             | Example                                                                                                 |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                | [models.PostV2TargetIdentifierAttributesTarget](../../models/postv2targetidentifierattributestarget.md) | :heavy_check_mark:                                                                                      | Whether the attribute is to be created on an object or a list.                                          | lists                                                                                                   |
| `identifier`                                                                                            | *str*                                                                                                   | :heavy_check_mark:                                                                                      | N/A                                                                                                     | 97052eb9-e65e-443f-a297-f2d9a4a7f795                                                                    |
| `data`                                                                                                  | [models.PostV2TargetIdentifierAttributesData](../../models/postv2targetidentifierattributesdata.md)     | :heavy_check_mark:                                                                                      | N/A                                                                                                     |                                                                                                         |
| `retries`                                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                        | :heavy_minus_sign:                                                                                      | Configuration to override the default retry behavior of the client.                                     |                                                                                                         |

### Response

**[models.PostV2TargetIdentifierAttributesResponse](../../models/postv2targetidentifierattributesresponse.md)**

### Errors

| Error Type                                                 | Status Code                                                | Content Type                                               |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| errors.PostV2TargetIdentifierAttributesValidationTypeError | 400                                                        | application/json                                           |
| errors.PostV2TargetIdentifierAttributesUnauthorizedError   | 403                                                        | application/json                                           |
| errors.PostV2TargetIdentifierAttributesNotFoundError       | 404                                                        | application/json                                           |
| errors.PostV2TargetIdentifierAttributesSlugConflictError   | 409                                                        | application/json                                           |
| errors.SDKDefaultError                                     | 4XX, 5XX                                                   | \*/\*                                                      |

## get_v2_target_identifier_attributes_attribute_

Gets information about a single attribute on either an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read`. When `target` is `lists`, the required scopes are `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/{target}/{identifier}/attributes/{attribute}" method="get" path="/v2/{target}/{identifier}/attributes/{attribute}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.get_v2_target_identifier_attributes_attribute_(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                               | Type                                                                                                                    | Required                                                                                                                | Description                                                                                                             | Example                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                | [models.GetV2TargetIdentifierAttributesAttributeTarget](../../models/getv2targetidentifierattributesattributetarget.md) | :heavy_check_mark:                                                                                                      | Whether the attribute is on an object or a list.                                                                        | lists                                                                                                                   |
| `identifier`                                                                                                            | *str*                                                                                                                   | :heavy_check_mark:                                                                                                      | N/A                                                                                                                     | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                    |
| `attribute`                                                                                                             | *str*                                                                                                                   | :heavy_check_mark:                                                                                                      | N/A                                                                                                                     | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                    |
| `retries`                                                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                        | :heavy_minus_sign:                                                                                                      | Configuration to override the default retry behavior of the client.                                                     |                                                                                                                         |

### Response

**[models.GetV2TargetIdentifierAttributesAttributeResponse](../../models/getv2targetidentifierattributesattributeresponse.md)**

### Errors

| Error Type                                                   | Status Code                                                  | Content Type                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| errors.GetV2TargetIdentifierAttributesAttributeNotFoundError | 404                                                          | application/json                                             |
| errors.SDKDefaultError                                       | 4XX, 5XX                                                     | \*/\*                                                        |

## patch_v2_target_identifier_attributes_attribute_

Updates a single attribute on a given object or list.

When `target` is `objects`, the required scopes are `object_configuration:read-write`. When `target` is `lists`, the required scopes are `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/{target}/{identifier}/attributes/{attribute}" method="patch" path="/v2/{target}/{identifier}/attributes/{attribute}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.patch_v2_target_identifier_attributes_attribute_(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", data={
        "title": "Your Attribute",
        "description": "Lorem ipsum",
        "api_slug": "my-attribute",
        "is_required": True,
        "is_unique": True,
        "default_value": {
            "type": "static",
            "template": [
                {
                    "value": 5.0,
                },
            ],
        },
        "config": {
            "currency": {
                "default_currency_code": "USD",
                "display_type": "symbol",
            },
            "record_reference": {
                "allowed_objects": [
                    "people",
                ],
            },
        },
        "is_archived": False,
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                   | Type                                                                                                                        | Required                                                                                                                    | Description                                                                                                                 | Example                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                    | [models.PatchV2TargetIdentifierAttributesAttributeTarget](../../models/patchv2targetidentifierattributesattributetarget.md) | :heavy_check_mark:                                                                                                          | Whether the attribute is on an object or a list.                                                                            | lists                                                                                                                       |
| `identifier`                                                                                                                | *str*                                                                                                                       | :heavy_check_mark:                                                                                                          | N/A                                                                                                                         | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                        |
| `attribute`                                                                                                                 | *str*                                                                                                                       | :heavy_check_mark:                                                                                                          | N/A                                                                                                                         | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                        |
| `data`                                                                                                                      | [models.PatchV2TargetIdentifierAttributesAttributeData](../../models/patchv2targetidentifierattributesattributedata.md)     | :heavy_check_mark:                                                                                                          | N/A                                                                                                                         |                                                                                                                             |
| `retries`                                                                                                                   | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                            | :heavy_minus_sign:                                                                                                          | Configuration to override the default retry behavior of the client.                                                         |                                                                                                                             |

### Response

**[models.PatchV2TargetIdentifierAttributesAttributeResponse](../../models/patchv2targetidentifierattributesattributeresponse.md)**

### Errors

| Error Type                                                                   | Status Code                                                                  | Content Type                                                                 |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| errors.PatchV2TargetIdentifierAttributesAttributeSystemEditUnauthorizedError | 400                                                                          | application/json                                                             |
| errors.PatchV2TargetIdentifierAttributesAttributeUnauthorizedError           | 403                                                                          | application/json                                                             |
| errors.PatchV2TargetIdentifierAttributesAttributeNotFoundError               | 404                                                                          | application/json                                                             |
| errors.SDKDefaultError                                                       | 4XX, 5XX                                                                     | \*/\*                                                                        |

## get_v2_target_identifier_attributes_attribute_options

Lists all select options for a particular attribute on either an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read`. When `target` is `lists`, the required scopes are `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/{target}/{identifier}/attributes/{attribute}/options" method="get" path="/v2/{target}/{identifier}/attributes/{attribute}/options" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.get_v2_target_identifier_attributes_attribute_options(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", show_archived=True)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                             | Type                                                                                                                                  | Required                                                                                                                              | Description                                                                                                                           | Example                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                              | [models.GetV2TargetIdentifierAttributesAttributeOptionsTarget](../../models/getv2targetidentifierattributesattributeoptionstarget.md) | :heavy_check_mark:                                                                                                                    | Whether the attribute is on an object or a list.                                                                                      | lists                                                                                                                                 |
| `identifier`                                                                                                                          | *str*                                                                                                                                 | :heavy_check_mark:                                                                                                                    | N/A                                                                                                                                   | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                                  |
| `attribute`                                                                                                                           | *str*                                                                                                                                 | :heavy_check_mark:                                                                                                                    | N/A                                                                                                                                   | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                                  |
| `show_archived`                                                                                                                       | *Optional[bool]*                                                                                                                      | :heavy_minus_sign:                                                                                                                    | N/A                                                                                                                                   | true                                                                                                                                  |
| `retries`                                                                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                      | :heavy_minus_sign:                                                                                                                    | Configuration to override the default retry behavior of the client.                                                                   |                                                                                                                                       |

### Response

**[models.GetV2TargetIdentifierAttributesAttributeOptionsResponse](../../models/getv2targetidentifierattributesattributeoptionsresponse.md)**

### Errors

| Error Type                                                          | Status Code                                                         | Content Type                                                        |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| errors.GetV2TargetIdentifierAttributesAttributeOptionsNotFoundError | 404                                                                 | application/json                                                    |
| errors.SDKDefaultError                                              | 4XX, 5XX                                                            | \*/\*                                                               |

## post_v2_target_identifier_attributes_attribute_options

Adds a select option to a select attribute on an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read-write`. When `target` is `lists`, the required scopes are `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/{target}/{identifier}/attributes/{attribute}/options" method="post" path="/v2/{target}/{identifier}/attributes/{attribute}/options" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.post_v2_target_identifier_attributes_attribute_options(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", data={
        "title": "Medium",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                               | Type                                                                                                                                    | Required                                                                                                                                | Description                                                                                                                             | Example                                                                                                                                 |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                                | [models.PostV2TargetIdentifierAttributesAttributeOptionsTarget](../../models/postv2targetidentifierattributesattributeoptionstarget.md) | :heavy_check_mark:                                                                                                                      | Whether the attribute is on an object or a list.                                                                                        | lists                                                                                                                                   |
| `identifier`                                                                                                                            | *str*                                                                                                                                   | :heavy_check_mark:                                                                                                                      | N/A                                                                                                                                     | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                                    |
| `attribute`                                                                                                                             | *str*                                                                                                                                   | :heavy_check_mark:                                                                                                                      | N/A                                                                                                                                     | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                                    |
| `data`                                                                                                                                  | [models.PostV2TargetIdentifierAttributesAttributeOptionsData](../../models/postv2targetidentifierattributesattributeoptionsdata.md)     | :heavy_check_mark:                                                                                                                      | N/A                                                                                                                                     |                                                                                                                                         |
| `retries`                                                                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                        | :heavy_minus_sign:                                                                                                                      | Configuration to override the default retry behavior of the client.                                                                     |                                                                                                                                         |

### Response

**[models.PostV2TargetIdentifierAttributesAttributeOptionsResponse](../../models/postv2targetidentifierattributesattributeoptionsresponse.md)**

### Errors

| Error Type                                                                 | Status Code                                                                | Content Type                                                               |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| errors.PostV2TargetIdentifierAttributesAttributeOptionsValidationTypeError | 400                                                                        | application/json                                                           |
| errors.PostV2TargetIdentifierAttributesAttributeOptionsUnauthorizedError   | 403                                                                        | application/json                                                           |
| errors.PostV2TargetIdentifierAttributesAttributeOptionsNotFoundError       | 404                                                                        | application/json                                                           |
| errors.PostV2TargetIdentifierAttributesAttributeOptionsSlugConflictError   | 409                                                                        | application/json                                                           |
| errors.SDKDefaultError                                                     | 4XX, 5XX                                                                   | \*/\*                                                                      |

## patch_v2_target_identifier_attributes_attribute_options_option_

Updates a select option on an attribute on either an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read-write`. When `target` is `lists`, the required scopes are `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/{target}/{identifier}/attributes/{attribute}/options/{option}" method="patch" path="/v2/{target}/{identifier}/attributes/{attribute}/options/{option}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.patch_v2_target_identifier_attributes_attribute_options_option_(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", option="Medium", data={
        "title": "Medium",
        "is_archived": False,
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                             | Type                                                                                                                                                  | Required                                                                                                                                              | Description                                                                                                                                           | Example                                                                                                                                               |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                                              | [models.PatchV2TargetIdentifierAttributesAttributeOptionsOptionTarget](../../models/patchv2targetidentifierattributesattributeoptionsoptiontarget.md) | :heavy_check_mark:                                                                                                                                    | Whether the attribute is on an object or a list.                                                                                                      | lists                                                                                                                                                 |
| `identifier`                                                                                                                                          | *str*                                                                                                                                                 | :heavy_check_mark:                                                                                                                                    | N/A                                                                                                                                                   | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                                                  |
| `attribute`                                                                                                                                           | *str*                                                                                                                                                 | :heavy_check_mark:                                                                                                                                    | N/A                                                                                                                                                   | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                                                  |
| `option`                                                                                                                                              | *str*                                                                                                                                                 | :heavy_check_mark:                                                                                                                                    | N/A                                                                                                                                                   | Medium                                                                                                                                                |
| `data`                                                                                                                                                | [models.PatchV2TargetIdentifierAttributesAttributeOptionsOptionData](../../models/patchv2targetidentifierattributesattributeoptionsoptiondata.md)     | :heavy_check_mark:                                                                                                                                    | N/A                                                                                                                                                   |                                                                                                                                                       |
| `retries`                                                                                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                      | :heavy_minus_sign:                                                                                                                                    | Configuration to override the default retry behavior of the client.                                                                                   |                                                                                                                                                       |

### Response

**[models.PatchV2TargetIdentifierAttributesAttributeOptionsOptionResponse](../../models/patchv2targetidentifierattributesattributeoptionsoptionresponse.md)**

### Errors

| Error Type                                                                        | Status Code                                                                       | Content Type                                                                      |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| errors.PatchV2TargetIdentifierAttributesAttributeOptionsOptionInvalidRequestError | 400                                                                               | application/json                                                                  |
| errors.PatchV2TargetIdentifierAttributesAttributeOptionsOptionUnauthorizedError   | 403                                                                               | application/json                                                                  |
| errors.PatchV2TargetIdentifierAttributesAttributeOptionsOptionNotFoundError       | 404                                                                               | application/json                                                                  |
| errors.PatchV2TargetIdentifierAttributesAttributeOptionsOptionSlugConflictError   | 409                                                                               | application/json                                                                  |
| errors.SDKDefaultError                                                            | 4XX, 5XX                                                                          | \*/\*                                                                             |

## get_v2_target_identifier_attributes_attribute_statuses

Lists all statuses for a particular status attribute on either an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read`. When `target` is `lists`, the required scopes are `list_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/{target}/{identifier}/attributes/{attribute}/statuses" method="get" path="/v2/{target}/{identifier}/attributes/{attribute}/statuses" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.get_v2_target_identifier_attributes_attribute_statuses(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", show_archived=True)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                               | Type                                                                                                                                    | Required                                                                                                                                | Description                                                                                                                             | Example                                                                                                                                 |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                                | [models.GetV2TargetIdentifierAttributesAttributeStatusesTarget](../../models/getv2targetidentifierattributesattributestatusestarget.md) | :heavy_check_mark:                                                                                                                      | Whether the attribute is on an object or a list.                                                                                        | lists                                                                                                                                   |
| `identifier`                                                                                                                            | *str*                                                                                                                                   | :heavy_check_mark:                                                                                                                      | N/A                                                                                                                                     | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                                    |
| `attribute`                                                                                                                             | *str*                                                                                                                                   | :heavy_check_mark:                                                                                                                      | N/A                                                                                                                                     | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                                    |
| `show_archived`                                                                                                                         | *Optional[bool]*                                                                                                                        | :heavy_minus_sign:                                                                                                                      | N/A                                                                                                                                     | true                                                                                                                                    |
| `retries`                                                                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                        | :heavy_minus_sign:                                                                                                                      | Configuration to override the default retry behavior of the client.                                                                     |                                                                                                                                         |

### Response

**[models.GetV2TargetIdentifierAttributesAttributeStatusesResponse](../../models/getv2targetidentifierattributesattributestatusesresponse.md)**

### Errors

| Error Type                                                           | Status Code                                                          | Content Type                                                         |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| errors.GetV2TargetIdentifierAttributesAttributeStatusesNotFoundError | 404                                                                  | application/json                                                     |
| errors.SDKDefaultError                                               | 4XX, 5XX                                                             | \*/\*                                                                |

## post_v2_target_identifier_attributes_attribute_statuses

Add a new status to a status attribute on either an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read-write`. When `target` is `lists`, the required scopes are `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/{target}/{identifier}/attributes/{attribute}/statuses" method="post" path="/v2/{target}/{identifier}/attributes/{attribute}/statuses" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.post_v2_target_identifier_attributes_attribute_statuses(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", data={
        "title": "In Progress",
        "celebration_enabled": True,
        "target_time_in_status": "P0Y0M1DT0H0M0S",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                 | Type                                                                                                                                      | Required                                                                                                                                  | Description                                                                                                                               | Example                                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                                  | [models.PostV2TargetIdentifierAttributesAttributeStatusesTarget](../../models/postv2targetidentifierattributesattributestatusestarget.md) | :heavy_check_mark:                                                                                                                        | Whether the attribute is on an object or a list.                                                                                          | lists                                                                                                                                     |
| `identifier`                                                                                                                              | *str*                                                                                                                                     | :heavy_check_mark:                                                                                                                        | N/A                                                                                                                                       | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                                      |
| `attribute`                                                                                                                               | *str*                                                                                                                                     | :heavy_check_mark:                                                                                                                        | N/A                                                                                                                                       | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                                      |
| `data`                                                                                                                                    | [models.PostV2TargetIdentifierAttributesAttributeStatusesData](../../models/postv2targetidentifierattributesattributestatusesdata.md)     | :heavy_check_mark:                                                                                                                        | N/A                                                                                                                                       |                                                                                                                                           |
| `retries`                                                                                                                                 | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                          | :heavy_minus_sign:                                                                                                                        | Configuration to override the default retry behavior of the client.                                                                       |                                                                                                                                           |

### Response

**[models.PostV2TargetIdentifierAttributesAttributeStatusesResponse](../../models/postv2targetidentifierattributesattributestatusesresponse.md)**

### Errors

| Error Type                                                                  | Status Code                                                                 | Content Type                                                                |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| errors.PostV2TargetIdentifierAttributesAttributeStatusesValidationTypeError | 400                                                                         | application/json                                                            |
| errors.PostV2TargetIdentifierAttributesAttributeStatusesUnauthorizedError   | 403                                                                         | application/json                                                            |
| errors.PostV2TargetIdentifierAttributesAttributeStatusesNotFoundError       | 404                                                                         | application/json                                                            |
| errors.PostV2TargetIdentifierAttributesAttributeStatusesSlugConflictError   | 409                                                                         | application/json                                                            |
| errors.SDKDefaultError                                                      | 4XX, 5XX                                                                    | \*/\*                                                                       |

## patch_v2_target_identifier_attributes_attribute_statuses_status_

Update a status on an status attribute on either an object or a list.

When `target` is `objects`, the required scopes are `object_configuration:read-write`. When `target` is `lists`, the required scopes are `list_configuration:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/{target}/{identifier}/attributes/{attribute}/statuses/{status}" method="patch" path="/v2/{target}/{identifier}/attributes/{attribute}/statuses/{status}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.attributes.patch_v2_target_identifier_attributes_attribute_statuses_status_(target="lists", identifier="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", attribute="41252299-f8c7-4b5e-99c9-4ff8321d2f96", status="In Progress", data={
        "title": "In Progress",
        "celebration_enabled": True,
        "target_time_in_status": "P0Y0M1DT0H0M0S",
        "is_archived": False,
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                               | Type                                                                                                                                                    | Required                                                                                                                                                | Description                                                                                                                                             | Example                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `target`                                                                                                                                                | [models.PatchV2TargetIdentifierAttributesAttributeStatusesStatusTarget](../../models/patchv2targetidentifierattributesattributestatusesstatustarget.md) | :heavy_check_mark:                                                                                                                                      | Whether the attribute is on an object or a list.                                                                                                        | lists                                                                                                                                                   |
| `identifier`                                                                                                                                            | *str*                                                                                                                                                   | :heavy_check_mark:                                                                                                                                      | N/A                                                                                                                                                     | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                                                                                                    |
| `attribute`                                                                                                                                             | *str*                                                                                                                                                   | :heavy_check_mark:                                                                                                                                      | N/A                                                                                                                                                     | 41252299-f8c7-4b5e-99c9-4ff8321d2f96                                                                                                                    |
| `status`                                                                                                                                                | *str*                                                                                                                                                   | :heavy_check_mark:                                                                                                                                      | N/A                                                                                                                                                     | In Progress                                                                                                                                             |
| `data`                                                                                                                                                  | [models.PatchV2TargetIdentifierAttributesAttributeStatusesStatusData](../../models/patchv2targetidentifierattributesattributestatusesstatusdata.md)     | :heavy_check_mark:                                                                                                                                      | N/A                                                                                                                                                     |                                                                                                                                                         |
| `retries`                                                                                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                        | :heavy_minus_sign:                                                                                                                                      | Configuration to override the default retry behavior of the client.                                                                                     |                                                                                                                                                         |

### Response

**[models.PatchV2TargetIdentifierAttributesAttributeStatusesStatusResponse](../../models/patchv2targetidentifierattributesattributestatusesstatusresponse.md)**

### Errors

| Error Type                                                                         | Status Code                                                                        | Content Type                                                                       |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| errors.PatchV2TargetIdentifierAttributesAttributeStatusesStatusInvalidRequestError | 400                                                                                | application/json                                                                   |
| errors.PatchV2TargetIdentifierAttributesAttributeStatusesStatusUnauthorizedError   | 403                                                                                | application/json                                                                   |
| errors.PatchV2TargetIdentifierAttributesAttributeStatusesStatusNotFoundError       | 404                                                                                | application/json                                                                   |
| errors.PatchV2TargetIdentifierAttributesAttributeStatusesStatusSlugConflictError   | 409                                                                                | application/json                                                                   |
| errors.SDKDefaultError                                                             | 4XX, 5XX                                                                           | \*/\*                                                                              |