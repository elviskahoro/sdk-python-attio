# PostV2MeetingsMeetingIDCallRecordingsStatus

The status of the call recording. When a call recording is first created, it will have a status of `PROCESSING`. Once the recording is ready, it will transition to `COMPLETED`. If the recording fails for any reason, the status will be `FAILED`.

## Example Usage

```python
from attio.models import PostV2MeetingsMeetingIDCallRecordingsStatus
value: PostV2MeetingsMeetingIDCallRecordingsStatus = "processing"
```


## Values

- `"processing"`
- `"completed"`
- `"failed"`
