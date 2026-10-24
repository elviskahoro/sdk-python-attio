# AccessLevel

Whether the workspace member is suspended or not and what level of privileges they have inside the workspace. We do not delete workspace members so that you can successfully attribute past actions to suspended workspace members.

## Example Usage

```python
from attio.models import AccessLevel
value: AccessLevel = "admin"
```


## Values

- `"admin"`
- `"member"`
- `"suspended"`
