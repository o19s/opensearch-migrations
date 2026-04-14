# multi_match Type Selection for eDisMax qf Migration

## Decision Rule
- **Different analyzers across qf fields** → `type: "best_fields"`
- **Same analyzer on ALL qf fields** → `type: "combined_fields"` (preferred) or `type: "cross_fields"`

## Why This Matters
`combined_fields` computes a single BM25 score across all fields as if they
were one logical field. This ONLY works when all fields use the same analyzer.
If fields have different analyzers (e.g., text_general for title vs keyword
for genres), `combined_fields` will produce errors or incorrect scoring.

## TMDB Example
```
qf=title^10 overview^5 cast^3 directors^3 tagline^2
```
- title, overview, tagline → `text_general` analyzer
- cast, directors → `text_general` but multiValued

Since all use text_general, `combined_fields` is technically valid here.
But if any field used a different analyzer (e.g., `genres_s` as keyword),
you MUST use `best_fields`.

## OpenSearch Translation
```json
{
  "multi_match": {
    "query": "dark knight",
    "type": "best_fields",
    "fields": ["title^10", "overview^5", "cast^3", "directors^3", "tagline^2"]
  }
}
```
