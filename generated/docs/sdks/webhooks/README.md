# Webhooks

## Overview

Webhooks allow you to listen for changes to data in Attio, for example when a record is updated.

### Available Operations

* [get_v2_webhooks](#get_v2_webhooks) - List webhooks
* [post_v2_webhooks](#post_v2_webhooks) - Create a webhook
* [get_v2_webhooks_webhook_id_](#get_v2_webhooks_webhook_id_) - Get a webhook
* [patch_v2_webhooks_webhook_id_](#patch_v2_webhooks_webhook_id_) - Update a webhook
* [delete_v2_webhooks_webhook_id_](#delete_v2_webhooks_webhook_id_) - Delete a webhook

## get_v2_webhooks

Get all of the webhooks in your workspace.

Required scopes: `webhook:read`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/webhooks" method="get" path="/v2/webhooks" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.webhooks.get_v2_webhooks(limit=10, offset=5)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `limit`                                                             | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 10                                                                  |
| `offset`                                                            | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 5                                                                   |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2WebhooksResponse](../../models/getv2webhooksresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_webhooks

Create a webhook and associated subscriptions.

Each combination of target URL, event type and filter must be unique within your workspace; duplicates are rejected with a 409.

Required scopes: `webhook:read-write`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/webhooks" method="post" path="/v2/webhooks" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.webhooks.post_v2_webhooks(data={
        "target_url": "https://example.com/webhook",
        "subscriptions": [],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                     | Type                                                                          | Required                                                                      | Description                                                                   |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `data`                                                                        | [models.PostV2WebhooksDataRequest](../../models/postv2webhooksdatarequest.md) | :heavy_check_mark:                                                            | N/A                                                                           |
| `retries`                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)              | :heavy_minus_sign:                                                            | Configuration to override the default retry behavior of the client.           |

### Response

**[models.PostV2WebhooksResponse](../../models/postv2webhooksresponse.md)**

### Errors

| Error Type                                   | Status Code                                  | Content Type                                 |
| -------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| errors.PostV2WebhooksValidationTypeError     | 400                                          | application/json                             |
| errors.PostV2WebhooksUniquenessConflictError | 409                                          | application/json                             |
| errors.SDKDefaultError                       | 4XX, 5XX                                     | \*/\*                                        |

## get_v2_webhooks_webhook_id_

Get a single webhook.

Required scopes: `webhook:read`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/webhooks/{webhook_id}" method="get" path="/v2/webhooks/{webhook_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.webhooks.get_v2_webhooks_webhook_id_(webhook_id="23e42eaf-323a-41da-b5bb-fd67eebda553")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `webhook_id`                                                        | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 23e42eaf-323a-41da-b5bb-fd67eebda553                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2WebhooksWebhookIDResponse](../../models/getv2webhookswebhookidresponse.md)**

### Errors

| Error Type                                 | Status Code                                | Content Type                               |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------------ |
| errors.GetV2WebhooksWebhookIDNotFoundError | 404                                        | application/json                           |
| errors.SDKDefaultError                     | 4XX, 5XX                                   | \*/\*                                      |

## patch_v2_webhooks_webhook_id_

Update a webhook and associated subscriptions.

Each combination of target URL, event type and filter must be unique within your workspace; duplicates are rejected with a 409. Changing the target URL re-checks the webhook's existing subscriptions against the new URL.

Required scopes: `webhook:read-write`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/webhooks/{webhook_id}" method="patch" path="/v2/webhooks/{webhook_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.webhooks.patch_v2_webhooks_webhook_id_(webhook_id="23e42eaf-323a-41da-b5bb-fd67eebda553", data={
        "target_url": "https://example.com/webhook",
        "subscriptions": [
            {
                "event_type": "note.created",
                "filter_": {
                    "dollar_and": [
                        {
                            "field": "parent_object_id",
                            "operator": "equals",
                            "value": "97052eb9-e65e-443f-a297-f2d9a4a7f795",
                        },
                    ],
                },
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                         | Type                                                                                              | Required                                                                                          | Description                                                                                       | Example                                                                                           |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `webhook_id`                                                                                      | *str*                                                                                             | :heavy_check_mark:                                                                                | N/A                                                                                               | 23e42eaf-323a-41da-b5bb-fd67eebda553                                                              |
| `data`                                                                                            | [models.PatchV2WebhooksWebhookIDDataRequest](../../models/patchv2webhookswebhookiddatarequest.md) | :heavy_check_mark:                                                                                | N/A                                                                                               |                                                                                                   |
| `retries`                                                                                         | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                  | :heavy_minus_sign:                                                                                | Configuration to override the default retry behavior of the client.                               |                                                                                                   |

### Response

**[models.PatchV2WebhooksWebhookIDResponse](../../models/patchv2webhookswebhookidresponse.md)**

### Errors

| Error Type                                             | Status Code                                            | Content Type                                           |
| ------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------ |
| errors.PatchV2WebhooksWebhookIDNotFoundError           | 404                                                    | application/json                                       |
| errors.PatchV2WebhooksWebhookIDUniquenessConflictError | 409                                                    | application/json                                       |
| errors.SDKDefaultError                                 | 4XX, 5XX                                               | \*/\*                                                  |

## delete_v2_webhooks_webhook_id_

Delete a webhook by ID.

Required scopes: `webhook:read-write`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/webhooks/{webhook_id}" method="delete" path="/v2/webhooks/{webhook_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.webhooks.delete_v2_webhooks_webhook_id_(webhook_id="23e42eaf-323a-41da-b5bb-fd67eebda553")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `webhook_id`                                                        | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 23e42eaf-323a-41da-b5bb-fd67eebda553                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2WebhooksWebhookIDResponse](../../models/deletev2webhookswebhookidresponse.md)**

### Errors

| Error Type                                    | Status Code                                   | Content Type                                  |
| --------------------------------------------- | --------------------------------------------- | --------------------------------------------- |
| errors.DeleteV2WebhooksWebhookIDNotFoundError | 404                                           | application/json                              |
| errors.SDKDefaultError                        | 4XX, 5XX                                      | \*/\*                                         |