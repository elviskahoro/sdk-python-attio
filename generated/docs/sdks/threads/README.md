# Threads

## Overview

Threads are groups of [comments](/rest-api/endpoint-reference/comments/get-a-comment) on either a record or entry.

### Available Operations

* [get_v2_threads](#get_v2_threads) - List threads
* [get_v2_threads_thread_id_](#get_v2_threads_thread_id_) - Get a thread and its comments

## get_v2_threads

List threads of comments on a record or list entry.

Each thread in the response includes at most `80` replies, starting with the oldest. When a thread holds more, its `has_more_comments` is `true`; use [Get a thread and its comments](/rest-api/endpoint-reference/threads/get-a-thread-and-its-comments) to page through every comment in that thread.

To view threads on records, you will need the `object_configuration:read` and `record_permission:read` scopes.

To view threads on list entries, you will need the `list_configuration:read` and `list_entry:read` scopes.

Required scopes: `comment:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/threads" method="get" path="/v2/threads" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.threads.get_v2_threads(record_id="891dcbfc-9141-415d-9b2a-2238a6cc012d", object="people", entry_id="2e6e29ea-c4e0-4f44-842d-78a891f8c156", list_id="33ebdbe9-e529-47c9-b894-0ba25e9c15c0", limit=10, offset=5)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `record_id`                                                         | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 891dcbfc-9141-415d-9b2a-2238a6cc012d                                |
| `object`                                                            | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | people                                                              |
| `entry_id`                                                          | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 2e6e29ea-c4e0-4f44-842d-78a891f8c156                                |
| `list_id`                                                           | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 33ebdbe9-e529-47c9-b894-0ba25e9c15c0                                |
| `limit`                                                             | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 10                                                                  |
| `offset`                                                            | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 5                                                                   |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2ThreadsResponse](../../models/getv2threadsresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## get_v2_threads_thread_id_

Get a thread and page through its comments, oldest first, starting with the comment that opened it.

Comments are paginated: at most `250` are returned per request. Keep paginating for as long as a `next_cursor` is returned.

Supply `created_after` to return only the comments created after a timestamp, which is useful when polling a thread for new replies. The comment that opened the thread is returned only when it also satisfies the filter.

To view threads on records, you will need the `object_configuration:read` and `record_permission:read` scopes.

To view threads on list entries, you will need the `list_configuration:read` and `list_entry:read` scopes.

Required scopes: `comment:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/threads/{thread_id}" method="get" path="/v2/threads/{thread_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.threads.get_v2_threads_thread_id_(thread_id="a649e4d9-435c-43fb-83ba-847b4876f27a", limit=250, cursor="eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr", created_after="2023-01-01T15:00:00.000000000Z")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  | Example                                                                      |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `thread_id`                                                                  | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          | a649e4d9-435c-43fb-83ba-847b4876f27a                                         |
| `limit`                                                                      | *Optional[int]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | 250                                                                          |
| `cursor`                                                                     | *Optional[str]*                                                              | :heavy_minus_sign:                                                           | N/A                                                                          | eyJkZXNjcmlwdGlvbiI6ICJ0aGlzIGlzIGEgY3Vyc29yIn0=.eM56CGbqZ6G1NHiJchTIkH4vKDr |
| `created_after`                                                              | *OptionalNullable[str]*                                                      | :heavy_minus_sign:                                                           | N/A                                                                          | 2023-01-01T15:00:00.000000000Z                                               |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |                                                                              |

### Response

**[models.GetV2ThreadsThreadIDResponse](../../models/getv2threadsthreadidresponse.md)**

### Errors

| Error Type                               | Status Code                              | Content Type                             |
| ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| errors.GetV2ThreadsThreadIDNotFoundError | 404                                      | application/json                         |
| errors.SDKDefaultError                   | 4XX, 5XX                                 | \*/\*                                    |