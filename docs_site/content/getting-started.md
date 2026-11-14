# Getting started

## Installation

```bash
pip install attio   # or: uv add attio
```

## Authentication

Create an access token in Attio and pass it as `oauth2`:

```python
import os
from attio import SDK

with SDK(oauth2=os.environ["ATTIO_API_KEY"]) as sdk:
    ...
```

## Examples

```python
from attio import SDK

with SDK(oauth2="<token>") as sdk:
    res = sdk.records.post_v2_objects_object_records_query(object="people")
    print(res)
```

More workflows are in the [repository README](https://github.com/elviskahoro/sdk-python-attio#common-workflows).

## CLI

```bash
uvx --from attio attio --help
```

See the [README CLI section](https://github.com/elviskahoro/sdk-python-attio#standalone-cli) for commands and credentials.
