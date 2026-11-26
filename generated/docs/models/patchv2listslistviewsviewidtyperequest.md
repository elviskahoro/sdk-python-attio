# PatchV2ListsListViewsViewIDTypeRequest

How the view shows records. A change to `kanban` requires `kanban.status_attribute`. A change to `table` removes the kanban settings.

## Example Usage

```python
from attio.models import PatchV2ListsListViewsViewIDTypeRequest
value: PatchV2ListsListViewsViewIDTypeRequest = "table"
```


## Values

- `"table"`
- `"kanban"`
