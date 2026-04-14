# Solr to OpenSearch Incompatibilities Steering

## Query Gaps

### Function Queries
Solr function queries (`bf`, `boost`, `_val_`) use a math-expression syntax
that has no direct equivalent in OpenSearch. The replacement is
`function_score` with `script_score`, `field_value_factor`, or decay
functions — but every translation requires rewriting the expression.

Common patterns:

| Solr | OpenSearch | Notes |
|------|-----------|-------|
| `bf=vote_average^2` | `function_score` → `field_value_factor: { field: "vote_average", modifier: "none" }` with `boost_mode: "sum"` | Simple field boost. The `^2` multiplier maps to `factor: 2` in `field_value_factor`. |
| `bf=recip(ms(NOW,release_date),3.16e-11,1,1)` | `function_score` → `exp` or `gauss` decay on `release_date` with `origin: "now"`, `scale`, `offset`, `decay` | Recency boost. Solr's `recip(ms(...))` has no formula equivalent — pick a decay function and tune `scale`/`decay` to approximate the curve. |
| `bf=linear(vote_count,1,0)` | `field_value_factor: { field: "vote_count", modifier: "none", factor: 1, missing: 0 }` | Linear field value. |
| `bf=log(vote_count)` | `field_value_factor: { field: "vote_count", modifier: "log1p" }` | Log boost. Note: Solr `log()` is natural log; OpenSearch `log1p` is `ln(1+x)` — close but not identical. |
| `bf=sum(vote_average,1)` | `script_score: { script: { source: "doc['vote_average'].value + 1" } }` | Arbitrary math falls back to Painless scripting. |
| `bf=product(vote_average,vote_count)` | `script_score: { script: { source: "doc['vote_average'].value * doc['vote_count'].value" } }` | Multi-field math requires scripting. |
| `bf=if(exists(query({!v='genres:Action'})),10,1)` | `should` clause with `boost: 10` or `script_score` with conditional | Solr's `if(exists(query(...)))` pattern has no declarative equivalent. Prefer a `should` clause when possible; fall back to Painless for complex conditionals. |
| `_val_:"ord(popularity)"` | Not supported — use `field_value_factor` or `script_score` | Solr's `ord()` (ordinal position) and `rord()` have no OpenSearch equivalent. |

**Key warnings:**
- `boost_mode` matters: Solr's `bf` is additive (added to the relevance score). Use `boost_mode: "sum"` in OpenSearch. Solr's `boost` parameter is multiplicative — use `boost_mode: "multiply"`.
- `missing` field values: Solr function queries silently return 0 for missing fields. OpenSearch `field_value_factor` throws errors unless you set `missing: 0`.
- **Performance**: `script_score` runs Painless on every matching doc. For large result sets, `field_value_factor` and decay functions are significantly faster.
- **Testing**: Function score translations change ranking. Always compare top-N results between Solr and OpenSearch after migration to verify the approximation is acceptable.

### MoreLikeThis (MLT)
Solr's MLT handler (`/mlt`) and query parser (`{!mlt}`) map to OpenSearch's
`more_like_this` query, but parameter names differ:

| Solr | OpenSearch |
|------|-----------|
| `mlt.fl=title,overview` | `fields: ["title", "overview"]` |
| `mlt.mintf=2` | `min_term_freq: 2` |
| `mlt.mindf=5` | `min_doc_freq: 5` |
| `mlt.maxqt=25` | `max_query_terms: 25` |
| `mlt.boost=true` | `boost_terms: 1` (or higher) |
| Stream body or `mlt.match.include` | `like: { _index: "idx", _id: "123" }` or `like: "free text"` |

Solr's MLT handler returns similar docs as a primary result set. OpenSearch's
MLT is a query clause — wrap it in a standard `_search` request.

### Spatial
Solr spatial field types map to OpenSearch geo types, but query syntax
differs completely:

| Solr | OpenSearch |
|------|-----------|
| `fieldType class="solr.LatLonPointSpatialField"` | `type: "geo_point"` |
| `fieldType class="solr.SpatialRecursivePrefixTreeFieldType"` | `type: "geo_shape"` |
| `fq={!geofilt sfield=location pt=40.7,-74.0 d=10}` | `geo_distance: { distance: "10km", location: { lat: 40.7, lon: -74.0 } }` |
| `fq={!bbox sfield=location pt=40.7,-74.0 d=10}` | `geo_bounding_box` with computed corners |
| `bf=recip(geodist(),2,200,20)` | `function_score` with `gauss` decay on geo_point field |
| `sort=geodist() asc` | `sort: [{ "_geo_distance": { "location": [lon, lat], "order": "asc" } }]` |

**Warning**: Solr uses `d` (distance in km), OpenSearch uses `distance` with
explicit units (`"10km"`, `"5mi"`). Solr's `geodist()` in function queries
has no direct equivalent — use decay functions or `_geo_distance` sort.

## Features

### Dynamic Fields
Solr's `dynamicField` patterns (`*_s`, `*_i`, `*_txt`) map to OpenSearch
`dynamic_templates`, but the matching syntax differs:

```
<!-- Solr -->
<dynamicField name="*_s" type="string" indexed="true" stored="true"/>

// OpenSearch
"dynamic_templates": [{
  "strings": {
    "match_mapping_type": "string",
    "match": "*_s",
    "mapping": { "type": "keyword" }
  }
}]
```

**Warning**: Solr dynamic fields are evaluated in order (first match wins).
OpenSearch dynamic templates are also ordered, but the matching rules
(`match`, `match_mapping_type`, `path_match`) are more restrictive.
Test with sample documents to verify the same fields get the expected types.

### Nested Docs
Solr `_childDocuments_` (block join) maps to OpenSearch `nested` type or
`join` field (parent-child). Key differences:

- Solr block join requires documents to be indexed together in the same
  update request. OpenSearch `nested` objects are stored within the parent
  document (similar constraint).
- Solr's `{!parent}` and `{!child}` query parsers map to `nested` query
  and `has_child`/`has_parent` queries.
- OpenSearch `nested` queries require explicit `path` and return the parent
  document. Solr's child document transformer (`[child]`) maps to
  `inner_hits` in OpenSearch.
- **Performance**: OpenSearch `nested` fields create hidden internal
  documents. Large arrays of nested objects can significantly increase
  index size and query latency.

### Joins
Solr `{!join from=field_a to=field_b}` has no direct equivalent.
Options in OpenSearch:

| Approach | When to use |
|----------|-------------|
| `terms` lookup query | Small-to-medium join sets. Queries index B to get values, uses them to filter index A. |
| Denormalize (flatten) | Best performance. Copy joined data into the parent document at index time. Trades storage for query speed. |
| `nested` type | When child data is naturally embedded and queried together with parent. |
| `join` field (parent-child) | When child docs update independently of parents. Higher query cost than nested. |

**Warning**: Solr joins are evaluated at query time and can be chained.
OpenSearch `terms` lookup is single-hop only. Multi-level joins require
denormalization or application-side logic.

## Plugins

### Querqy
Solr Querqy (query rewriting, synonyms, boosts, filters) has a community
OpenSearch plugin, but it is **not included by default** in managed
OpenSearch (AWS). Migration options:

- Self-managed OpenSearch: Install the Querqy OpenSearch plugin.
- AWS OpenSearch Service: No Querqy support. Rewrite rules must be
  translated to: synonym token filters, `should` clauses for boosts,
  `must_not` clauses for down-boosts, and `filter` clauses for Querqy
  filters. This is a significant manual effort.

### SMUI (Search Management UI)
SMUI manages Querqy rules via a web UI. If Querqy is not available on the
target OpenSearch cluster, SMUI rules must be exported and translated into
native OpenSearch constructs (synonyms files, query templates, etc.).

### Custom Request Handlers
No direct equivalent in OpenSearch. Solr request handlers that combine
multiple search components (faceting, grouping, highlighting, custom logic)
must be decomposed into:
- Standard OpenSearch query features (aggregations, highlighters, collapse)
- Search templates for reusable query patterns
- Client-side orchestration for complex multi-step logic
- Custom OpenSearch plugins (last resort — increases operational complexity)

### Search Components
Solr search components (`SearchComponent` interface) that hook into the
query pipeline have no equivalent. Logic must move to:
- OpenSearch search pipelines (request/response processors) — available
  in OpenSearch 2.x for some use cases
- Client-side pre/post processing
- Ingest pipelines (for index-time transformations)

### LTR (Learning to Rank)
Both Solr and OpenSearch support LTR plugins, but model formats and feature
definitions differ:
- Solr LTR: Model stored in Solr's managed resources, features defined
  as Solr feature stores.
- OpenSearch LTR: Uses the OpenSearch LTR plugin, models uploaded via API,
  features defined as OpenSearch queries.
- **Migration**: Feature definitions must be rewritten from Solr query
  syntax to OpenSearch DSL. Model weights can often be preserved if the
  same algorithm (LambdaMART, linear) is used on both sides. Retrain
  if feature semantics changed during translation.
