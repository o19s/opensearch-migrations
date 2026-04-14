# Querqy OpenSearch Plugin: Rewriter REST API

## Registering a Rewriter
Rewriters are registered via PUT to the `_querqy/rewriter` endpoint:

```
PUT /_querqy/rewriter/common_rules_rewriter
{
  "class": "querqy.rewrite.commonrules.CommonRulesRewriter",
  "config": {
    "rules": "laptop =>\n  SYNONYM: notebook\n  UP(100): brand:Apple\n\nsmartphone =>\n  SYNONYM: mobile phone\n  DOWN(50): brand:Generic"
  }
}
```

## Rewriter Types
| Rewriter | Class |
|----------|-------|
| Common Rules | `querqy.rewrite.commonrules.CommonRulesRewriter` |
| Replace | `querqy.rewrite.replace.ReplaceRewriter` |
| Word Break | `querqy.rewrite.wordbreak.WordBreakCompoundRewriter` |
| Number Unit | `querqy.rewrite.numberunit.NumberUnitRewriter` |

## Chaining Rewriters
Specify multiple rewriters in the search request:
```json
{
  "query": {
    "querqy": {
      "matching_query": { "query": "laptop" },
      "query_fields": ["title^3", "description"],
      "rewriters": ["common_rules_rewriter", "replace_rewriter"]
    }
  }
}
```

## Key Differences from Solr
- Solr: rewriters configured in `querqy.xml` (XML), deployed via config reload
- OpenSearch: rewriters registered via REST API (JSON), stored in cluster state
- Solr: rewriter chain order defined in `querqy.xml`
- OpenSearch: chain order defined per-query in the `rewriters` array
