# Solr to OpenSearch Incompatibilities Steering

Each incompatibility is tagged with severity:
- **Blocker** — no direct equivalent; requires redesign or external tooling
- **Major** — equivalent exists but requires significant rewriting
- **Minor** — equivalent exists with small syntax/config changes

---

## Schema & Field Type Incompatibilities

1. **`copyField`** (Minor) — Solr `copyField` directive maps to OpenSearch `copy_to` field parameter. Must be declared per-field in mappings rather than as a top-level directive. Multi-target `copyField` (one source → multiple destinations) requires `copy_to` on each target.

2. **`ICUCollationField`** (Major) — Solr's `ICUCollationField` provides locale-aware sorting and comparison. OpenSearch has the `icu_collation_keyword` type via the ICU analysis plugin, but configuration syntax differs significantly. Requires plugin installation on managed OpenSearch.

3. **`EnumField` / `EnumFieldType`** (Major) — Solr supports enum fields with ordered string values and custom sort order. No direct OpenSearch equivalent. Workaround: map to `keyword` with a parallel `integer` field for sort order, or use `script_score` / runtime fields.

4. **`SortableTextField`** (Minor) — Solr 7+ field type combining full-text and doc-values for sorting. OpenSearch workaround: use `text` field with a `keyword` sub-field (`fields.raw`).

5. **Dynamic fields** (Minor) — Solr `dynamicField` rules like `*_s`, `*_txt` map to OpenSearch `dynamic_templates`. Syntax differs: Solr uses glob-style name patterns; OpenSearch uses `match`/`match_pattern` with regex or simple wildcard.

6. **`_all` field** (Major) — Solr's implicit catch-all field. Deprecated in Elasticsearch 6+ and absent in OpenSearch. Must explicitly define a `copy_to` target field or use `multi_match` across known fields.

7. **Schema-less / managed-schema auto-field-addition** (Minor) — Solr's schemaless mode adds fields on the fly via field guessing. OpenSearch has `dynamic: true` (default) but type inference rules differ. Explicit mappings recommended for production.

8. **`multiValued` + `docValues` behavior** (Minor) — Solr stores multi-valued docValues as `SORTED_SET`. OpenSearch stores multi-valued fields as arrays with doc_values automatically. Sorting on multi-valued fields differs: Solr picks min/max implicitly; OpenSearch requires explicit `mode` parameter.

## Query & Search Incompatibilities

9. **Function queries** (Major) — Solr `{!func}recip()`, `sum()`, `product()`, `log()`, `map()` etc. Must be rewritten to OpenSearch `script_score` with Painless scripts, or use built-in `function_score` functions (`decay`, `field_value_factor`). No 1:1 syntax translation.

10. **MoreLikeThis handler** (Major) — Solr's MLT handler and query parser (`{!mlt}`) map to OpenSearch `more_like_this` query. Parameters differ: Solr `mlt.fl` → `fields`, `mlt.mintf` → `min_term_freq`. Stream-based MLT (posting a document body) not supported in OpenSearch.

11. **Spatial / geo queries** (Major) — Solr `{!geofilt}`, `{!bbox}`, `geodist()` function → OpenSearch `geo_distance`, `geo_bounding_box` queries. Solr `SpatialRecursivePrefixTreeFieldType` (RPT) has no direct equivalent; use `geo_shape` with appropriate precision. JTS geometry library behaviors differ.

12. **Join queries** (Blocker) — Solr `{!join from=field_a to=field_b}` performs index-time or query-time joining across documents. No direct OpenSearch equivalent. Options: `nested` type, `has_child`/`has_parent` queries (requires parent-child data model), `terms` lookup query, or denormalize at index time.

13. **Graph queries** (Blocker) — Solr `{!graph}` for recursive traversal has no OpenSearch equivalent. Must redesign as application-level traversal or move logic to a graph database.

14. **Block join / nested documents** (Major) — Solr `_childDocuments_` and `{!parent}`/`{!child}` queries map to OpenSearch `nested` type or `join` field type (parent-child). Data must be reindexed in the appropriate structure. Performance characteristics differ.

15. **Streaming expressions** (Blocker) — Solr's `/stream` handler and streaming expressions (e.g., `search()`, `rollup()`, `jdbc()`) have no OpenSearch equivalent. Must be rebuilt using OpenSearch SQL, PPL (Piped Processing Language), or application-level logic.

16. **Solr SQL** (Major) — Solr's SQL interface (via `/sql` handler, built on Apache Calcite) maps to OpenSearch SQL plugin. Syntax is similar but not identical. Complex joins and subqueries may not translate.

17. **Local params / query parsers** (Major) — Solr's `{!parser param=value}` local params syntax has no equivalent in OpenSearch. Each parser (`lucene`, `edismax`, `dismax`, `complexphrase`, etc.) must be translated to the corresponding OpenSearch query type.

18. **Real-time GET** (Minor) — Solr's `/get` handler for fetching by ID without near-real-time search latency maps to OpenSearch `GET /<index>/_doc/<id>` API. Functionally similar but Solr returns uncommitted documents; OpenSearch's real-time get returns the latest version from the transaction log.

19. **Grouping / collapse** (Major) — Solr `group=true&group.field=X` maps to OpenSearch `collapse` field or `terms` aggregation with `top_hits`. Solr's `group.ngroups`, `group.truncate`, and `group.func` have no direct equivalents. Requires redesign for complex grouping.

## Faceting Incompatibilities

20. **JSON Facet API** (Major) — Solr's JSON Facet API (`json.facet`) maps to OpenSearch aggregations. Conceptually similar but syntax is entirely different. Solr's `domain` changes, `relatedness()` stat, and `type: "query"` facets require careful translation.

