# positionIncrementGap: Solr vs OpenSearch

## The Problem
Multi-valued text fields (e.g., `tags: ["new york", "city guide"]`) can
produce false phrase matches across value boundaries. Without a position
gap, a phrase query for "york city" would match because "york" ends
value 1 and "city" starts value 2.

## Solr
Set on the **fieldType** definition (camelCase):
```xml
<fieldType name="text_general" class="solr.TextField"
           positionIncrementGap="100">
```

## OpenSearch
Set on the **field mapping** (snake_case), NOT on the analyzer:
```json
{
  "mappings": {
    "properties": {
      "tags": {
        "type": "text",
        "position_increment_gap": 100
      }
    }
  }
}
```

## Key Differences
| | Solr | OpenSearch |
|---|---|---|
| Parameter name | `positionIncrementGap` (camelCase) | `position_increment_gap` (snake_case) |
| Where it's set | On the fieldType | On the field mapping |
| Default value | 0 | 100 |

**Important**: OpenSearch defaults to 100 (unlike Solr's default of 0),
so the migration may not require explicit configuration unless Solr uses
a non-standard value. But if Solr explicitly sets `positionIncrementGap=0`
(allowing cross-value phrase matches), you must explicitly set
`position_increment_gap: 0` in OpenSearch to preserve the same behavior.
