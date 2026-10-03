# Attio Python SDK

<div align="left">
    <a href="https://opensource.org/licenses/MIT">
        <img alt="MIT License" src="https://img.shields.io/badge/License-MIT-blue.svg" style="width: 100px; height: 28px;" />
    </a>
</div>

<br /><br />

Type-safe Python client for the [Attio API](https://developers.attio.com/), with support for sync and async usage.

<!-- Start Summary [summary] -->
## Summary


<!-- End Summary [summary] -->

<!-- Start Table of Contents [toc] -->
## Table of Contents
<!-- $toc-max-depth=2 -->
* [Attio Python SDK](#attio-python-sdk)
  * [SDK Installation](#sdk-installation)
  * [IDE Support](#ide-support)
  * [SDK Example Usage](#sdk-example-usage)
  * [Authentication](#authentication)
  * [Common Workflows](#common-workflows)
  * [Available Resources and Operations](#available-resources-and-operations)
  * [File uploads](#file-uploads)
  * [Retries](#retries)
  * [Error Handling](#error-handling)
  * [Server Selection](#server-selection)
  * [Custom HTTP Client](#custom-http-client)
  * [Resource Management](#resource-management)
  * [Debugging](#debugging)
  * [Troubleshooting](#troubleshooting)

<!-- End Table of Contents [toc] -->
<!-- Start SDK Installation [installation] -->
## SDK Installation

> [!TIP]
> To finish publishing your SDK to PyPI you must [run your first generation action](https://www.speakeasy.com/docs/github-setup#step-by-step-guide).


> [!NOTE]
> **Python version upgrade policy**
>
> Once a Python version reaches its [official end of life date](https://devguide.python.org/versions/), a 3-month grace period is provided for users to upgrade. Following this grace period, the minimum python version supported in the SDK will be updated.

The SDK can be installed with *uv*, *pip*, or *poetry* package managers.

### uv

*uv* is a fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It's recommended for its speed and modern Python tooling capabilities.

```bash
uv add git+<UNSET>.git
```

### PIP

*PIP* is the default package installer for Python, enabling easy installation and management of packages from PyPI via the command line.

```bash
pip install git+<UNSET>.git
```

### Poetry

*Poetry* is a modern tool that simplifies dependency management and package publishing by using a single `pyproject.toml` file to handle project metadata and dependencies.

```bash
poetry add git+<UNSET>.git
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from attio python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "attio",
# ]
# ///

from attio import SDK

sdk = SDK(
  # SDK arguments
)

# Rest of script here...
```

Once that is saved to a file, you can run it with `uv run script.py` where
`script.py` can be replaced with the actual file name.
<!-- End SDK Installation [installation] -->

<!-- Start IDE Support [idesupport] -->
## IDE Support

### PyCharm

Generally, the SDK will work well with most IDEs out of the box. However, when using PyCharm, you can enjoy much better integration with Pydantic by installing an additional plugin.

- [PyCharm Pydantic Plugin](https://docs.pydantic.dev/latest/integrations/pycharm/)
<!-- End IDE Support [idesupport] -->

<!-- Start SDK Example Usage [usage] -->
## SDK Example Usage

### Example

```python
# Synchronous Example
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects()

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from attio import SDK

async def main():

    async with SDK(
        oauth2="<YOUR_OAUTH2_HERE>",
    ) as sdk:

        res = await sdk.objects.get_v2_objects_async()

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

<!-- Start Authentication [security] -->
## Authentication

### Per-Client Security Schemes

This SDK supports the following security scheme globally:

| Name     | Type   | Scheme       |
| -------- | ------ | ------------ |
| `oauth2` | oauth2 | OAuth2 token |

To authenticate with the API the `oauth2` parameter must be set when initializing the SDK client instance. For example:
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects()

    # Handle response
    print(res)

```
<!-- End Authentication [security] -->

## Common Workflows

### List objects

```python
from attio import SDK

with SDK(oauth2="<YOUR_OAUTH2_HERE>") as sdk:
    res = sdk.objects.get_v2_objects()
    print(res)
```

### Create a record (people)

```python
from attio import SDK

with SDK(oauth2="<YOUR_OAUTH2_HERE>") as sdk:
    res = sdk.records.post_v2_objects_object_records(
        object="people",
        data={
            "values": {
                "<ATTRIBUTE_SLUG_OR_ID>": ["Ada Lovelace"],
            },
        },
    )
    print(res)
```

### Query records (people)

```python
from attio import SDK

with SDK(oauth2="<YOUR_OAUTH2_HERE>") as sdk:
    res = sdk.records.post_v2_objects_object_records_query(
        object="people",
        limit=25,
        offset=0,
    )
    print(res)
```

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

### [Activities](docs/sdks/activities/README.md)

* [get_v2_activities](docs/sdks/activities/README.md#get_v2_activities) - List activities
* [post_v2_activities](docs/sdks/activities/README.md#post_v2_activities) - Create an activity
* [get_v2_activities_activity_](docs/sdks/activities/README.md#get_v2_activities_activity_) - Get an activity
* [patch_v2_activities_activity_](docs/sdks/activities/README.md#patch_v2_activities_activity_) - Update an activity
* [delete_v2_activities_activity_](docs/sdks/activities/README.md#delete_v2_activities_activity_) - Delete an activity

### [ActivityRecords](docs/sdks/activityrecords/README.md)

* [post_v2_activities_activity_records_query](docs/sdks/activityrecords/README.md#post_v2_activities_activity_records_query) - List activity records
* [post_v2_activities_activity_records](docs/sdks/activityrecords/README.md#post_v2_activities_activity_records) - Create an activity record
* [put_v2_activities_activity_records](docs/sdks/activityrecords/README.md#put_v2_activities_activity_records) - Upsert an activity record
* [get_v2_activities_activity_records_record_id_](docs/sdks/activityrecords/README.md#get_v2_activities_activity_records_record_id_) - Get an activity record
* [patch_v2_activities_activity_records_record_id_](docs/sdks/activityrecords/README.md#patch_v2_activities_activity_records_record_id_) - Update an activity record (append multiselect values)
* [put_v2_activities_activity_records_record_id_](docs/sdks/activityrecords/README.md#put_v2_activities_activity_records_record_id_) - Update an activity record (overwrite multiselect values)
* [delete_v2_activities_activity_records_record_id_](docs/sdks/activityrecords/README.md#delete_v2_activities_activity_records_record_id_) - Delete an activity record

### [Attributes](docs/sdks/attributes/README.md)

* [get_v2_target_identifier_attributes](docs/sdks/attributes/README.md#get_v2_target_identifier_attributes) - List attributes
* [post_v2_target_identifier_attributes](docs/sdks/attributes/README.md#post_v2_target_identifier_attributes) - Create an attribute
* [get_v2_target_identifier_attributes_attribute_](docs/sdks/attributes/README.md#get_v2_target_identifier_attributes_attribute_) - Get an attribute
* [patch_v2_target_identifier_attributes_attribute_](docs/sdks/attributes/README.md#patch_v2_target_identifier_attributes_attribute_) - Update an attribute
* [get_v2_target_identifier_attributes_attribute_options](docs/sdks/attributes/README.md#get_v2_target_identifier_attributes_attribute_options) - List select options
* [post_v2_target_identifier_attributes_attribute_options](docs/sdks/attributes/README.md#post_v2_target_identifier_attributes_attribute_options) - Create a select option
* [patch_v2_target_identifier_attributes_attribute_options_option_](docs/sdks/attributes/README.md#patch_v2_target_identifier_attributes_attribute_options_option_) - Update a select option
* [get_v2_target_identifier_attributes_attribute_statuses](docs/sdks/attributes/README.md#get_v2_target_identifier_attributes_attribute_statuses) - List statuses
* [post_v2_target_identifier_attributes_attribute_statuses](docs/sdks/attributes/README.md#post_v2_target_identifier_attributes_attribute_statuses) - Create a status
* [patch_v2_target_identifier_attributes_attribute_statuses_status_](docs/sdks/attributes/README.md#patch_v2_target_identifier_attributes_attribute_statuses_status_) - Update a status

### [CallRecordings](docs/sdks/callrecordings/README.md)

* [get_v2_meetings_meeting_id_call_recordings](docs/sdks/callrecordings/README.md#get_v2_meetings_meeting_id_call_recordings) - List call recordings
* [post_v2_meetings_meeting_id_call_recordings](docs/sdks/callrecordings/README.md#post_v2_meetings_meeting_id_call_recordings) - Create call recording
* [get_v2_meetings_meeting_id_call_recordings_call_recording_id_](docs/sdks/callrecordings/README.md#get_v2_meetings_meeting_id_call_recordings_call_recording_id_) - Get call recording
* [delete_v2_meetings_meeting_id_call_recordings_call_recording_id_](docs/sdks/callrecordings/README.md#delete_v2_meetings_meeting_id_call_recordings_call_recording_id_) - Delete call recording

### [Comments](docs/sdks/comments/README.md)

* [post_v2_comments](docs/sdks/comments/README.md#post_v2_comments) - Create a comment
* [get_v2_comments_comment_id_](docs/sdks/comments/README.md#get_v2_comments_comment_id_) - Get a comment
* [delete_v2_comments_comment_id_](docs/sdks/comments/README.md#delete_v2_comments_comment_id_) - Delete a comment

### [Emails](docs/sdks/emails/README.md)

* [get_v2_emails](docs/sdks/emails/README.md#get_v2_emails) - List emails

### [Entries](docs/sdks/entries/README.md)

* [post_v2_lists_list_entries_query](docs/sdks/entries/README.md#post_v2_lists_list_entries_query) - List entries
* [post_v2_lists_list_entries](docs/sdks/entries/README.md#post_v2_lists_list_entries) - Create an entry (add record to list)
* [put_v2_lists_list_entries](docs/sdks/entries/README.md#put_v2_lists_list_entries) - Upsert a list entry by parent
* [get_v2_lists_list_entries_entry_id_](docs/sdks/entries/README.md#get_v2_lists_list_entries_entry_id_) - Get a list entry
* [patch_v2_lists_list_entries_entry_id_](docs/sdks/entries/README.md#patch_v2_lists_list_entries_entry_id_) - Update a list entry (append multiselect values)
* [put_v2_lists_list_entries_entry_id_](docs/sdks/entries/README.md#put_v2_lists_list_entries_entry_id_) - Update a list entry (overwrite multiselect values)
* [delete_v2_lists_list_entries_entry_id_](docs/sdks/entries/README.md#delete_v2_lists_list_entries_entry_id_) - Delete a list entry
* [get_v2_lists_list_entries_entry_id_attributes_attribute_values](docs/sdks/entries/README.md#get_v2_lists_list_entries_entry_id_attributes_attribute_values) - List attribute values for a list entry
* [put_v2_lists_list_entries_entry_id_attributes_attribute_values](docs/sdks/entries/README.md#put_v2_lists_list_entries_entry_id_attributes_attribute_values) - Write list entry attribute values

### [Files](docs/sdks/files/README.md)

* [get_v2_files](docs/sdks/files/README.md#get_v2_files) - List files
* [post_v2_files](docs/sdks/files/README.md#post_v2_files) - Create a folder
* [post_v2_files_upload](docs/sdks/files/README.md#post_v2_files_upload) - Upload a file
* [get_v2_files_file_id_](docs/sdks/files/README.md#get_v2_files_file_id_) - Get a file
* [delete_v2_files_file_id_](docs/sdks/files/README.md#delete_v2_files_file_id_) - Delete a file
* [get_v2_files_file_id_download](docs/sdks/files/README.md#get_v2_files_file_id_download) - Download a file

### [Lists](docs/sdks/lists/README.md)

* [get_v2_lists](docs/sdks/lists/README.md#get_v2_lists) - List all lists
* [post_v2_lists](docs/sdks/lists/README.md#post_v2_lists) - Create a list
* [get_v2_lists_list_](docs/sdks/lists/README.md#get_v2_lists_list_) - Get a list
* [patch_v2_lists_list_](docs/sdks/lists/README.md#patch_v2_lists_list_) - Update a list
* [get_v2_lists_list_views](docs/sdks/lists/README.md#get_v2_lists_list_views) - List views for list

### [Meetings](docs/sdks/meetings/README.md)

* [get_v2_meetings](docs/sdks/meetings/README.md#get_v2_meetings) - List meetings
* [post_v2_meetings](docs/sdks/meetings/README.md#post_v2_meetings) - Create a meeting
* [get_v2_meetings_meeting_id_](docs/sdks/meetings/README.md#get_v2_meetings_meeting_id_) - Get a meeting
* [patch_v2_meetings_meeting_id_](docs/sdks/meetings/README.md#patch_v2_meetings_meeting_id_) - Update a meeting (append linked records)
* [put_v2_meetings_meeting_id_](docs/sdks/meetings/README.md#put_v2_meetings_meeting_id_) - Update a meeting (overwrite linked records)
* [delete_v2_meetings_meeting_id_](docs/sdks/meetings/README.md#delete_v2_meetings_meeting_id_) - Delete a meeting

### [Meta](docs/sdks/meta/README.md)

* [get_v2_self](docs/sdks/meta/README.md#get_v2_self) - Identify

### [Notes](docs/sdks/notes/README.md)

* [get_v2_notes](docs/sdks/notes/README.md#get_v2_notes) - List notes
* [post_v2_notes](docs/sdks/notes/README.md#post_v2_notes) - Create a note
* [get_v2_notes_note_id_](docs/sdks/notes/README.md#get_v2_notes_note_id_) - Get a note
* [patch_v2_notes_note_id_](docs/sdks/notes/README.md#patch_v2_notes_note_id_) - Update a note
* [delete_v2_notes_note_id_](docs/sdks/notes/README.md#delete_v2_notes_note_id_) - Delete a note

### [Objects](docs/sdks/objects/README.md)

* [get_v2_objects](docs/sdks/objects/README.md#get_v2_objects) - List objects
* [post_v2_objects](docs/sdks/objects/README.md#post_v2_objects) - Create an object
* [get_v2_objects_object_](docs/sdks/objects/README.md#get_v2_objects_object_) - Get an object
* [patch_v2_objects_object_](docs/sdks/objects/README.md#patch_v2_objects_object_) - Update an object
* [delete_v2_objects_object_](docs/sdks/objects/README.md#delete_v2_objects_object_) - Delete an object
* [get_v2_objects_object_views](docs/sdks/objects/README.md#get_v2_objects_object_views) - List views for object

### [Records](docs/sdks/records/README.md)

* [post_v2_objects_object_records_query](docs/sdks/records/README.md#post_v2_objects_object_records_query) - List records
* [post_v2_objects_object_records](docs/sdks/records/README.md#post_v2_objects_object_records) - Create a record
* [put_v2_objects_object_records](docs/sdks/records/README.md#put_v2_objects_object_records) - Upsert a record
* [get_v2_objects_object_records_record_id_](docs/sdks/records/README.md#get_v2_objects_object_records_record_id_) - Get a record
* [patch_v2_objects_object_records_record_id_](docs/sdks/records/README.md#patch_v2_objects_object_records_record_id_) - Update a record (append multiselect values)
* [put_v2_objects_object_records_record_id_](docs/sdks/records/README.md#put_v2_objects_object_records_record_id_) - Update a record (overwrite multiselect values)
* [delete_v2_objects_object_records_record_id_](docs/sdks/records/README.md#delete_v2_objects_object_records_record_id_) - Delete a record
* [post_v2_objects_object_records_merge](docs/sdks/records/README.md#post_v2_objects_object_records_merge) - Merge two records
* [get_v2_objects_object_records_record_id_attributes_attribute_values](docs/sdks/records/README.md#get_v2_objects_object_records_record_id_attributes_attribute_values) - List record attribute values
* [put_v2_objects_object_records_record_id_attributes_attribute_values](docs/sdks/records/README.md#put_v2_objects_object_records_record_id_attributes_attribute_values) - Write record attribute values
* [get_v2_objects_object_records_record_id_entries](docs/sdks/records/README.md#get_v2_objects_object_records_record_id_entries) - List record entries
* [post_v2_objects_records_search](docs/sdks/records/README.md#post_v2_objects_records_search) - Search records

### [Sequences](docs/sdks/sequences/README.md)

* [post_v2_sequences_unsubscribed_emails](docs/sdks/sequences/README.md#post_v2_sequences_unsubscribed_emails) - Add emails to the unsubscribe list

### [Sql](docs/sdks/sql/README.md)

* [post_v2_sql](docs/sdks/sql/README.md#post_v2_sql) - Query SQL

### [Tasks](docs/sdks/tasks/README.md)

* [get_v2_tasks](docs/sdks/tasks/README.md#get_v2_tasks) - List tasks
* [post_v2_tasks](docs/sdks/tasks/README.md#post_v2_tasks) - Create a task
* [get_v2_tasks_task_id_](docs/sdks/tasks/README.md#get_v2_tasks_task_id_) - Get a task
* [patch_v2_tasks_task_id_](docs/sdks/tasks/README.md#patch_v2_tasks_task_id_) - Update a task
* [delete_v2_tasks_task_id_](docs/sdks/tasks/README.md#delete_v2_tasks_task_id_) - Delete a task

### [Threads](docs/sdks/threads/README.md)

* [get_v2_threads](docs/sdks/threads/README.md#get_v2_threads) - List threads
* [get_v2_threads_thread_id_](docs/sdks/threads/README.md#get_v2_threads_thread_id_) - Get a thread and its comments

### [Transcripts](docs/sdks/transcripts/README.md)

* [get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript](docs/sdks/transcripts/README.md#get_v2_meetings_meeting_id_call_recordings_call_recording_id_transcript) - Deprecated: Get call transcript

### [Webhooks](docs/sdks/webhooks/README.md)

* [get_v2_webhooks](docs/sdks/webhooks/README.md#get_v2_webhooks) - List webhooks
* [post_v2_webhooks](docs/sdks/webhooks/README.md#post_v2_webhooks) - Create a webhook
* [get_v2_webhooks_webhook_id_](docs/sdks/webhooks/README.md#get_v2_webhooks_webhook_id_) - Get a webhook
* [patch_v2_webhooks_webhook_id_](docs/sdks/webhooks/README.md#patch_v2_webhooks_webhook_id_) - Update a webhook
* [delete_v2_webhooks_webhook_id_](docs/sdks/webhooks/README.md#delete_v2_webhooks_webhook_id_) - Delete a webhook

### [WorkspaceMembers](docs/sdks/workspacemembers/README.md)

* [get_v2_workspace_members](docs/sdks/workspacemembers/README.md#get_v2_workspace_members) - List workspace members
* [get_v2_workspace_members_workspace_member_id_](docs/sdks/workspacemembers/README.md#get_v2_workspace_members_workspace_member_id_) - Get a workspace member

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- Start File uploads [file-upload] -->
## File uploads

Certain SDK methods accept file objects as part of a request body or multi-part request. It is possible and typically recommended to upload files as a stream rather than reading the entire contents into memory. This avoids excessive memory consumption and potentially crashing with out-of-memory errors when working with very large files. The following example demonstrates how to attach a file stream to a request.

> [!TIP]
>
> For endpoints that handle file uploads bytes arrays can also be used. However, using streams is recommended for large files.
>

```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.files.post_v2_files_upload(file={
        "file_name": "example.file",
        "content": open("example.file", "rb"),
    }, object="people", record_id="bf071e1f-6035-429d-b874-d83ea64ea13b", parent_folder_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")

    # Handle response
    print(res)

```
<!-- End File uploads [file-upload] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
from attio import SDK
from attio.utils import BackoffStrategy, RetryConfig


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects(,
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    # Handle response
    print(res)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
from attio import SDK
from attio.utils import BackoffStrategy, RetryConfig


with SDK(
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects()

    # Handle response
    print(res)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`SDKError`](./src/attio/errors/sdkerror.py) is the base class for all HTTP error responses. It has the following properties:

| Property           | Type             | Description                                                                             |
| ------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `err.message`      | `str`            | Error message                                                                           |
| `err.status_code`  | `int`            | HTTP response status code eg `404`                                                      |
| `err.headers`      | `httpx.Headers`  | HTTP response headers                                                                   |
| `err.body`         | `str`            | HTTP body. Can be empty string if no body is returned.                                  |
| `err.raw_response` | `httpx.Response` | Raw HTTP response                                                                       |
| `err.data`         |                  | Optional. Some errors may contain structured data. [See Error Classes](#error-classes). |

### Example
```python
from attio import SDK, errors


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:
    res = None
    try:

        res = sdk.objects.post_v2_objects(data={
            "api_slug": "people",
            "singular_noun": "Person",
            "plural_noun": "People",
        })

        # Handle response
        print(res)


    except errors.SDKError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.QuotaExceededError):
            print(e.data.status_code)  # float
            print(e.data.type)  # models.PostV2ObjectsBadRequestType
            print(e.data.code)  # models.PostV2ObjectsCodeQuotaExceeded
            print(e.data.message)  # str
```

### Error Classes
**Primary error:**
* [`SDKError`](./src/attio/errors/sdkerror.py): The base class for HTTP error responses.

<details><summary>Less common errors (175)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.


**Inherit from [`SDKError`](./src/attio/errors/sdkerror.py)**:
* [`QuotaExceededError`](./src/attio/errors/quotaexceedederror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectValidationTypeError`](./src/attio/errors/patchv2objectsobjectvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`DeleteV2ObjectsObjectSystemEditUnauthorizedError`](./src/attio/errors/deletev2objectsobjectsystemeditunauthorizederror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityValidationTypeError`](./src/attio/errors/patchv2activitiesactivityvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`DeleteV2ActivitiesActivitySystemEditUnauthorizedError`](./src/attio/errors/deletev2activitiesactivitysystemeditunauthorizederror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesActivityRecordsQueryFilterError`](./src/attio/errors/postv2activitiesactivityrecordsqueryfiltererror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesActivityRecordsInvalidRequestError`](./src/attio/errors/postv2activitiesactivityrecordsinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsInvalidRequestError`](./src/attio/errors/putv2activitiesactivityrecordsinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityRecordsRecordIDInvalidRequestError`](./src/attio/errors/patchv2activitiesactivityrecordsrecordidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsRecordIDInvalidRequestError`](./src/attio/errors/putv2activitiesactivityrecordsrecordidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesValidationTypeError`](./src/attio/errors/postv2targetidentifierattributesvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeSystemEditUnauthorizedError`](./src/attio/errors/patchv2targetidentifierattributesattributesystemeditunauthorizederror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeOptionsValidationTypeError`](./src/attio/errors/postv2targetidentifierattributesattributeoptionsvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeOptionsOptionInvalidRequestError`](./src/attio/errors/patchv2targetidentifierattributesattributeoptionsoptioninvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeStatusesValidationTypeError`](./src/attio/errors/postv2targetidentifierattributesattributestatusesvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeStatusesStatusInvalidRequestError`](./src/attio/errors/patchv2targetidentifierattributesattributestatusesstatusinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsQueryFilterError`](./src/attio/errors/postv2objectsobjectrecordsqueryfiltererror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsInvalidRequestError`](./src/attio/errors/postv2objectsobjectrecordsinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsInvalidRequestError`](./src/attio/errors/putv2objectsobjectrecordsinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectRecordsRecordIDInvalidRequestError`](./src/attio/errors/patchv2objectsobjectrecordsrecordidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDInvalidRequestError`](./src/attio/errors/putv2objectsobjectrecordsrecordidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`SelfMergeError`](./src/attio/errors/selfmergeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`GetV2ObjectsObjectRecordsRecordIDAttributesAttributeValuesValidationTypeError`](./src/attio/errors/getv2objectsobjectrecordsrecordidattributesattributevaluesvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDAttributesAttributeValuesBadRequestInvalidRequestError`](./src/attio/errors/putv2objectsobjectrecordsrecordidattributesattributevaluesbadrequestinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsRecordsSearchInvalidRequestError`](./src/attio/errors/postv2objectsrecordssearchinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2SQLFilterError`](./src/attio/errors/postv2sqlfiltererror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ListsInvalidRequestError`](./src/attio/errors/postv2listsinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2ListsListInvalidRequestError`](./src/attio/errors/patchv2listslistinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ListsListEntriesInvalidRequestError`](./src/attio/errors/postv2listslistentriesinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesInvalidRequestError`](./src/attio/errors/putv2listslistentriesinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2ListsListEntriesEntryIDInvalidRequestError`](./src/attio/errors/patchv2listslistentriesentryidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesEntryIDInvalidRequestError`](./src/attio/errors/putv2listslistentriesentryidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesEntryIDAttributesAttributeValuesBadRequestInvalidRequestError`](./src/attio/errors/putv2listslistentriesentryidattributesattributevaluesbadrequestinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2TasksInvalidRequestError`](./src/attio/errors/postv2tasksinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2TasksTaskIDInvalidRequestError`](./src/attio/errors/patchv2taskstaskidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2CommentsInvalidRequestError`](./src/attio/errors/postv2commentsinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2SequencesUnsubscribedEmailsValidationTypeError`](./src/attio/errors/postv2sequencesunsubscribedemailsvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2MeetingsValidationTypeError`](./src/attio/errors/postv2meetingsvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PatchV2MeetingsMeetingIDInvalidRequestError`](./src/attio/errors/patchv2meetingsmeetingidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PutV2MeetingsMeetingIDInvalidRequestError`](./src/attio/errors/putv2meetingsmeetingidinvalidrequesterror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`DeleteV2MeetingsMeetingIDSystemEditUnauthorizedError`](./src/attio/errors/deletev2meetingsmeetingidsystemeditunauthorizederror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2MeetingsMeetingIDCallRecordingsValidationTypeError`](./src/attio/errors/postv2meetingsmeetingidcallrecordingsvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2WebhooksValidationTypeError`](./src/attio/errors/postv2webhooksvalidationtypeerror.py): Bad Request. Status code `400`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsUnauthorizedError`](./src/attio/errors/postv2objectsunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectUnauthorizedError`](./src/attio/errors/patchv2objectsobjectunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`DeleteV2ObjectsObjectUnauthorizedError`](./src/attio/errors/deletev2objectsobjectunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesAuthError`](./src/attio/errors/postv2activitiesautherror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityUnauthorizedError`](./src/attio/errors/patchv2activitiesactivityunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`DeleteV2ActivitiesActivityUnauthorizedError`](./src/attio/errors/deletev2activitiesactivityunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesActivityRecordsAuthError`](./src/attio/errors/postv2activitiesactivityrecordsautherror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsAuthError`](./src/attio/errors/putv2activitiesactivityrecordsautherror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityRecordsRecordIDUnauthorizedError`](./src/attio/errors/patchv2activitiesactivityrecordsrecordidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsRecordIDUnauthorizedError`](./src/attio/errors/putv2activitiesactivityrecordsrecordidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`DeleteV2ActivitiesActivityRecordsRecordIDUnauthorizedError`](./src/attio/errors/deletev2activitiesactivityrecordsrecordidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesUnauthorizedError`](./src/attio/errors/postv2targetidentifierattributesunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeUnauthorizedError`](./src/attio/errors/patchv2targetidentifierattributesattributeunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeOptionsUnauthorizedError`](./src/attio/errors/postv2targetidentifierattributesattributeoptionsunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeOptionsOptionUnauthorizedError`](./src/attio/errors/patchv2targetidentifierattributesattributeoptionsoptionunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeStatusesUnauthorizedError`](./src/attio/errors/postv2targetidentifierattributesattributestatusesunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeStatusesStatusUnauthorizedError`](./src/attio/errors/patchv2targetidentifierattributesattributestatusesstatusunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsUnauthorizedError`](./src/attio/errors/postv2objectsobjectrecordsunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsUnauthorizedError`](./src/attio/errors/putv2objectsobjectrecordsunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectRecordsRecordIDUnauthorizedError`](./src/attio/errors/patchv2objectsobjectrecordsrecordidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDUnauthorizedError`](./src/attio/errors/putv2objectsobjectrecordsrecordidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`DeleteV2ObjectsObjectRecordsRecordIDUnauthorizedError`](./src/attio/errors/deletev2objectsobjectrecordsrecordidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsMergeUnauthorizedError`](./src/attio/errors/postv2objectsobjectrecordsmergeunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDAttributesAttributeValuesUnauthorizedError`](./src/attio/errors/putv2objectsobjectrecordsrecordidattributesattributevaluesunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`BillingError`](./src/attio/errors/billingerror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2ListsListEntriesUnauthorizedError`](./src/attio/errors/postv2listslistentriesunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesUnauthorizedError`](./src/attio/errors/putv2listslistentriesunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PatchV2ListsListEntriesEntryIDUnauthorizedError`](./src/attio/errors/patchv2listslistentriesentryidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesEntryIDUnauthorizedError`](./src/attio/errors/putv2listslistentriesentryidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`DeleteV2ListsListEntriesEntryIDUnauthorizedError`](./src/attio/errors/deletev2listslistentriesentryidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesEntryIDAttributesAttributeValuesUnauthorizedError`](./src/attio/errors/putv2listslistentriesentryidattributesattributevaluesunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`DeleteV2CommentsCommentIDUnauthorizedError`](./src/attio/errors/deletev2commentscommentidunauthorizederror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2MeetingsMeetingIDCallRecordingsAuthError`](./src/attio/errors/postv2meetingsmeetingidcallrecordingsautherror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`PostV2FilesUploadAuthError`](./src/attio/errors/postv2filesuploadautherror.py): Forbidden. Status code `403`. Applicable to 1 of 97 methods.*
* [`GetV2ObjectsObjectNotFoundError`](./src/attio/errors/getv2objectsobjectnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectNotFoundError`](./src/attio/errors/patchv2objectsobjectnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2ObjectsObjectNotFoundError`](./src/attio/errors/deletev2objectsobjectnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ObjectsObjectViewsNotFoundError`](./src/attio/errors/getv2objectsobjectviewsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ActivitiesActivityNotFoundError`](./src/attio/errors/getv2activitiesactivitynotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityNotFoundError`](./src/attio/errors/patchv2activitiesactivitynotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2ActivitiesActivityNotFoundError`](./src/attio/errors/deletev2activitiesactivitynotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesActivityRecordsQueryNotFoundError`](./src/attio/errors/postv2activitiesactivityrecordsquerynotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesActivityRecordsNotFoundError`](./src/attio/errors/postv2activitiesactivityrecordsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsNotFoundError`](./src/attio/errors/putv2activitiesactivityrecordsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ActivitiesActivityRecordsRecordIDNotFoundError`](./src/attio/errors/getv2activitiesactivityrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityRecordsRecordIDNotFoundError`](./src/attio/errors/patchv2activitiesactivityrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsRecordIDNotFoundError`](./src/attio/errors/putv2activitiesactivityrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2ActivitiesActivityRecordsRecordIDNotFoundError`](./src/attio/errors/deletev2activitiesactivityrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesNotFoundError`](./src/attio/errors/postv2targetidentifierattributesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2TargetIdentifierAttributesAttributeNotFoundError`](./src/attio/errors/getv2targetidentifierattributesattributenotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeNotFoundError`](./src/attio/errors/patchv2targetidentifierattributesattributenotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2TargetIdentifierAttributesAttributeOptionsNotFoundError`](./src/attio/errors/getv2targetidentifierattributesattributeoptionsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeOptionsNotFoundError`](./src/attio/errors/postv2targetidentifierattributesattributeoptionsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeOptionsOptionNotFoundError`](./src/attio/errors/patchv2targetidentifierattributesattributeoptionsoptionnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2TargetIdentifierAttributesAttributeStatusesNotFoundError`](./src/attio/errors/getv2targetidentifierattributesattributestatusesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeStatusesNotFoundError`](./src/attio/errors/postv2targetidentifierattributesattributestatusesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeStatusesStatusNotFoundError`](./src/attio/errors/patchv2targetidentifierattributesattributestatusesstatusnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsQueryNotFoundError`](./src/attio/errors/postv2objectsobjectrecordsquerynotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsNotFoundError`](./src/attio/errors/postv2objectsobjectrecordsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsNotFoundError`](./src/attio/errors/putv2objectsobjectrecordsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ObjectsObjectRecordsRecordIDInvalidRequestError`](./src/attio/errors/getv2objectsobjectrecordsrecordidinvalidrequesterror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectRecordsRecordIDNotFoundError`](./src/attio/errors/patchv2objectsobjectrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDNotFoundError`](./src/attio/errors/putv2objectsobjectrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2ObjectsObjectRecordsRecordIDNotFoundError`](./src/attio/errors/deletev2objectsobjectrecordsrecordidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsMergeInvalidRequestError`](./src/attio/errors/postv2objectsobjectrecordsmergeinvalidrequesterror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ObjectsObjectRecordsRecordIDAttributesAttributeValuesNotFoundError`](./src/attio/errors/getv2objectsobjectrecordsrecordidattributesattributevaluesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDAttributesAttributeValuesNotFoundInvalidRequestError`](./src/attio/errors/putv2objectsobjectrecordsrecordidattributesattributevaluesnotfoundinvalidrequesterror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ListsNotFoundError`](./src/attio/errors/postv2listsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ListsListNotFoundError`](./src/attio/errors/getv2listslistnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2ListsListNotFoundError`](./src/attio/errors/patchv2listslistnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ListsListViewsNotFoundError`](./src/attio/errors/getv2listslistviewsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ListsListEntriesQueryNotFoundError`](./src/attio/errors/postv2listslistentriesquerynotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ListsListEntriesNotFoundError`](./src/attio/errors/postv2listslistentriesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesNotFoundError`](./src/attio/errors/putv2listslistentriesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ListsListEntriesEntryIDNotFoundError`](./src/attio/errors/getv2listslistentriesentryidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2ListsListEntriesEntryIDNotFoundError`](./src/attio/errors/patchv2listslistentriesentryidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesEntryIDNotFoundError`](./src/attio/errors/putv2listslistentriesentryidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2ListsListEntriesEntryIDNotFoundError`](./src/attio/errors/deletev2listslistentriesentryidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ListsListEntriesEntryIDAttributesAttributeValuesNotFoundError`](./src/attio/errors/getv2listslistentriesentryidattributesattributevaluesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2ListsListEntriesEntryIDAttributesAttributeValuesNotFoundInvalidRequestError`](./src/attio/errors/putv2listslistentriesentryidattributesattributevaluesnotfoundinvalidrequesterror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2WorkspaceMembersWorkspaceMemberIDNotFoundError`](./src/attio/errors/getv2workspacemembersworkspacememberidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2NotesNotFoundError`](./src/attio/errors/getv2notesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2NotesNotFoundError`](./src/attio/errors/postv2notesnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2NotesNoteIDNotFoundError`](./src/attio/errors/getv2notesnoteidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2NotesNoteIDNotFoundError`](./src/attio/errors/patchv2notesnoteidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2NotesNoteIDNotFoundError`](./src/attio/errors/deletev2notesnoteidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2TasksNotFoundError`](./src/attio/errors/postv2tasksnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2TasksTaskIDNotFoundError`](./src/attio/errors/getv2taskstaskidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2TasksTaskIDNotFoundError`](./src/attio/errors/patchv2taskstaskidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2TasksTaskIDNotFoundError`](./src/attio/errors/deletev2taskstaskidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2ThreadsThreadIDNotFoundError`](./src/attio/errors/getv2threadsthreadidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2CommentsCommentIDNotFoundError`](./src/attio/errors/getv2commentscommentidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2CommentsCommentIDNotFoundError`](./src/attio/errors/deletev2commentscommentidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2MeetingsMeetingIDNotFoundError`](./src/attio/errors/getv2meetingsmeetingidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2MeetingsMeetingIDNotFoundError`](./src/attio/errors/patchv2meetingsmeetingidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PutV2MeetingsMeetingIDNotFoundError`](./src/attio/errors/putv2meetingsmeetingidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2MeetingsMeetingIDNotFoundError`](./src/attio/errors/deletev2meetingsmeetingidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2MeetingsMeetingIDCallRecordingsNotFoundError`](./src/attio/errors/postv2meetingsmeetingidcallrecordingsnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2MeetingsMeetingIDCallRecordingsCallRecordingIDNotFoundError`](./src/attio/errors/getv2meetingsmeetingidcallrecordingscallrecordingidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2MeetingsMeetingIDCallRecordingsCallRecordingIDNotFoundError`](./src/attio/errors/deletev2meetingsmeetingidcallrecordingscallrecordingidnotfounderror.py): Call recording not found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2FilesFileIDNotFoundError`](./src/attio/errors/getv2filesfileidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2FilesFileIDNotFoundError`](./src/attio/errors/deletev2filesfileidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`GetV2WebhooksWebhookIDNotFoundError`](./src/attio/errors/getv2webhookswebhookidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PatchV2WebhooksWebhookIDNotFoundError`](./src/attio/errors/patchv2webhookswebhookidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`DeleteV2WebhooksWebhookIDNotFoundError`](./src/attio/errors/deletev2webhookswebhookidnotfounderror.py): Not Found. Status code `404`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsSlugConflictError`](./src/attio/errors/postv2objectsslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectSlugConflictError`](./src/attio/errors/patchv2objectsobjectslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesSlugConflictError`](./src/attio/errors/postv2activitiesslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivitySlugConflictError`](./src/attio/errors/patchv2activitiesactivityslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2ActivitiesActivityRecordsConcurrentWriteConflictError`](./src/attio/errors/postv2activitiesactivityrecordsconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsConcurrentWriteConflictError`](./src/attio/errors/putv2activitiesactivityrecordsconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2ActivitiesActivityRecordsRecordIDConcurrentWriteConflictError`](./src/attio/errors/patchv2activitiesactivityrecordsrecordidconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PutV2ActivitiesActivityRecordsRecordIDConcurrentWriteConflictError`](./src/attio/errors/putv2activitiesactivityrecordsrecordidconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesSlugConflictError`](./src/attio/errors/postv2targetidentifierattributesslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeOptionsSlugConflictError`](./src/attio/errors/postv2targetidentifierattributesattributeoptionsslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeOptionsOptionSlugConflictError`](./src/attio/errors/patchv2targetidentifierattributesattributeoptionsoptionslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2TargetIdentifierAttributesAttributeStatusesSlugConflictError`](./src/attio/errors/postv2targetidentifierattributesattributestatusesslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2TargetIdentifierAttributesAttributeStatusesStatusSlugConflictError`](./src/attio/errors/patchv2targetidentifierattributesattributestatusesstatusslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2ObjectsObjectRecordsConcurrentWriteConflictError`](./src/attio/errors/postv2objectsobjectrecordsconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsConcurrentWriteConflictError`](./src/attio/errors/putv2objectsobjectrecordsconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2ObjectsObjectRecordsRecordIDConcurrentWriteConflictError`](./src/attio/errors/patchv2objectsobjectrecordsrecordidconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PutV2ObjectsObjectRecordsRecordIDConcurrentWriteConflictError`](./src/attio/errors/putv2objectsobjectrecordsrecordidconcurrentwriteconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2ListsSlugConflictError`](./src/attio/errors/postv2listsslugconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2WebhooksUniquenessConflictError`](./src/attio/errors/postv2webhooksuniquenessconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PatchV2WebhooksWebhookIDUniquenessConflictError`](./src/attio/errors/patchv2webhookswebhookiduniquenessconflicterror.py): Conflict. Status code `409`. Applicable to 1 of 97 methods.*
* [`PostV2NotesValidationTypeError`](./src/attio/errors/postv2notesvalidationtypeerror.py): Content Too Large. Status code `413`. Applicable to 1 of 97 methods.*
* [`PatchV2NotesNoteIDValidationTypeError`](./src/attio/errors/patchv2notesnoteidvalidationtypeerror.py): Content Too Large. Status code `413`. Applicable to 1 of 97 methods.*
* [`ResponseValidationError`](./src/attio/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>

\* Check [the method documentation](#available-resources-and-operations) to see if the error is applicable.
<!-- End Error Handling [errors] -->

<!-- Start Server Selection [server] -->
## Server Selection

### Override Server URL Per-Client

The default server can be overridden globally by passing a URL to the `server_url: str` optional parameter when initializing the SDK client instance. For example:
```python
from attio import SDK


with SDK(
    server_url="https://api.attio.com",
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects()

    # Handle response
    print(res)

```
<!-- End Server Selection [server] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from attio import SDK
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = SDK(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from attio import SDK
from attio.httpclient import AsyncHttpClient
import httpx

class CustomClient(AsyncHttpClient):
    client: AsyncHttpClient

    def __init__(self, client: AsyncHttpClient):
        self.client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: Union[
            httpx._types.AuthTypes, httpx._client.UseClientDefault, None
        ] = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: Union[
            bool, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request.headers["Client-Level-Header"] = "added by client"

        return await self.client.send(
            request, stream=stream, auth=auth, follow_redirects=follow_redirects
        )

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: Union[
            httpx._types.TimeoutTypes, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        return self.client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

s = SDK(async_client=CustomClient(httpx.AsyncClient()))
```
### httpx2 (Pydantic's httpx fork)

[httpx2](https://httpx2.pydantic.dev/) is Pydantic's maintained fork of `httpx`. To run this SDK on httpx2, call `alias_httpx()` at your program's entry point, before importing the SDK, so every `import httpx` — including the ones inside the SDK — resolves to `httpx2`:
```python
import httpx2

httpx2.alias_httpx()

from attio import SDK

s = SDK()
```

An SDK can also be generated against httpx2 directly, so it depends on the fork instead of `httpx`, by setting `python.httpClientLibrary: httpx2` in `gen.yaml`.
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `SDK` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
from attio import SDK
def main():

    with SDK(
        oauth2="<YOUR_OAUTH2_HERE>",
    ) as sdk:
        # Rest of application here...


# Or when using async:
async def amain():

    async with SDK(
        oauth2="<YOUR_OAUTH2_HERE>",
    ) as sdk:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from attio import SDK
import logging

logging.basicConfig(level=logging.DEBUG)
s = SDK(debug_logger=logging.getLogger("attio"))
```
<!-- End Debugging [debug] -->

## Troubleshooting

### 401 or 403 responses

- Confirm the OAuth2 token is valid and not expired.
- Confirm the token includes the scopes required by the endpoint (scope requirements are listed in each operation doc).
- Verify you are sending the token through `SDK(oauth2=...)`.

### Validation errors on create/update

- Attribute keys and value shapes must match your Attio workspace schema.
- Check the operation docs for the exact request model and examples.
- Start from a simple payload, then add fields incrementally.

### Async usage issues

- Use async methods (ending in `_async`) inside `async with SDK(...)`.
- Do not mix sync and async clients in the same call path.

<!-- Placeholder for Future Speakeasy SDK Sections -->
