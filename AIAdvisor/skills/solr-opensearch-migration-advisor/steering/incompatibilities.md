# Solr to OpenSearch Incompatibilities Steering

## Query Gaps
- Function Queries: OpenSearch `script_score` is the replacement, but syntax differs.
- MoreLikeThis (MLT): Similar, but syntax is different.
- Spatial: Solr `latlon` and `spatial` fields map to `geo_point` and `geo_shape`.

## Features
- Dynamic Fields: Mapping differs, `dynamic_templates` is the OpenSearch way.
- Nested Docs: Solr `_childDocuments_` maps to `nested` objects or parent-child joining.
- Joins: Solr `!join` maps to `terms` lookup query or flattened index design.

## Relevance Tooling
- Querqy: Plugin exists for OpenSearch, but engine-native rules (Solr `fq` syntax in filters/boosts) must be rewritten to Query DSL. Generic rules port cleanly. AWS Managed requires custom plugin upload (2.15+, not on Serverless). See `steering/relevance_tooling.md`.
- SMUI: Supports OpenSearch backend. Reconfigure connection + audit rule syntax.
- Query Elevation (pinned results): No built-in OpenSearch equivalent. Querqy DECORATE + application logic, or `function_score` with extreme weights.
- Learning to Rank: Solr LTR and OpenSearch LTR have different APIs, feature stores, and model formats. Models must be re-exported and often retrained.

## Plugins
- Custom Request Handlers: No direct equivalent; must rebuild using standard Search API + Client-side logic.
- Search Components: No equivalent; logic must be moved to the client or a custom OpenSearch plugin.
- Solr Power: No equivalent; use standard OpenSearch feature set.
