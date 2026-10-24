# PostV2TargetIdentifierAttributesDisplayType

How the currency should be displayed across the app. "code" will display the ISO currency code e.g. "USD", "name" will display the localized currency name e.g. "British pound", "narrowSymbol" will display "$1" instead of "US$1" and "symbol" will display a localized currency symbol such as "$".

## Example Usage

```python
from attio.models import PostV2TargetIdentifierAttributesDisplayType
value: PostV2TargetIdentifierAttributesDisplayType = "code"
```


## Values

- `"code"`
- `"name"`
- `"narrowSymbol"`
- `"symbol"`
