# PatchV2ObjectsObjectViewsViewIDTypeRequest

How the view shows records. A change to `kanban` requires `kanban.status_attribute`. A change to `table` removes the kanban settings.

## Example Usage

```python
from attio.models import PatchV2ObjectsObjectViewsViewIDTypeRequest
value: PatchV2ObjectsObjectViewsViewIDTypeRequest = "table"
```


## Values

- `"table"`
- `"kanban"`
