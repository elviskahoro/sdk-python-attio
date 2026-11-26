# Op

The operator. `in` takes a non-empty array and matches when one `eq` condition with one of its values matches. Responses never contain `in`.

## Example Usage

```python
from attio.models import Op
value: Op = "eq"
```


## Values

- `"eq"`
- `"not_eq"`
- `"lt"`
- `"gt"`
- `"contains"`
- `"not_contains"`
- `"starts_with"`
- `"ends_with"`
- `"empty"`
- `"not_empty"`
- `"entered"`
- `"not_entered"`
- `"in"`
