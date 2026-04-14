# Querqy infoLogging: Seeing Which Rules Fired

## Solr
In Solr, add `querqy.infoLogging=on` to the request parameters:
```
/solr/collection/select?q=laptop&querqy.infoLogging=on
```
Response includes a `querqy.infoLog` section showing which rewriters
matched and what actions they took.

## OpenSearch Querqy Plugin
The OpenSearch Querqy plugin supports the same concept via the
`info_logging` parameter in the querqy query clause:

```json
{
  "query": {
    "querqy": {
      "matching_query": { "query": "laptop" },
      "query_fields": ["title^3", "description"],
      "rewriters": ["common_rules"],
      "info_logging": {
        "id": "my-query-debug-id"
      }
    }
  }
}
```

The response includes a `querqy_decorations` array in each hit's
`matched_queries` showing which rules fired:

```json
{
  "hits": {
    "hits": [{
      "matched_queries": ["common_rules:laptop=>UP(100):brand:Apple"]
    }]
  }
}
```

## Key Difference
- Solr: `querqy.infoLogging=on` as a request parameter
- OpenSearch: `info_logging: { "id": "..." }` inside the querqy query body
- Both return decoration data showing rule matches, but the response
  format differs (Solr uses `querqy.infoLog`, OpenSearch uses
  `querqy_decorations` in matched_queries)
