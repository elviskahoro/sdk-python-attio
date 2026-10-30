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
from attio.utils import parse_datetime


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.sql.post_v2_sql(sql="SELECT * FROM companies WHERE companies.name = 'Fundstack'", parameters={
        "name": {
            "type": "string",
            "value": "Fundstack",
        },
        "since": {
            "type": "timestamp",
            "value": parse_datetime("2023-01-01T15:00:00.000000000Z"),
        },
        "names": {
            "type": "list",
            "item_type": "string",
            "value": [
                "Fundstack",
                "Acme",
            ],
        },
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Required                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `sql`                                                                                                                                                                                                                                                                                                                                                                                                                                                              | *str*                                                                                                                                                                                                                                                                                                                                                                                                                                                              | :heavy_check_mark:                                                                                                                                                                                                                                                                                                                                                                                                                                                 | The SQL query to be executed. Use `$name` placeholders to reference values from `parameters` instead of inlining them into the query.                                                                                                                                                                                                                                                                                                                              | SELECT * FROM companies WHERE (name = $name OR name = ANY($names)) AND created_at >= $since                                                                                                                                                                                                                                                                                                                                                                        |
| `parameters`                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Dict[str, [models.Parameters](../../models/parameters.md)]                                                                                                                                                                                                                                                                                                                                                                                                         | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Named parameters referenced in the query using `$name` syntax. A maximum of 25 parameters can be provided. Each parameter must declare its type explicitly. Names must start with a letter or underscore, only contain letters, digits and underscores, and be at most 64 characters long. Compare against a list parameter with `= ANY($name)`, not `IN ($name)`, which does not type check. Read a field of a struct parameter with `get_field($name, 'field')`. | {<br/>"name": {<br/>"type": "string",<br/>"value": "Fundstack"<br/>},<br/>"since": {<br/>"type": "timestamp",<br/>"value": "2023-01-01T15:00:00.000000000Z"<br/>},<br/>"names": {<br/>"type": "list",<br/>"item_type": "string",<br/>"value": [<br/>"Fundstack",<br/>"Acme"<br/>]<br/>}<br/>}                                                                                                                                                                      |
| `retries`                                                                                                                                                                                                                                                                                                                                                                                                                                                          | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                                                                                                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                                                                                                                                                                                |                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### Response

**[models.PostV2SQLResponse](../../models/postv2sqlresponse.md)**

### Errors

| Error Type                  | Status Code                 | Content Type                |
| --------------------------- | --------------------------- | --------------------------- |
| errors.PostV2SQLFilterError | 400                         | application/json            |
| errors.SDKDefaultError      | 4XX, 5XX                    | \*/\*                       |