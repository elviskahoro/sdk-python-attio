# PostV2WebhooksStatus

The state of the webhook. Webhooks marked as active and degraded will receive events, inactive ones will not. If a webhook remains in the degraded state for 7 days, it will be marked inactive.

## Example Usage

```python
from attio.models import PostV2WebhooksStatus
value: PostV2WebhooksStatus = "active"
```


## Values

- `"active"`
- `"degraded"`
- `"inactive"`
