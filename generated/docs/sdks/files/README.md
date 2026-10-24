# Files

## Overview

Files are documents and folders linked to records, stored either in Attio or connected via external storage providers.

### Available Operations

* [get_v2_files](#get_v2_files) - List files
* [post_v2_files](#post_v2_files) - Create a folder
* [post_v2_files_upload](#post_v2_files_upload) - Upload a file
* [get_v2_files_file_id_](#get_v2_files_file_id_) - Get a file
* [delete_v2_files_file_id_](#delete_v2_files_file_id_) - Delete a file
* [get_v2_files_file_id_download](#get_v2_files_file_id_download) - Download a file

## get_v2_files

Lists internal files, externally connected files and folders for a specific record. Use the `object` and `record_id` query parameters to specify the record. Optional query parameters may be provided to filter results by storage provider or parent folder.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `object_configuration:read`, `record_permission:read`, `file:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/files" method="get" path="/v2/files" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.files.get_v2_files(object="<value>", record_id="7e76e3c7-d094-4620-b8c3-0ec424086010", limit=50)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                               | Type                                                                                    | Required                                                                                | Description                                                                             | Example                                                                                 |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `object`                                                                                | *str*                                                                                   | :heavy_check_mark:                                                                      | N/A                                                                                     |                                                                                         |
| `record_id`                                                                             | *str*                                                                                   | :heavy_check_mark:                                                                      | N/A                                                                                     |                                                                                         |
| `storage_provider`                                                                      | [Optional[models.GetV2FilesStorageProvider]](../../models/getv2filesstorageprovider.md) | :heavy_minus_sign:                                                                      | Filter results by storage provider.                                                     |                                                                                         |
| `parent_folder_id`                                                                      | *Optional[str]*                                                                         | :heavy_minus_sign:                                                                      | N/A                                                                                     |                                                                                         |
| `limit`                                                                                 | *Optional[int]*                                                                         | :heavy_minus_sign:                                                                      | N/A                                                                                     | 50                                                                                      |
| `cursor`                                                                                | *Optional[str]*                                                                         | :heavy_minus_sign:                                                                      | N/A                                                                                     |                                                                                         |
| `retries`                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                        | :heavy_minus_sign:                                                                      | Configuration to override the default retry behavior of the client.                     |                                                                                         |

### Response

**[models.GetV2FilesResponse](../../models/getv2filesresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_files

Creates a native folder entry or a connected file/folder entry on an object record.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `file:read-write`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/files" method="post" path="/v2/files" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.files.post_v2_files(request={
        "object": "people",
        "record_id": "bf071e1f-6035-429d-b874-d83ea64ea13b",
        "storage_provider": "google-drive",
        "external_provider_file_id": "01ISGXZ5BRAMVD7SEPXNCYS4XGKT3YTOKQ",
        "file_type": "connected-file",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `request`                                                           | [models.PostV2FilesRequest](../../models/postv2filesrequest.md)     | :heavy_check_mark:                                                  | The request object to use for the request.                          |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PostV2FilesResponse](../../models/postv2filesresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |

## post_v2_files_upload

Uploads a file to native Attio storage for a record. Send multipart/form-data with a single binary field named `file` together with the body fields `object`, `record_id`, and optional `parent_folder_id`. Maximum file size is 50 MB.

This endpoint is rate limited to 1 request per second.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `file:read-write`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v2/files/upload" method="post" path="/v2/files/upload" -->
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

### Parameters

| Parameter                                                             | Type                                                                  | Required                                                              | Description                                                           | Example                                                               |
| --------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `file`                                                                | [models.PostV2FilesUploadFile](../../models/postv2filesuploadfile.md) | :heavy_check_mark:                                                    | The file to upload.                                                   |                                                                       |
| `object`                                                              | *str*                                                                 | :heavy_check_mark:                                                    | The object slug or ID.                                                | people                                                                |
| `record_id`                                                           | *str*                                                                 | :heavy_check_mark:                                                    | The ID of the record to upload the file to.                           | bf071e1f-6035-429d-b874-d83ea64ea13b                                  |
| `parent_folder_id`                                                    | *Optional[str]*                                                       | :heavy_minus_sign:                                                    | Optional parent folder ID. Omit to upload to the root folder.         | a1b2c3d4-e5f6-7890-abcd-ef1234567890                                  |
| `retries`                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)      | :heavy_minus_sign:                                                    | Configuration to override the default retry behavior of the client.   |                                                                       |

### Response

**[models.PostV2FilesUploadResponse](../../models/postv2filesuploadresponse.md)**

### Errors

| Error Type                        | Status Code                       | Content Type                      |
| --------------------------------- | --------------------------------- | --------------------------------- |
| errors.PostV2FilesUploadAuthError | 403                               | application/json                  |
| errors.SDKDefaultError            | 4XX, 5XX                          | \*/\*                             |

## get_v2_files_file_id_

Get a single file entry by ID.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `file:read`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/files/{file_id}" method="get" path="/v2/files/{file_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.files.get_v2_files_file_id_(file_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `file_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | a1b2c3d4-e5f6-7890-abcd-ef1234567890                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.GetV2FilesFileIDResponse](../../models/getv2filesfileidresponse.md)**

### Errors

| Error Type                           | Status Code                          | Content Type                         |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |
| errors.GetV2FilesFileIDNotFoundError | 404                                  | application/json                     |
| errors.SDKDefaultError               | 4XX, 5XX                             | \*/\*                                |

## delete_v2_files_file_id_

Delete a single file by ID. Deleting a folder will delete all of its descendants.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `file:read-write`, `object_configuration:read`, `record_permission:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_/v2/files/{file_id}" method="delete" path="/v2/files/{file_id}" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.files.delete_v2_files_file_id_(file_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `file_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 | a1b2c3d4-e5f6-7890-abcd-ef1234567890                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.DeleteV2FilesFileIDResponse](../../models/deletev2filesfileidresponse.md)**

### Errors

| Error Type                              | Status Code                             | Content Type                            |
| --------------------------------------- | --------------------------------------- | --------------------------------------- |
| errors.DeleteV2FilesFileIDNotFoundError | 404                                     | application/json                        |
| errors.SDKDefaultError                  | 4XX, 5XX                                | \*/\*                                   |

## get_v2_files_file_id_download

Downloads a file by redirecting to a signed URL.

This endpoint is in beta. We will aim to avoid breaking changes, but small updates may be made as we roll out to more users.

Required scopes: `object_configuration:read`, `record_permission:read`, `file:read`.

Supported token levels: `workspace`, `user`.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_/v2/files/{file_id}/download" method="get" path="/v2/files/{file_id}/download" -->
```python
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.files.get_v2_files_file_id_download(file_id="97de9380-4280-4233-9bf3-e41cc1bc2101")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `file_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.GetV2FilesFileIDDownloadResponse](../../models/getv2filesfileiddownloadresponse.md)**

### Errors

| Error Type             | Status Code            | Content Type           |
| ---------------------- | ---------------------- | ---------------------- |
| errors.SDKDefaultError | 4XX, 5XX               | \*/\*                  |