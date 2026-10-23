# Emails

## Overview

Emails are messages synced from connected mailboxes.

### Available Operations

* [get_v2_emails](#get_v2_emails) - List emails

## get_v2_emails

Lists email metadata from your workspace's connected mailboxes. Email content is never returned.

At least one of `linked_object` with `linked_record_ids`, `participants`, or `domain` must be supplied; there is no way to list every email. When several are supplied they are combined with OR: emails matching any of the filters are returned.

> **Requesting access:** this endpoint is enabled per workspace and per app while it is in alpha. Contact [support@attio.com](mailto:support@attio.com) to request access.

**Things to know**

- Filters that identify your own workspace are ignored. This covers a member's or invited member's address, one of your mailboxes, and any of their domains. If every filter you supply is ignored, an empty page is returned.
- A filter that names a protected recipient in your workspace is rejected rather than ignored. This covers an address or a domain you supply directly. A record whose address or domain is a protected recipient is ignored instead, in the same way as the filters above.
- Emails from a mailbox shared with your workspace as metadata only are returned without a subject line. An email is left out entirely when it has no participant you may see — that is, when every participant outside your workspace is a protected recipient.
- An email that reached more than one of your mailboxes is returned once, and `id.mailbox_id` identifies whichever copy was readable.
- `linked_records` is derived when you make the request rather than stored, so it reflects your records as they are now.
- Emails are returned newest first, ordered by when they were sent. Each request scans a bounded number of emails, so a page can hold fewer emails than `limit`, or none at all, while more are still available. Keep paginating for as long as a `next_cursor` is returned, rather than stopping on a short page.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `email:read`, `record_permission:read`, `object_configuration:read`.

Supported token levels: `workspace`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/emails" method="get" path="/v2/emails" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.emails.get_v2_emails(limit=25, participants="", domain="fundstack.com", exclude_automated_participants=False)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `limit`                                                             | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 25                                                                  |
| `cursor`                                                            | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `linked_object`                                                     | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `linked_record_ids`                                                 | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `participants`                                                      | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `domain`                                                            | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | fundstack.com                                                       |
| `sent_after`                                                        | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `sent_before`                                                       | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `exclude_automated_participants`                                    | *Optional[bool]*                                                    | :heavy_minus_sign:                                                  | N/A                                                                 | false                                                               |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2EmailsResponse](../../models/getv2emailsresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |