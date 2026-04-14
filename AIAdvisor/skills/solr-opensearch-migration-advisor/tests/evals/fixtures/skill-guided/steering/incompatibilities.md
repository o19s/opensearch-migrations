# Solr to OpenSearch Incompatibilities

## Function Queries
Solr function queries (`bf`, `boost`, `_val_`) → use `function_score` with `script_score`, `field_value_factor`, or decay functions. See `references/function-queries.md`.

## Custom Request Handlers
No direct equivalent in OpenSearch; must rebuild using standard Search API + client-side logic. See `references/request-handlers.md`.

## eDisMax Field Weighting
`qf=title^10 overview^5` → `multi_match` with `fields: ["title^10", "overview^5"]`. See `references/edismax.md`.

## Highlighting
`hl.fragsize` → `fragment_size`, `hl.snippets` → `number_of_fragments`, `hl.simple.pre/post` → `pre_tags`/`post_tags`. See `references/highlighting.md`.

## Joins
Solr `{!join}` has no direct equivalent; use `terms` lookup query or denormalize (flatten) at index time. See `references/joins.md`.
