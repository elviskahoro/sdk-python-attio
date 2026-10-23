# WorkspaceMemberAccess


## Fields

| Field                                                       | Type                                                        | Required                                                    | Description                                                 | Example                                                     |
| ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| `workspace_member_id`                                       | *str*                                                       | :heavy_check_mark:                                          | A UUID to identify the workspace member to grant access to. | 50cf242c-7fa3-4cad-87d0-75b1af71c57b                        |
| `level`                                                     | [models.Level](../models/level.md)                          | :heavy_check_mark:                                          | The level of access to the list.                            | read-and-write                                              |