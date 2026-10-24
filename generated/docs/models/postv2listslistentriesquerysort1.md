# PostV2ListsListEntriesQuerySort1

Sort by attribute


## Fields

| Field                                                                                              | Type                                                                                               | Required                                                                                           | Description                                                                                        |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `direction`                                                                                        | [models.PostV2ListsListEntriesQueryDirection1](../models/postv2listslistentriesquerydirection1.md) | :heavy_check_mark:                                                                                 | The direction to sort the results by.                                                              |
| `attribute`                                                                                        | *str*                                                                                              | :heavy_check_mark:                                                                                 | A slug or ID to identify the attribute to sort by.                                                 |
| `field`                                                                                            | *Optional[str]*                                                                                    | :heavy_minus_sign:                                                                                 | Which field on the value to sort by e.g. "last_name" on a name value.                              |