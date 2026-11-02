# WorkspaceBlocklist

## Overview

An address is an email address (jane@acme.com) or a domain (acme.com). The workspace blocklist is the workspace-wide list of addresses whose emails and calendar events are hidden in Attio. An email address matches only itself, and a domain matches every email address at that domain. The address itself is the key: there is no separate ID.

### Available Operations

* [put_v2_workspace_blocklist_addresses](#put_v2_workspace_blocklist_addresses) - Add or update workspace blocklist addresses
* [delete_v2_workspace_blocklist_addresses_address_](#delete_v2_workspace_blocklist_addresses_address_) - Delete a workspace blocklist address

## put_v2_workspace_blocklist_addresses

An address is an email address (jane@acme.com) or a domain (acme.com).

Sets each address in the request to the given enforcement level on the workspace blocklist. The address itself is its key: there is no separate ID.

An address that isn't on the workspace blocklist is added. An address already at the requested level is left unchanged, so this endpoint is safe to retry. An address at the other level is moved to the requested level.

This endpoint only adds and updates the addresses in the request. Addresses on the workspace blocklist that aren't in the request are left alone; it never replaces the whole list.

Addresses are normalized: email addresses and domains are trimmed and lowercased, a URL is reduced to its hostname, and a leading `www.` is removed. The response returns the normalized value, which is the key for the address. Duplicate addresses are collapsed, and a request that gives the same address two different enforcement levels is rejected.

The request is applied all or nothing. Protected changes take effect immediately. Blocked changes take effect once each connected mailbox has re-synced, which may take a few minutes.

A user-level access token can only call this endpoint if the workspace member it acts for is a workspace admin.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `email_calendar_blocklist:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="put_/v2/workspace_blocklist_addresses" method="put" path="/v2/workspace_blocklist_addresses" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.workspace_blocklist.put_v2_workspace_blocklist_addresses(data={
        "addresses": [
            {
                "address": "lists@acme.com",
                "enforcement_level": "blocked",
            },
            {
                "address": "https://www.newsletter.example.com",
                "enforcement_level": "blocked",
            },
            {
                "address": "jane@acme.com",
                "enforcement_level": "protected",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                         | Type                                                                                                              | Required                                                                                                          | Description                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `data`                                                                                                            | [models.PutV2WorkspaceBlocklistAddressesDataRequest](../../models/putv2workspaceblocklistaddressesdatarequest.md) | :heavy_check_mark:                                                                                                | N/A                                                                                                               |
| `retries`                                                                                                         | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                  | :heavy_minus_sign:                                                                                                | Configuration to override the default retry behavior of the client.                                               |

### Response

**[models.PutV2WorkspaceBlocklistAddressesResponse](../../models/putv2workspaceblocklistaddressesresponse.md)**

### Errors

| Error Type                                                     | Status Code                                                    | Content Type                                                   |
| -------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- |
| errors.PutV2WorkspaceBlocklistAddressesValidationTypeError     | 400                                                            | application/json                                               |
| errors.PutV2WorkspaceBlocklistAddressesAuthError               | 403                                                            | application/json                                               |
| errors.PutV2WorkspaceBlocklistAddressesUniquenessConflictError | 409                                                            | application/json                                               |
| errors.SDKDefaultError                                         | 4XX, 5XX                                                       | \*/\*                                                          |

## delete_v2_workspace_blocklist_addresses_address_

An address is an email address (jane@acme.com) or a domain (acme.com).

Removes an address from the workspace blocklist, whatever its enforcement level. The address itself is its key: there is no separate ID.

The address is normalized as when it is added: email addresses and domains are trimmed and lowercased, a URL is reduced to its hostname, and a leading `www.` is removed. So the address is found whatever form it was added in. A URL, or any other value with reserved characters, must be percent-encoded in the path.

An address that isn't on the workspace blocklist returns a `404`. A client retrying a request can treat a `404` as done.

Removing a protected address takes effect immediately. Removing a blocked address takes effect once each connected mailbox has re-synced, which may take a few minutes.

A user-level access token can only call this endpoint if the workspace member it acts for is a workspace admin.

This endpoint is in alpha and may be subject to breaking changes as we gather feedback.

Required scopes: `email_calendar_blocklist:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/workspace_blocklist_addresses/{address}" method="delete" path="/v2/workspace_blocklist_addresses/{address}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.workspace_blocklist.delete_v2_workspace_blocklist_addresses_address_(address="jane@acme.com")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `address`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | jane@acme.com                                                       |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2WorkspaceBlocklistAddressesAddressResponse](../../models/deletev2workspaceblocklistaddressesaddressresponse.md)**

### Errors

| Error Type                                                           | Status Code                                                          | Content Type                                                         |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| errors.DeleteV2WorkspaceBlocklistAddressesAddressValidationTypeError | 400                                                                  | application/json                                                     |
| errors.DeleteV2WorkspaceBlocklistAddressesAddressUnauthorizedError   | 403                                                                  | application/json                                                     |
| errors.DeleteV2WorkspaceBlocklistAddressesAddressNotFoundError       | 404                                                                  | application/json                                                     |
| errors.SDKDefaultError                                               | 4XX, 5XX                                                             | \*/\*                                                                |
