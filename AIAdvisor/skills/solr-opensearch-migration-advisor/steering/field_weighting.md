# Solr to OpenSearch Field Weighting Steering

## Overview
Translate Solr eDisMax field boosting to OpenSearch multi-field queries.
Field weighting is central to media search where title, cast, director,
and plot carry different relevance signals.

## Key Conversions
- `qf=title^10 overview^5 cast^3` → `multi_match` with `fields: ["title^10", "overview^5", "cast^3"]`.
- `pf=title^15 overview^8` → separate `multi_match` with `type: "phrase"` in a `bool.should` clause.
- `pf2` / `pf3` (bigram/trigram phrase) → additional phrase `multi_match` queries with `slop`.
- `bf` (boost function) → `function_score` wrapper with `field_value_factor` or `script_score`.
- `bq` (boost query) → additional `should` clause in `bool` query.

## Multi-Match Types
- `type: "best_fields"` — default, scores by best matching field. Good for distinct fields (title vs overview).
- `type: "cross_fields"` — treats multiple fields as one logical field. Good when fields share the same analyzer.
- `type: "combined_fields"` — similar to cross_fields but uses BM25 across fields. Best for same-analyzer text fields (title, overview, tagline).
- `type: "phrase"` — matches the full query as a phrase. Use for `pf` translation.

## Guidance
- For heterogeneous fields (cast, director, plot with different analyzers or field types), use `best_fields` with explicit per-field boosts.
- For homogeneous text fields sharing an analyzer (title, overview, tagline), prefer `combined_fields`.
- Always translate both `qf` and `pf` — dropping `pf` loses phrase proximity boosting, which degrades relevance for multi-word queries.
- Solr's `mm` (minimum_should_match) applies directly via `minimum_should_match` on the `multi_match` or `bool` query.

## Example
Solr eDisMax parameters:
```
defType=edismax
qf=title^10 overview^5 cast^3 directors^3 tagline^2
pf=title^15 overview^8
mm=2<-1 5<80%
```

OpenSearch equivalent:
```json
{
  "query": {
    "bool": {
      "must": [{
        "multi_match": {
          "query": "user query here",
          "fields": ["title^10", "overview^5", "cast^3", "directors^3", "tagline^2"],
          "type": "best_fields",
          "minimum_should_match": "2<-1 5<80%"
        }
      }],
      "should": [{
        "multi_match": {
          "query": "user query here",
          "fields": ["title^15", "overview^8"],
          "type": "phrase"
        }
      }]
    }
  }
}
```
