# Solr to OpenSearch Incompatibilities Steering

## Query Gaps
- Function Queries: OpenSearch `script_score` is the replacement, but syntax differs.
- MoreLikeThis (MLT): Similar, but syntax is different.
- Spatial: Solr `latlon` and `spatial` fields map to `geo_point` and `geo_shape`.

## Features
- Dynamic Fields: Mapping differs, `dynamic_templates` is the OpenSearch way.
- Nested Docs: Solr `_childDocuments_` maps to `nested` objects or parent-child joining.
- Joins: Solr `!join` maps to `terms` lookup query or flattened index design.

## Plugins
- Custom Request Handlers: No direct equivalent; must rebuild using standard Search API + Client-side logic.
- Search Components: No equivalent; logic must be moved to the client or a custom OpenSearch plugin.
- Solr Power: No equivalent; use standard OpenSearch feature set.

## Metrics-Derived Incompatibilities

When live Solr metrics are available (via `inspect_solr_mbeans`), check handler usage to flag additional incompatibilities:

- **MoreLikeThis handler** with high request count → Behavioral: MLT syntax differs in OpenSearch. High usage means many code paths to update.
- **StreamHandler / Streaming Expressions** → Unsupported: No equivalent in OpenSearch. Move aggregation logic to the application layer or use OpenSearch aggregations.
- **Custom request handlers** (non-standard class names in MBeans) with significant request counts → Breaking: Must be rebuilt. Prioritize by request volume — high-traffic custom handlers are the most urgent migration items.
- **GraphHandler / `{!graph}`** → Unsupported: No graph traversal in OpenSearch.
- **Spell check / suggest handler** with high usage → Behavioral: OpenSearch has suggesters but the API differs. High usage means search-as-you-type UX may change.
- **High error rate on any handler** (> 1% of requests) → Informational: Investigate before migration — existing errors may mask additional incompatibilities.
