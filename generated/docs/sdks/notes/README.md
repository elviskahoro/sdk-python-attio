# Notes

## Overview

Notes are rich text documents that reference a single parent record.

### Available Operations

* [get_v2_notes](#get_v2_notes) - List notes
* [post_v2_notes](#post_v2_notes) - Create a note
* [get_v2_notes_note_id_](#get_v2_notes_note_id_) - Get a note
* [patch_v2_notes_note_id_](#patch_v2_notes_note_id_) - Update a note
* [delete_v2_notes_note_id_](#delete_v2_notes_note_id_) - Delete a note

## get_v2_notes

List notes for all records or for a specific record.

This endpoint is temporarily rate limited to 10 requests per second.

Required scopes: `note:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/notes" method="get" path="/v2/notes" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.notes.get_v2_notes(limit=10, offset=5, parent_object="people", parent_record_id="891dcbfc-9141-415d-9b2a-2238a6cc012d")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `limit`                                                             | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 10                                                                  |
| `offset`                                                            | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 5                                                                   |
| `parent_object`                                                     | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | people                                                              |
| `parent_record_id`                                                  | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 | 891dcbfc-9141-415d-9b2a-2238a6cc012d                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2NotesResponse](../../models/getv2notesresponse.md)**

### Errors

| Error Type                     | Status Code                    | Content Type                   |
| ------------------------------ | ------------------------------ | ------------------------------ |
| errors.GetV2NotesNotFoundError | 404                            | application/json               |
| errors.SDKDefaultError         | 4XX, 5XX                       | \*/\*                          |

## post_v2_notes

Creates a new note for a given record.

Required scopes: `note:read-write`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/notes" method="post" path="/v2/notes" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.notes.post_v2_notes(data={
        "parent_object": "people",
        "parent_record_id": "891dcbfc-9141-415d-9b2a-2238a6cc012d",
        "title": "Initial Prospecting Call Summary",
        "format_": "plaintext",
        "content": "# Meeting Recap: Q4 Planning\n\n**Date:** 2023-10-26\n**Attendees:** Alex, Jamie, Casey\n\n## Key Discussion Points\n\n- Reviewed Q3 performance metrics.\n- Brainstormed key initiatives for Q4.\n- Discussed budget allocation for ==Project Phoenix==.\n\n## Action Items\n\n1. Alex to finalize Q4 roadmap by EOD Friday.\n2. Jamie to schedule follow-up with [Marketing Team](https://app.attio.com/teams/marketing).\n3. Casey to draft initial budget for ~~Project Chimera~~ (now deferred).\n\n*Next steps: Review draft roadmap next week.*",
        "created_at": "2023-01-01T15:00:00.000000000Z",
        "meeting_id": "14beef7a-99f7-4534-a87e-70b564330a4c",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data`                                                              | [models.PostV2NotesData](../../models/postv2notesdata.md)           | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2NotesResponse](../../models/postv2notesresponse.md)**

### Errors

| Error Type                            | Status Code                           | Content Type                          |
| ------------------------------------- | ------------------------------------- | ------------------------------------- |
| errors.PostV2NotesNotFoundError       | 404                                   | application/json                      |
| errors.PostV2NotesValidationTypeError | 413                                   | application/json                      |
| errors.SDKDefaultError                | 4XX, 5XX                              | \*/\*                                 |

## get_v2_notes_note_id_

Get a single note by ID.

Required scopes: `note:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/notes/{note_id}" method="get" path="/v2/notes/{note_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.notes.get_v2_notes_note_id_(note_id="ff3f3bd4-40f4-4f80-8187-cd02385af424")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `note_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | ff3f3bd4-40f4-4f80-8187-cd02385af424                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2NotesNoteIDResponse](../../models/getv2notesnoteidresponse.md)**

### Errors

| Error Type                           | Status Code                          | Content Type                         |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |
| errors.GetV2NotesNoteIDNotFoundError | 404                                  | application/json                     |
| errors.SDKDefaultError               | 4XX, 5XX                             | \*/\*                                |

## patch_v2_notes_note_id_

Updates an existing note's title and/or content. Only the fields you provide are changed, and any field you omit is left untouched. Providing `content` replaces the note's entire content. A note's parent record cannot be changed.

Required scopes: `note:read-write`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="patch_/v2/notes/{note_id}" method="patch" path="/v2/notes/{note_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.notes.patch_v2_notes_note_id_(note_id="ff3f3bd4-40f4-4f80-8187-cd02385af424", data={
        "title": "Initial Prospecting Call Summary",
        "format_": "markdown",
        "content": "# Meeting Recap: Q4 Planning\n\n**Date:** 2023-10-26\n**Attendees:** Alex, Jamie, Casey\n\n## Key Discussion Points\n\n- Reviewed Q3 performance metrics.\n- Brainstormed key initiatives for Q4.\n- Discussed budget allocation for ==Project Phoenix==.\n\n## Action Items\n\n1. Alex to finalize Q4 roadmap by EOD Friday.\n2. Jamie to schedule follow-up with [Marketing Team](https://app.attio.com/teams/marketing).\n3. Casey to draft initial budget for ~~Project Chimera~~ (now deferred).\n\n*Next steps: Review draft roadmap next week.*",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                               | Type                                                                    | Required                                                                | Description                                                             | Example                                                                 |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `note_id`                                                               | *str*                                                                   | :heavy_check_mark:                                                      | N/A                                                                     | ff3f3bd4-40f4-4f80-8187-cd02385af424                                    |
| `data`                                                                  | [models.PatchV2NotesNoteIDData](../../models/patchv2notesnoteiddata.md) | :heavy_check_mark:                                                      | N/A                                                                     |                                                                         |
| `retries`                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)        | :heavy_minus_sign:                                                      | Configuration to override the default retry behavior of the client.     |                                                                         |

### Response

**[models.PatchV2NotesNoteIDResponse](../../models/patchv2notesnoteidresponse.md)**

### Errors

| Error Type                                   | Status Code                                  | Content Type                                 |
| -------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| errors.PatchV2NotesNoteIDNotFoundError       | 404                                          | application/json                             |
| errors.PatchV2NotesNoteIDValidationTypeError | 413                                          | application/json                             |
| errors.SDKDefaultError                       | 4XX, 5XX                                     | \*/\*                                        |

## delete_v2_notes_note_id_

Delete a single note by ID.

Required scopes: `note:read-write`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/notes/{note_id}" method="delete" path="/v2/notes/{note_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.notes.delete_v2_notes_note_id_(note_id="ff3f3bd4-40f4-4f80-8187-cd02385af424")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `note_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | ff3f3bd4-40f4-4f80-8187-cd02385af424                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2NotesNoteIDResponse](../../models/deletev2notesnoteidresponse.md)**

### Errors

| Error Type                              | Status Code                             | Content Type                            |
| --------------------------------------- | --------------------------------------- | --------------------------------------- |
| errors.DeleteV2NotesNoteIDNotFoundError | 404                                     | application/json                        |
| errors.SDKDefaultError                  | 4XX, 5XX                                | \*/\*                                   |