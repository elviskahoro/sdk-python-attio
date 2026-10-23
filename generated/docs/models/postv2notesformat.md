# PostV2NotesFormat

Specify the format for the note's content. Choose from:
- `plaintext`: Standard text format where `\n` signifies a new line.
- `markdown`: Enables rich text formatting using a subset of Markdown syntax:
  - **Headings**: Levels 1-3 (`#`, `##`, `###`).
  - **Lists**: Unordered (`-`, `*`, `+`) and ordered (`1.`, `2.`).
  - **Text styles**: Bold (`**bold**` or `__bold__`), italic (`*italic*` or `_italic_`), strikethrough (`~~strikethrough~~`), and highlight (`==highlighted==`).
  - **Links**: Standard Markdown links (`[link text](https://example.com)`).

  *Note: While the Attio interface supports image embeds, they cannot currently be added or retrieved via the API's markdown format.*

## Example Usage

```python
from attio.models import PostV2NotesFormat
value: PostV2NotesFormat = "plaintext"
```


## Values

- `"plaintext"`
- `"markdown"`
