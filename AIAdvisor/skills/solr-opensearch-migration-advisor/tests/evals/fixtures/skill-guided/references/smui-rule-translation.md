# SMUI Rule Export Format and Translation

## Export Format
SMUI exports Querqy rules as **plain text** (not JSON). Each rule block
starts with an input term, followed by indented rule lines:

```
laptop =>
  SYNONYM: notebook
  SYNONYM: portable computer
  UP(100): brand:Apple
  DOWN(50): brand:Generic
  FILTER: * category:electronics

smartphone =>
  SYNONYM: mobile phone
  SYNONYM: cell phone
  DELETE: cheap
  UP(200): condition:new
```

## Translation to OpenSearch

### SYNONYM rules → synonym token filter
```json
{
  "settings": {
    "analysis": {
      "filter": {
        "smui_synonyms": {
          "type": "synonym",
          "synonyms": [
            "laptop, notebook, portable computer",
            "smartphone, mobile phone, cell phone"
          ]
        }
      }
    }
  }
}
```

### UP rules → bool.should with boost
```json
{ "should": [{ "term": { "brand": { "value": "Apple", "boost": 100 }}}] }
```

### DOWN rules → boosting query with negative_boost
```json
{
  "boosting": {
    "positive": { "match_all": {} },
    "negative": { "term": { "brand": "Generic" }},
    "negative_boost": 0.5
  }
}
```

### FILTER rules → bool.filter
```json
{ "filter": [{ "term": { "category": "electronics" }}] }
```

### DELETE rules → application-layer preprocessing
No native OpenSearch equivalent. Strip the term from the query string
before building the OpenSearch DSL.
