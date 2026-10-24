# WorkspaceAccess

The level of access granted to all members of the workspace for this list. `null` values represent a private list that only grants access to specific workspace members via the `workspace_member_access` property.

## Example Usage

```python
from attio.models import WorkspaceAccess
value: WorkspaceAccess = "full-access"
```


## Values

- `"full-access"`
- `"read-and-write"`
- `"read-only"`
