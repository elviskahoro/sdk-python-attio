# GetV2EmailsRequest


## Fields

| Field                            | Type                             | Required                         | Description                      | Example                          |
| -------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- |
| `limit`                          | *Optional[int]*                  | :heavy_minus_sign:               | N/A                              | 25                               |
| `cursor`                         | *Optional[str]*                  | :heavy_minus_sign:               | N/A                              |                                  |
| `linked_object`                  | *Optional[str]*                  | :heavy_minus_sign:               | N/A                              |                                  |
| `linked_record_ids`              | *Optional[str]*                  | :heavy_minus_sign:               | N/A                              |                                  |
| `participants`                   | *Optional[str]*                  | :heavy_minus_sign:               | N/A                              |                                  |
| `domain`                         | *Optional[str]*                  | :heavy_minus_sign:               | N/A                              | fundstack.com                    |
| `sent_after`                     | *OptionalNullable[str]*          | :heavy_minus_sign:               | N/A                              |                                  |
| `sent_before`                    | *OptionalNullable[str]*          | :heavy_minus_sign:               | N/A                              |                                  |
| `exclude_automated_participants` | *Optional[bool]*                 | :heavy_minus_sign:               | N/A                              | false                            |