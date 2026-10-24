# GetV2WebhooksWebhookIDStatus

The state of the webhook. Webhooks marked as active and degraded will receive events, inactive ones will not. If a webhook remains in the degraded state for 7 days, it will be marked inactive.

## Example Usage

```python
from attio.models import GetV2WebhooksWebhookIDStatus
value: GetV2WebhooksWebhookIDStatus = "active"
```


## Values

- `"active"`
- `"degraded"`
- `"inactive"`
