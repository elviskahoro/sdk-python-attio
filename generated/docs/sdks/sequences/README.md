# Sequences

## Overview

Sequences are automated email campaigns sent from Attio.

### Available Operations

* [post_v2_sequences_unsubscribed_emails](#post_v2_sequences_unsubscribed_emails) - Add emails to the unsubscribe list

## post_v2_sequences_unsubscribed_emails

Adds email addresses to the workspace's sequence unsubscribe list. Email addresses on the unsubscribe list cannot be enrolled in any sequence, and any of their active sequence runs are exited. Email addresses that are already on the unsubscribe list are ignored, so this endpoint is safe to retry.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `sequence_unsubscribe:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/sequences/unsubscribed_emails" method="post" path="/v2/sequences/unsubscribed_emails" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.sequences.post_v2_sequences_unsubscribed_emails(data={
        "email_addresses": [
            "person@example.com",
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                           | Type                                                                                                                | Required                                                                                                            | Description                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `data`                                                                                                              | [models.PostV2SequencesUnsubscribedEmailsDataRequest](../../models/postv2sequencesunsubscribedemailsdatarequest.md) | :heavy_check_mark:                                                                                                  | N/A                                                                                                                 |
| `retries`                                                                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                    | :heavy_minus_sign:                                                                                                  | Configuration to override the default retry behavior of the client.                                                 |

### Response

**[models.PostV2SequencesUnsubscribedEmailsResponse](../../models/postv2sequencesunsubscribedemailsresponse.md)**

### Errors

| Error Type                                                  | Status Code                                                 | Content Type                                                |
| ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| errors.PostV2SequencesUnsubscribedEmailsValidationTypeError | 400                                                         | application/json                                            |
| errors.SDKDefaultError                                      | 4XX, 5XX                                                    | \*/\*                                                       |