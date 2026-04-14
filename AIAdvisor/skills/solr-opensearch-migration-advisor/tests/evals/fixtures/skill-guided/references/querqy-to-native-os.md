# Querqy Rule Translation to Native OpenSearch

## AWS OpenSearch Service Limitation
Querqy plugin CANNOT be installed on AWS OpenSearch Service. AWS does not
support custom plugin installation on the managed service. Self-managed
OpenSearch clusters CAN use the Querqy community plugin.

## Rule-by-Rule Translation

### UP (boost)
Querqy: `laptop => UP(100): brand:Apple`
OpenSearch: `bool.should` clause with `boost`:
```json
{ "should": [{ "term": { "brand": { "value": "Apple", "boost": 100 } } }] }
```

### DOWN (penalize)
Querqy: `laptop => DOWN(50): brand:Generic`
OpenSearch: Negative boost via `boosting` query:
```json
{
  "boosting": {
    "positive": { "match": { "title": "laptop" } },
    "negative": { "term": { "brand": "Generic" } },
    "negative_boost": 0.5
  }
}
```

### FILTER (add filter)
Querqy: `laptop => FILTER: category:electronics`
OpenSearch: `bool.filter` clause:
```json
{ "filter": [{ "term": { "category": "electronics" } }] }
```

### DELETE (remove term from query)
Querqy: `cheap laptop => DELETE: cheap`
OpenSearch: Application-layer query rewriting — strip the term before
building the query. No native OpenSearch equivalent.

### SYNONYM (expand query)
Querqy: `laptop => SYNONYM: notebook`
OpenSearch: Synonym token filter in the analyzer chain:
```json
{
  "filter": {
    "query_synonyms": {
      "type": "synonym",
      "synonyms": ["laptop, notebook"]
    }
  }
}
```
Or use `bool.should` with the synonym term for query-time expansion.
