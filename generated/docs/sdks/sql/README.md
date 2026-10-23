# Sql

## Overview

Query records and list entries across your workspace using SQL. A single query can reference any object or list in the workspace.

### Available Operations

* [post_v2_sql](#post_v2_sql) - Query SQL

## post_v2_sql

Query records and lists with SQL. Your workspace must be on the Enterprise plan in order to access this endpoint.

This endpoint is rate limited to 2 requests per second.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `record_permission:read`, `object_configuration:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/sql" method="post" path="/v2/sql" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.sql.post_v2_sql(sql="SELECT * FROM companies WHERE companies.name = 'Fundstack'")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `sql`                                                               | *str*                                                               | :heavy_check_mark:                                                  | The SQL query to be executed.                                       | SELECT * FROM companies WHERE companies.name = 'Fundstack'          |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.PostV2SQLResponse](../../models/postv2sqlresponse.md)**

### Errors

| Error Type                  | Status Code                 | Content Type                |
| --------------------------- | --------------------------- | --------------------------- |
| errors.PostV2SQLFilterError | 400                         | application/json            |
| errors.SDKDefaultError      | 4XX, 5XX                    | \*/\*                       |