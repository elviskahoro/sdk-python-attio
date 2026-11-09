# GetV2WorkspaceBlocklistAddressesEnforcementLevel

`protected`: emails and calendar events are hidden unless at least one participant is not on the workspace blocklist. `blocked`: they are hidden even when other participants are included.

## Example Usage

```python
from attio.models import GetV2WorkspaceBlocklistAddressesEnforcementLevel
value: GetV2WorkspaceBlocklistAddressesEnforcementLevel = "protected"
```


## Values

- `"protected"`
- `"blocked"`
