# PostV2SQLFilterError

Bad Request


## Fields

| Field                                              | Type                                               | Required                                           | Description                                        | Example                                            |
| -------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------- |
| `status_code`                                      | *float*                                            | :heavy_check_mark:                                 | N/A                                                |                                                    |
| `type`                                             | [models.PostV2SQLType](../models/postv2sqltype.md) | :heavy_check_mark:                                 | N/A                                                |                                                    |
| `code`                                             | [models.PostV2SQLCode](../models/postv2sqlcode.md) | :heavy_check_mark:                                 | N/A                                                |                                                    |
| `message`                                          | *str*                                              | :heavy_check_mark:                                 | N/A                                                | SQL syntax error.                                  |