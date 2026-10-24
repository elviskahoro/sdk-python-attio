# GetV2TasksSort

Optionally sort the results. "created_at:asc" returns oldest results first, "created_at:desc" returns the newest results first. "completed_at:asc" and "completed_at:desc" sort by completion time. With "completed_at:asc", incomplete tasks (no completion date) appear first, followed by completed tasks oldest-first. With "completed_at:desc", completed tasks appear first (newest-first), followed by incomplete tasks. To exclude incomplete tasks, filter by is_completed. If unspecified, defaults to "created_at:asc" (oldest results first).

## Example Usage

```python
from attio.models import GetV2TasksSort
value: GetV2TasksSort = "created_at:asc"
```


## Values

- `"created_at:asc"`
- `"created_at:desc"`
- `"completed_at:asc"`
- `"completed_at:desc"`
