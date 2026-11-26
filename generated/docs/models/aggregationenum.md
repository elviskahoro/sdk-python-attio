# AggregationEnum

The calculation that the column footer of a table view shows, on the field that the column shows. Omitted when the column has none. Not allowed on a kanban view, which uses `kanban.aggregation`. In an update, an omitted aggregation keeps the aggregation of a column with the same attribute and field, and `null` removes it. Each field can count and give the percentage of records where it is empty or not empty. `sum`, `mean`, `min` and `max` are only for number, currency and rating attributes.

## Example Usage

```python
from attio.models import AggregationEnum
value: AggregationEnum = "count_empty"
```


## Values

- `"count_empty"`
- `"count_not_empty"`
- `"percent_empty"`
- `"percent_not_empty"`
- `"sum"`
- `"mean"`
- `"max"`
- `"min"`
