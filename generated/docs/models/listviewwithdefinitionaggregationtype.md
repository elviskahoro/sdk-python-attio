# ListViewWithDefinitionAggregationType

The calculation. Each field can count and give the percentage of records where it is empty or not empty. `sum`, `mean`, `min` and `max` are only for number, currency and rating attributes.

## Example Usage

```python
from attio.models import ListViewWithDefinitionAggregationType
value: ListViewWithDefinitionAggregationType = "count_empty"
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
