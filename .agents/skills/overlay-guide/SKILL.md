---
name: overlay-guide
description: Reference guide for creating and modifying OpenAPI Overlays used to customize the Attio API spec before SDK generation with Speakeasy
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash
---

# OpenAPI Overlay Guide

Reference for creating and using OpenAPI Overlays to customize the API specification without modifying the original OpenAPI document. Overlays follow the [OpenAPI Overlay Specification v1.0.0](https://github.com/OAI/Overlay-Specification).

> **Always regenerate after editing the overlay** (`ci/regenerate_host.sh` or
> `uv run python ci/pipeline.py generate --no-fetch`) and commit the regenerated
> SDK in the same PR as the overlay change.

## Why Use Overlays?

- **Separation of concerns**: Keep API definition separate from SDK-specific customizations
- **Non-invasive**: Apply modifications without editing the upstream OpenAPI document
- **Version control**: Track customizations independently from the core API spec

## Overlay Document Structure

Every overlay document contains three required sections:

```yaml
overlay: 1.0.0              # Overlay specification version
info:                        # Metadata about the overlay
  title: "Description"
  version: "0.0.1"
actions:                     # Array of modifications to apply
  - target: "JSONPath"
    update: {}
```

Each action contains:
- **target** (required): JSONPath expression identifying where to apply changes
- **description** (optional): Explanation of the action
- **update** (optional): Properties and values to merge with target objects
- **remove** (optional): Boolean to remove the target object (default: false)

## JSONPath Expressions

| Expression | Description |
|------------|-------------|
| `$.info.title` | Select the title field of the info object |
| `$.servers[0].url` | Select the URL of the first server |
| `$.paths['/drinks'].get` | Select the GET operation on /drinks path |
| `$.paths.*.*` | Select all operations across all paths |
| `$.paths..parameters[?(@.in=='query')]` | Select all query parameters |
| `$.components.schemas.Drink` | Select the Drink schema |
| `$.paths.*[?(@.operationId == 'listUsers')]` | Select operations by operationId |

### Target Selection Guidelines

| Update Type | Target Object |
|-------------|---------------|
| Update primitive value (string, number, boolean) | The containing object |
| Update an object | The object itself |
| Update an array | The array itself |
| Add new property to object | The object itself |
| Remove property/item | The object/array itself |

## Common Use Cases

### 1. Method Name Overrides

```yaml
actions:
  - target: $.paths.*.*[?(@.operationId == 'generateCodeSamplePreviewAsync')]
    update:
      x-speakeasy-name-override: generateCodeSamplePreviewAsynchronous
```

### 2. Adding Code Samples

```yaml
actions:
  - target: $["paths"]["/v1/artifacts/namespaces"]["get"]
    update:
      x-codeSamples:
        - lang: python
          label: getNamespaces
          source: |-
            from sdk import Client
            client = Client(api_key="<KEY>")
            res = client.artifacts.get_namespaces()
```

### 3. Hiding Internal APIs

```yaml
actions:
  - target: "$.paths['/internal/staff']"
    update:
      x-internal: true
```

### 4. Standardizing Configurations

Remove operation-level server and security configs to use global defaults:

```yaml
actions:
  - target: $.paths.*.*.servers
    remove: true
  - target: $.paths.*.*.security
    remove: true
```

### 5. Adding Speakeasy Extensions

```yaml
actions:
  - target: "$.components.schemas.Order"
    update:
      x-speakeasy-entity: Order
```

### 6. Enhancing Schema Definitions

```yaml
actions:
  - target: "$.components.schemas.Drink"
    update:
      properties:
        type:
          type: string
          description: "Type of drink, e.g., 'cocktail', 'beer'."
```

## Speakeasy-Specific Extensions

- `x-speakeasy-name-override`: Override generated method/class names
- `x-speakeasy-entity`: Enable Terraform provider support
- `x-speakeasy-entity-operation`: Mark operations for entity support
- `x-internal`: Hide endpoints from public SDK generation
- `x-codeSamples`: Add language-specific code examples
- `x-speakeasy-retries`: Configure retry behavior
- `x-speakeasy-pagination`: Configure pagination handling

## CLI Commands

```bash
# Compare two specs to generate an overlay
speakeasy overlay compare --before=./openapi_original.yaml --after=./openapi.yaml > overlay.yaml

# Validate an overlay
speakeasy overlay validate -o overlay.yaml

# Apply an overlay to produce a combined spec
speakeasy overlay apply -s openapi.yaml -o overlay.yaml > combined.yaml

# Add overlay to Speakeasy workflow
speakeasy configure sources
```

## This Project

The overlay file is at `overlay.yaml` in the project root. It currently handles:
- **Timestamp value fields**: Removes `format` fields and changes examples/descriptions so Speakeasy generates `str` instead of `date` types
- **`list` parameter renaming**: Renames `list` to `list_id` via `x-speakeasy-name-override` to avoid Python built-in conflicts

The overlay is referenced in `.speakeasy/workflow.yaml` and applied automatically during `speakeasy run`.

## Best Practices

1. Use descriptive titles and descriptions in each overlay and action
2. Version your overlays alongside your API versions
3. Test JSONPath expressions with [jsonpath.com](https://jsonpath.com/)
4. Keep overlays focused — separate concerns into separate overlays
5. Validate before applying: `speakeasy overlay validate`
6. Try the visual playground at [overlay.speakeasy.com](https://overlay.speakeasy.com/)

## Troubleshooting

- **JSONPath not matching**: Validate expressions using online tools or test on a sample of the spec
- **Overlay not applying**: Ensure `target` points to the correct location and format follows the spec
- **Conflicts between actions**: Actions are applied in order; later actions can conflict with earlier ones
- **`oneOf` index drift**: The indices in `overlay.yaml` are positional — if Attio reorders schema union types, update the index numbers
