# Tasks

## Overview

A task is a defined, actionable item with references to linked records and assigned workspace members.

### Available Operations

* [get_v2_tasks](#get_v2_tasks) - List tasks
* [post_v2_tasks](#post_v2_tasks) - Create a task
* [get_v2_tasks_task_id_](#get_v2_tasks_task_id_) - Get a task
* [patch_v2_tasks_task_id_](#patch_v2_tasks_task_id_) - Update a task
* [delete_v2_tasks_task_id_](#delete_v2_tasks_task_id_) - Delete a task

## get_v2_tasks

List all tasks. Results are sorted by creation date, from oldest to newest.

Required scopes: `task:read`, `object_configuration:read`, `record_permission:read`, `user_management:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/tasks" method="get" path="/v2/tasks" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.tasks.get_v2_tasks(limit=10, offset=5, sort="created_at:desc", linked_object="people", linked_record_id="891dcbfc-9141-415d-9b2a-2238a6cc012d", assignee="50cf242c-7fa3-4cad-87d0-75b1af71c57b", is_completed=True)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Required                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `limit`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | *Optional[int]*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 10                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `offset`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | *Optional[int]*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `sort`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | [Optional[models.GetV2TasksSort]](../../models/getv2taskssort.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Optionally sort the results. "created_at:asc" returns oldest results first, "created_at:desc" returns the newest results first. "completed_at:asc" and "completed_at:desc" sort by completion time. With "completed_at:asc", incomplete tasks (no completion date) appear first, followed by completed tasks oldest-first. With "completed_at:desc", completed tasks appear first (newest-first), followed by incomplete tasks. To exclude incomplete tasks, filter by is_completed. If unspecified, defaults to "created_at:asc" (oldest results first). | created_at:desc                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `linked_object`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | *Optional[str]*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | people                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `linked_record_id`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | *Optional[str]*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 891dcbfc-9141-415d-9b2a-2238a6cc012d                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `assignee`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | *OptionalNullable[str]*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **Example 1:** 50cf242c-7fa3-4cad-87d0-75b1af71c57b<br/>**Example 2:** alice@attio.com                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `is_completed`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | *Optional[bool]*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | N/A                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | true                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `retries`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

### Response

**[models.GetV2TasksResponse](../../models/getv2tasksresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_tasks

Creates a new task.

At present, tasks can only be created from plaintext without record reference formatting.

Required scopes: `task:read-write`, `object_configuration:read`, `record_permission:read`, `user_management:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/tasks" method="post" path="/v2/tasks" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.tasks.post_v2_tasks(data={
        "content": "Follow up on current software solutions",
        "format_": "plaintext",
        "deadline_at": "2023-01-01T15:00:00.000000000Z",
        "is_completed": False,
        "linked_records": [
            "person@company.com",
            "fundstack.com",
        ],
        "assignees": [],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data`                                                              | [models.PostV2TasksData](../../models/postv2tasksdata.md)           | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2TasksResponse](../../models/postv2tasksresponse.md)**

### Errors

| Error Type                            | Status Code                           | Content Type                          |
| ------------------------------------- | ------------------------------------- | ------------------------------------- |
| errors.PostV2TasksInvalidRequestError | 400                                   | application/json                      |
| errors.PostV2TasksNotFoundError       | 404                                   | application/json                      |
| errors.SDKDefaultError                | 4XX, 5XX                              | \*/\*                                 |

## get_v2_tasks_task_id_

Get a single task by ID.

Required scopes: `task:read`, `object_configuration:read`, `record_permission:read`, `user_management:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/tasks/{task_id}" method="get" path="/v2/tasks/{task_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.tasks.get_v2_tasks_task_id_(task_id="649e34f4-c39a-4f4d-99ef-48a36bef8f04")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `task_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 649e34f4-c39a-4f4d-99ef-48a36bef8f04                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2TasksTaskIDResponse](../../models/getv2taskstaskidresponse.md)**

### Errors

| Error Type                           | Status Code                          | Content Type                         |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |
| errors.GetV2TasksTaskIDNotFoundError | 404                                  | application/json                     |
| errors.SDKDefaultError               | 4XX, 5XX                             | \*/\*                                |

## patch_v2_tasks_task_id_

Updates an existing task by `task_id`. At present, only the `deadline_at`, `is_completed`, `linked_records`, and `assignees` fields can be updated.

Required scopes: `task:read-write`, `object_configuration:read`, `record_permission:read`, `user_management:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/tasks/{task_id}" method="patch" path="/v2/tasks/{task_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.tasks.patch_v2_tasks_task_id_(task_id="649e34f4-c39a-4f4d-99ef-48a36bef8f04", data={
        "deadline_at": "2023-01-01T15:00:00.000000000Z",
        "is_completed": False,
        "linked_records": [
            "person@company.com",
            "fundstack.com",
        ],
        "assignees": [
            {
                "workspace_member_email_address": "alice@attio.com",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                               | Type                                                                    | Required                                                                | Description                                                             | Example                                                                 |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `task_id`                                                               | *str*                                                                   | :heavy_check_mark:                                                      | N/A                                                                     | 649e34f4-c39a-4f4d-99ef-48a36bef8f04                                    |
| `data`                                                                  | [models.PatchV2TasksTaskIDData](../../models/patchv2taskstaskiddata.md) | :heavy_check_mark:                                                      | N/A                                                                     |                                                                         |
| `retries`                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)        | :heavy_minus_sign:                                                      | Configuration to override the default retry behavior of the client.     |                                                                         |

### Response

**[models.PatchV2TasksTaskIDResponse](../../models/patchv2taskstaskidresponse.md)**

### Errors

| Error Type                                   | Status Code                                  | Content Type                                 |
| -------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| errors.PatchV2TasksTaskIDInvalidRequestError | 400                                          | application/json                             |
| errors.PatchV2TasksTaskIDNotFoundError       | 404                                          | application/json                             |
| errors.SDKDefaultError                       | 4XX, 5XX                                     | \*/\*                                        |

## delete_v2_tasks_task_id_

Delete a task by ID.

Required scopes: `task:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/tasks/{task_id}" method="delete" path="/v2/tasks/{task_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.tasks.delete_v2_tasks_task_id_(task_id="649e34f4-c39a-4f4d-99ef-48a36bef8f04")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `task_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | 649e34f4-c39a-4f4d-99ef-48a36bef8f04                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2TasksTaskIDResponse](../../models/deletev2taskstaskidresponse.md)**

### Errors

| Error Type                              | Status Code                             | Content Type                            |
| --------------------------------------- | --------------------------------------- | --------------------------------------- |
| errors.DeleteV2TasksTaskIDNotFoundError | 404                                     | application/json                        |
| errors.SDKDefaultError                  | 4XX, 5XX                                | \*/\*                                   |