21. **Facet exclusion tags** (Major) — Solr's `{!tag=X}` on `fq` and `{!ex=X}` on facets for multi-select faceting has no declarative equivalent in OpenSearch. Must implement using `global` aggregations or `post_filter` + multiple filtered aggregations.

22. **Pivot facets** (Minor) — Solr `facet.pivot=field1,field2` maps to nested `terms` aggregations. Straightforward but verbose.

## Analysis & Text Processing Incompatibilities

23. **`WordDelimiterFilterFactory`** (Major) — Solr's WDFF (and `WordDelimiterGraphFilterFactory`) has many configuration options (`splitOnCaseChange`, `generateWordParts`, `catenateWords`, etc.). OpenSearch's `word_delimiter` / `word_delimiter_graph` filter supports most options but defaults differ. Must audit and test each configured option.

24. **`SynonymFilterFactory` format** (Minor) — Both support synonym files, but format details differ. Solr supports `solr` and `wordnet` formats. OpenSearch supports `solr` format synonym files. Test with the actual synonym file.

25. **`PhoneticFilterFactory`** (Minor) — Solr bundles multiple phonetic encoders (Metaphone, Soundex, etc.) via `analysis-extras`. OpenSearch provides the `phonetic` analysis plugin. Requires plugin installation; encoder names and parameters may differ.

26. **`ICUFoldingFilterFactory` / `ICUNormalizer2FilterFactory`** (Minor) — Requires the ICU analysis plugin in OpenSearch. Available but must be explicitly installed on managed clusters.

27. **`ManagedSynonymFilterFactory` / `ManagedStopFilterFactory`** (Major) — Solr's managed resources REST API for live synonym/stopword updates has no direct equivalent. OpenSearch requires reindexing or index close/open to update synonyms. Workaround: use `search_analyzer` with the synonym filter and reopen the index.

## Relevance Tooling Incompatibilities

28. **Querqy engine-native rules** (Major) — Generic Querqy rules (SYNONYM, DELETE, DECORATE) port cleanly. Rules containing Solr-native syntax (raw `fq` filters, Lucene query syntax in boost expressions) must be rewritten to OpenSearch Query DSL. See `steering/relevance_tooling.md`.

29. **Querqy on AWS Managed OpenSearch** (Major) — Not pre-installed. Custom plugin upload available on OpenSearch 2.15+ in select regions only. Not available on Serverless. Must validate region availability and version compatibility.

30. **Query Elevation / pinned results** (Blocker) — Solr's `QueryElevationComponent` (elevate.xml) pins specific documents for specific queries. No built-in OpenSearch equivalent. Workaround: Querqy DECORATE rules with application logic, or `function_score` with extreme weights on document IDs, or `pinned` query (available in Elasticsearch but **not** in OpenSearch).

31. **Learning to Rank** (Major) — Solr LTR and OpenSearch LTR plugins have different model registration APIs, feature store formats, and model serialization. Models must be re-exported and re-registered. Retraining often needed because feature values (scores, norms) differ between engines.

## Infrastructure & Operations Incompatibilities

32. **ZooKeeper dependency** (Minor) — SolrCloud requires external ZooKeeper for cluster coordination. OpenSearch uses internal cluster manager nodes. Eliminates operational dependency but requires understanding of OpenSearch master election and `minimum_master_nodes` (deprecated; use `cluster.initial_master_nodes`).

33. **Config set management** (Major) — Solr stores schema + solrconfig per collection in ZooKeeper (`/configs/`). OpenSearch stores index settings + mappings per index via REST API. No equivalent to Solr's config set sharing/inheritance across collections.

34. **Data Import Handler (DIH)** (Blocker) — Solr's DIH for database-to-index ingestion has no OpenSearch equivalent. Replace with Logstash JDBC input, OpenSearch Ingestion (OSI) pipeline, or custom application code.

35. **SolrJ client library** (Major) — SolrJ has no OpenSearch equivalent. Must migrate to `opensearch-java` client. API surface differs entirely (SolrJ is Solr-specific; opensearch-java uses builder pattern for Query DSL). See also: pysolr → `opensearch-py`.

36. **Authentication model** (Major) — Solr supports BasicAuth, Kerberos, PKI, and custom `AuthenticationPlugin`. OpenSearch supports BasicAuth (internal users database), SAML, OIDC, LDAP/AD, client certificates via Security plugin. Direct mapping varies; Kerberos requires proxy-based auth or LDAP backend.

37. **Collection aliasing** (Minor) — Solr aliases map to OpenSearch aliases. Solr's routed aliases (time-routed, category-routed) have no direct equivalent; use ISM (Index State Management) rollover policies for time-based patterns.

## Plugin & Extension Incompatibilities

38. **Custom Request Handlers** (Blocker) — Solr's custom `RequestHandler` classes (extending `SearchHandler` or `RequestHandlerBase`) have no direct equivalent. Must rebuild using standard OpenSearch Search API + client-side logic, or write a custom OpenSearch plugin with `RestHandler`.

39. **Search Components** (Blocker) — Solr's `SearchComponent` pipeline (chained components in `solrconfig.xml` like `SpellCheckComponent`, `SuggestComponent`, `DebugComponent`) has no equivalent. Logic must be moved to client-side orchestration, OpenSearch plugin development, or replaced with built-in OpenSearch features where available (e.g., `_search` suggesters, `_explain` API).

40. **Solr Power** (Blocker) — No equivalent; use standard OpenSearch feature set.

41. **Solr contrib modules** (Major) — Solr ships contrib modules (analysis-extras, clustering, langid, velocity) that may not have OpenSearch equivalents. Must audit which contribs are in use and find replacements: e.g., `langid` → OpenSearch `lang_ident` ingest processor; `clustering` → no equivalent; `velocity` (response templating) → no equivalent.
