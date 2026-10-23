# RecordReference

Configuration available for attributes of type "record-reference".


## Fields

| Field                                                                                                                              | Type                                                                                                                               | Required                                                                                                                           | Description                                                                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `allowed_object_ids`                                                                                                               | List[*str*]                                                                                                                        | :heavy_check_mark:                                                                                                                 | A list of UUIDs to indicate which objects records are allowed to belong to. Leave empty to to allow records from all object types. |