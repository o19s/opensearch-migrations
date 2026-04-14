# bf vs boost: Additive vs Multiplicative Scoring

## Solr Behavior
- `bf=linear(popularity,1,0)` → score = relevance + popularity (ADDITIVE)
- `boost=linear(popularity,1,0)` → score = relevance × popularity (MULTIPLICATIVE)

## OpenSearch Translation
```json
// bf (additive) → boost_mode: "sum"
{
  "function_score": {
    "query": { "multi_match": { ... } },
    "field_value_factor": { "field": "popularity" },
    "boost_mode": "sum"
  }
}

// boost (multiplicative) → boost_mode: "multiply"
{
  "function_score": {
    "query": { "multi_match": { ... } },
    "field_value_factor": { "field": "popularity" },
    "boost_mode": "multiply"
  }
}
```

## Common Mistake
Using `boost_mode: "multiply"` for a `bf` translation (or vice versa) will
produce drastically different rankings. A document with popularity=0 would
get score=0 under multiply but score=relevance under sum.
