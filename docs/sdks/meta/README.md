# Meta

## Overview

Meta endpoints are used to get information about the API token.

### Available Operations

* [get_v2_self](#get_v2_self) - Identify

## get_v2_self

Identify the current access token, the workspace it is linked to, and any permissions it has.

Every kind of Attio access token can be introspected:

- **Workspace access tokens**, created from a workspace's settings. These have no OAuth client, so `client_id` and `aud` contain the workspace access token's own ID.
- **OAuth access tokens**, granted to an app through the OAuth 2.0 authorization code flow. `client_id` and `aud` contain the app ID.
- **App access tokens**, issued to an app installation and exposed to that app's server functions as `ATTIO_API_TOKEN`. `client_id` and `aud` contain the app ID.

Per [RFC 7662](https://www.rfc-editor.org/rfc/rfc7662), `active` is the only member guaranteed to be present. `exp` is always `null`, because Attio access tokens do not currently expire.
All other members are optional, and are omitted rather than returned as `null` when they are not present.

Unknown, revoked, and deleted tokens are not treated as an error. They return `200` with `{"active": false}` and no other members.

### Example Usage: App access token

<!-- UsageSnippet language="python" operationID="get_/v2/self" method="get" path="/v2/self" example="App access token" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meta.get_v2_self()

    # Handle response
    print(res)

```
### Example Usage: Inactive token

<!-- UsageSnippet language="python" operationID="get_/v2/self" method="get" path="/v2/self" example="Inactive token" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meta.get_v2_self()

    # Handle response
    print(res)

```
### Example Usage: User-level app access token

<!-- UsageSnippet language="python" operationID="get_/v2/self" method="get" path="/v2/self" example="User-level app access token" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meta.get_v2_self()

    # Handle response
    print(res)

```
### Example Usage: Workspace access token

<!-- UsageSnippet language="python" operationID="get_/v2/self" method="get" path="/v2/self" example="Workspace access token" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.meta.get_v2_self()

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.GetV2SelfResponse](../../models/getv2selfresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |