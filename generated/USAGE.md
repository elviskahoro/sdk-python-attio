<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
from attio import SDK


with SDK(
    oauth2="<YOUR_OAUTH2_HERE>",
) as sdk:

    res = sdk.objects.get_v2_objects()

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from attio import SDK

async def main():

    async with SDK(
        oauth2="<YOUR_OAUTH2_HERE>",
    ) as sdk:

        res = await sdk.objects.get_v2_objects_async()

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->