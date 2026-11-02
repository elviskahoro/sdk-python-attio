# EnforcementLevelResponse

`protected`: emails and calendar events are hidden unless at least one participant is not on the workspace blocklist. `blocked`: they are hidden even when other participants are included.

## Example Usage

```python
from attio.models import EnforcementLevelResponse
value: EnforcementLevelResponse = "protected"
```


## Values

- `"protected"`
- `"blocked"`
