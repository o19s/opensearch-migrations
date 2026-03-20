# Edge Cases, Gotchas, and Long-Tail Migration Issues

> **Secondary Reference** — This file covers edge cases, obscure pitfalls, and long-tail
> issues that go beyond the primary expert references. It is designed to be loaded on demand
> when a user's situation suggests they may hit one of these issues, not as default reading.
>
> For the core migration path, see references 01–07. This file covers the remaining 20%.

---

## How to Use This File

**Load this reference when:**
- The user mentions a specific Solr feature not covered in the primary references
- The user reports unexpected behavior after migration
- The user asks "what else could go wrong?" or "what am I missing?"
- The migration involves uncommon Solr features (streaming expressions, CDCR, block joins, custom update processors, payload scoring)
- The user is doing a pre-migration risk assessment and wants exhaustive coverage

**Do not load by default** — the primary references cover the 80% case. This file is the safety net.

---

## 1. Query Translation Edge Cases

### 1.1 minimum_should_match behaves differently per-field vs per-document

**The trap:** In Solr eDisMax with `sow=true`, `mm` (minimum_should_match) is evaluated
per-document — a doc must contain N of the query terms *anywhere across all queried fields*.
In OpenSearch `multi_match` with `best_fields` or `most_fields`, `minimum_should_match` is
applied *per-field* — each field independently must satisfy the constraint.

**Result:** OpenSearch silently drops results that Solr would have returned.

**Fix:** Use `type: cross_fields` in `multi_match`, which evaluates across fields like Solr.
Or decompose into explicit `bool` queries with controlled `minimum_should_match` at the
outer level.

**Impact:** Critical for any migration using `mm` with multi-field queries.

**Sources:**
- https://docs.opensearch.org/latest/query-dsl/full-text/multi-match/
- https://solr.apache.org/guide/8_8/the-extended-dismax-query-parser.html

### 1.2 simple_query_string is NOT a drop-in for Solr query syntax

**The trap:** `simple_query_string` looks like Solr's query syntax, making it tempting as a
shortcut. But it handles boosting, operators, and whitespace differently. Term-specific boosts
in multi-word queries may require full `bool` query syntax.

**Fix:** Validate all query patterns explicitly. Don't assume compatibility.

**Sources:**
- https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-solr-opensearch/query-conversion.html

### 1.3 Query Elevation Component has no built-in equivalent

**The trap:** Solr's Query Elevation ("best bets", "sponsored search") pins specific documents
to the top for specific queries via XML config. OpenSearch has no built-in equivalent.
(Elasticsearch has a `pinned` query since 7.4, but OpenSearch does not.)

**Fix:** Implement via application-layer logic, boosting with `function_score` and extreme
weights, or a custom solution that injects pinned IDs into queries as `should` clauses with
high boost.

**Impact:** Important for e-commerce and editorial search.

### 1.4 max_clause_count defaults are much lower

**The trap:** OpenSearch 2.0+ defaults `max_clause_count` to 1024. Solr typically allows
much higher limits. Queries that worked fine in Solr suddenly fail with
`too_many_clauses` errors. Wildcard queries and queries with many OR terms are especially
affected.

**Fix:** Increase via cluster settings: `PUT /_cluster/settings { "persistent": { "indices.query.bool.max_clause_count": 4096 } }`. But also audit queries — rewrite to use `terms` queries for bulk matching instead of many `should` clauses.

**Impact:** Critical — causes hard failures, not subtle relevance changes.

**Sources:**
- https://github.com/opensearch-project/OpenSearch/issues/3652

### 1.5 Solr function queries vs function_score composability

**The trap:** Solr allows arbitrary mathematical scoring combinations inline. OpenSearch's
`function_score` has a fixed set of functions (weight, field_value_factor, script_score, decay,
random_score). Solr's composability (`product(query({!type=edismax qf=title}hello), 2.0)`)
is harder to replicate.

**Fix:** Use `script_score` with Painless for complex formulas. Be aware that Painless scripts
have performance implications at scale — benchmark before production.

### 1.6 Grouping / field collapsing semantics differ

**The trap:** Solr's `CollapsingQParser` is a post-filter with specific semantics around
group head selection. OpenSearch's `collapse` parameter and `inner_hits` have different APIs
and edge-case behavior, especially around null values in the collapse field and interaction
with aggregations.

**Fix:** Rewrite using OpenSearch's `collapse` parameter with `inner_hits`. Test thoroughly —
null handling and tie-breaking logic differ.

### 1.7 Spellcheck/Suggest architecture differences

**The trap:** Solr's SuggestComponent provides in-memory lookup implementations (TSTLookup,
FSTLookup, WFSTLookup) with fine-grained control. OpenSearch's suggesters have different
architecture and capability. The `completion` field type requires a dedicated mapping.

**Fix:** Use OpenSearch's `completion` field type for autocomplete, `term`/`phrase` suggesters
for spell-check. Test quality — algorithms and ranking differ.

**Sources:**
- https://opensearch.org/docs/latest/search-plugins/searching-data/did-you-mean/

---

## 2. Schema and Mapping Edge Cases

### 2.1 Text vs keyword fielddata memory bomb

**The trap:** Trying to sort or aggregate on a `text` field fails by default in OpenSearch.
The "fix" that appears in Stack Overflow — enabling `fielddata: true` — is a memory bomb that
leads to `CircuitBreakingException` and node instability. This has no parallel in Solr where
field types handle both search and sort/agg concerns.

**Fix:** Use multi-fields: map as both `text` (for search) and `keyword` (for sort/agg).
Use the `.keyword` sub-field for sorting and aggregations. **Never enable `fielddata: true`
in production.**

**Impact:** Critical — can take down nodes.

**Sources:**
- https://opensearch.org/blog/error-logs/error-log-fielddata-is-disabled-on-text-fields-by-default/

### 2.2 multiValued enforcement is lost

**The trap:** Solr explicitly marks fields as `multiValued`. OpenSearch has no such
attribute — ANY field can accept an array. You lose schema-level enforcement that prevents
accidentally storing arrays in single-value fields.

**Fix:** Enforce single-value constraints at the application layer or with ingest pipeline
validation.

### 2.3 Geospatial field type gaps (RPT features)

**The trap:** Solr's `SpatialRecursivePrefixTreeFieldType` (RPT) supports features like
heatmap faceting and complex polygon operations that OpenSearch's `geo_point` does not.

**Fix:** Map `LatLonPointSpatialField` to `geo_point`. For polygon needs, use `geo_shape`.
For heatmap faceting, use `geotile_grid` or `geohash_grid` aggregations — similar but not
identical.

### 2.4 Index template changes don't affect live indexes

**The trap:** Changing an OpenSearch index template does NOT change the configuration of
live indexes. Unlike Solr configsets uploaded to ZooKeeper which can affect running
collections, OpenSearch templates only apply to *new* indexes.

**Fix:** Apply changes to both the template (for future indexes) and the live index (for
current). For mapping changes that require reindexing, create a new index and alias-swap.

### 2.5 Cluster-level settings that were index-level in Solr

**The trap:** Some Solr settings configurable per-collection are cluster-level in OpenSearch:
`max_clause_count`, circuit breaker settings, cache settings. You can't set different limits
for different indexes.

**Fix:** Set cluster-level defaults that work for all indexes. Design around the constraint.

---

## 3. Analyzer Chain Edge Cases

### 3.1 SynonymGraphFilter + word_delimiter_graph ordering

**The trap:** Migrating a Solr analyzer chain that applies `word_delimiter_graph` before
synonym expansion, with `FlattenGraphFilterFactory` after, can produce different results in
OpenSearch. The token graph handling differs subtly.

**Fix:** Test analyzer chains with `_analyze` API. May need to reorder filters.
Good news: OpenSearch supports both Solr synonym format and WordNet format, so synonym files
can usually be reused directly.

**Sources:**
- https://github.com/opensearch-project/OpenSearch/issues/16263

### 3.2 Custom similarity classes require plugin development

**The trap:** Solr allows custom similarity implementations via Java classes referenced in
schema.xml. OpenSearch requires writing and installing a plugin for custom similarities. On
AWS managed OpenSearch, custom plugins are not supported — you're limited to built-in
similarities (BM25, DFR, DFI, IB, LM Dirichlet, LM Jelinek Mercer).

**Fix:** If using classic TF-IDF, configure `"similarity": { "type": "scripted", ... }` or
accept BM25 and retune. If using truly custom scoring, this may be a migration blocker for
AWS managed service.

**Impact:** Critical for users with custom similarity implementations on AWS.

---

## 4. Relevance Deep Cuts

### 4.1 BM25 length normalization over-penalizes long documents

**The trap:** BM25's `b` parameter controls document length normalization. At the default
`b=0.75`, long documents are penalized relative to shorter ones. If your corpus has high
variance in document length (e.g., mixing abstracts with full-text articles), short documents
may be unfairly boosted.

**Fix:** Tune the `b` parameter: `0` disables length normalization entirely, `1` is full
normalization. Start with `0.75` (default) and adjust based on relevance testing.

**Sources:**
- https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables

### 4.2 Learning to Rank model migration

**The trap:** Solr's LTR module and OpenSearch's LTR plugin have different APIs, feature store
formats, and model definition syntax. The OpenSearch LTR plugin has been significantly improved
(2024–2025) and is now a first-class component, but migration requires rewriting feature
definitions.

**Good news:** Trained model weights (XGBoost, RankLib) can often be preserved — only the
feature definitions need rewriting to OpenSearch query syntax.

**Sources:**
- https://docs.opensearch.org/latest/search-plugins/ltr/index/
- https://opensourceconnections.com/blog/2025/12/16/a-year-of-transformation-for-learning-to-rank-in-opensearch/

---

## 5. Data Migration and Indexing Edge Cases

### 5.1 Data Import Handler (DIH) is gone

**The trap:** DIH was deprecated in Solr 8.6 and removed in 9.0. Many Solr deployments rely
on DIH for database-to-index synchronization. OpenSearch has no equivalent built-in.

**Fix:** Replace with Logstash JDBC input, Apache NiFi, OpenSearch Ingestion (Data Prepper),
or custom application code. This also requires converting XML document format to JSON.

**Impact:** Critical for deployments that rely on DIH for ongoing data sync, not just the
initial migration.

**Sources:**
- https://pureinsights.com/blog/2022/apache-solr-removing-data-import-handler/

### 5.2 Update processor chains → ingest pipelines

**The trap:** Solr's `updateRequestProcessorChain` must be converted to OpenSearch ingest
pipelines. The processor types, configuration, and error handling are completely different.
Some Solr update processors (e.g., `StatelessScriptUpdateProcessor`) have no direct equivalent.

**Fix:** Map each processor individually. Consider whether complex transformations should
move to the application layer or OpenSearch Ingestion (Data Prepper) instead of ingest
pipelines.

### 5.3 Optimistic concurrency control differences

**The trap:** Solr uses `_version_` field for optimistic locking. OpenSearch uses
`_seq_no` + `_primary_term` for the same purpose. The semantics are similar but the API
is different, and external versioning (`version_type: external`) has its own gotchas.

**Fix:** Rewrite concurrency control code to use `if_seq_no` and `if_primary_term` parameters
on update requests.

### 5.4 Bulk indexing refresh behavior

**The trap:** During bulk loads, OpenSearch's default 1-second `refresh_interval` creates
enormous overhead. Each refresh creates a new Lucene segment. With millions of documents,
this causes segment explosion, high merge overhead, and degraded performance.

**Fix:** Set `refresh_interval: -1` before bulk loading, then force refresh after.
Also set `number_of_replicas: 0` during bulk load, then restore after. This mirrors
Solr's pattern of disabling autoSoftCommit during bulk loads.

**Sources:**
- https://opensearch.org/blog/optimize-refresh-interval/

---

## 6. Operations Edge Cases

### 6.1 Disk watermark blocks are percentage-based

**The trap:** OpenSearch blocks index creation when disk usage exceeds percentage thresholds
(low: 85%, high: 90%, flood: 95%), even if hundreds of GB remain free on large volumes.
During migration, when you're actively creating new indexes, this can cause sudden failures.

**Fix:** Check `_cat/nodes?h=disk.used_percent` before migration. Relax thresholds if needed:
`PUT /_cluster/settings { "persistent": { "cluster.routing.allocation.disk.watermark.low": "90%", "cluster.routing.allocation.disk.watermark.high": "95%" } }`

### 6.2 No in-place rollback after OpenSearch upgrade

**The trap:** Once you upgrade an OpenSearch node, rollback cannot be done in-place. You must
restore from a snapshot to a new cluster. This is different from Solr where you can often
roll back by restarting with the old binary.

**Fix:** Always take snapshots before any migration or upgrade step. Use blue-green deployment
with feature flags to route traffic.

**Sources:**
- https://github.com/opensearch-project/OpenSearch/issues/2405

### 6.3 IOPS exhaustion during migration

**The trap:** During production migration, a spike in indexing + query traffic can exhaust
IOPS on EBS volumes, causing 5xx errors with no easy recovery.

**Fix:** Pre-provision sufficient IOPS (gp3 with explicit IOPS allocation). Monitor I/O
metrics during migration. Consider off-peak migration windows.

### 6.4 Debugging is harder without Solr Admin UI

**The trap:** Solr Admin UI provides visual shard/node status, collection graphs, and easy
query testing. OpenSearch Dashboards is powerful but doesn't replicate this admin experience.
AWS managed OpenSearch further limits access to some cluster APIs.

**Fix:** Build monitoring dashboards early. Learn the `_cat` APIs:
`_cat/health`, `_cat/nodes`, `_cat/indices`, `_cat/shards`, `_cat/allocation`.
Use `_cluster/allocation/explain` for debugging yellow/red cluster states.

---

## 7. Security Differences

### 7.1 Security model is much richer (positive but complex)

**The trap:** SolrCloud has basic auth and rule-based authorization — typically requiring
external tools (Apache Ranger) for fine-grained access. OpenSearch has built-in RBAC with
document-level and field-level security, TLS, SAML, OIDC, and more. The security model
is a significant learning curve.

**Fix:** Plan security configuration early. Map existing Solr roles to OpenSearch roles.
On AWS, decide between IAM + SigV4 (simpler) and FGAC with internal user DB (more
flexible for multi-tenant scenarios).

---

## 8. Features With No Direct Equivalent

These Solr features have no 1:1 mapping and require redesign:

| Solr Feature | Status | Workaround |
|---|---|---|
| Streaming Expressions | No equivalent | Application-layer processing, OpenSearch SQL/PPL, external tools (Spark, Flink) |
| Query Elevation | No built-in | Application logic or `function_score` with high boost |
| Cross-collection joins | No equivalent | Denormalization, nested docs, application-side joins |
| DIH (Data Import Handler) | Removed in Solr 9 | Logstash, Data Prepper, NiFi, custom code |
| CDCR | Different model | Cross-cluster replication (CCR), dual-write, snapshots |
| Payload scoring | Limited support | Script scoring with stored payloads, or redesign |
| SolrCloud Admin UI | No equivalent | OpenSearch Dashboards + custom monitoring |
| Multi-field aliases | Not supported | `copy_to` catch-all field or `multi_match` |
| Custom similarity (on AWS) | Blocked | Built-in similarities only; retune BM25 |
| Highlighting fragment merge | Different behavior | Test highlighting output carefully |

---

## 9. Organizational and Process Gotchas

### 9.1 Query migration is where teams spend the most time

Every migration team underestimates query translation effort. It is mechanical but extremely
time-consuming, especially for applications with many query patterns. Catalog ALL query
patterns before starting.

**Sources:**
- https://bigdataboutique.com/blog/solr-to-opensearch-migration-deep-dive

### 9.2 Change adoption is the biggest non-technical challenge

Teams resist migration because they are comfortable with Solr tooling and fear disruption.
Without training and hands-on time, complexity causes stalls.

**Fix:** Start with a smaller, less critical index. Build expertise before tackling the main
search workload. Pair engineers with someone who knows OpenSearch.

### 9.3 Dual-write infrastructure cost surprise

Dual-write (writing to both Solr and OpenSearch during migration) doubles indexing load and
adds application complexity. Teams often forget to budget for running both systems in parallel
for 1–3 months.

**Fix:** Plan infrastructure cost explicitly. Set a hard deadline for decommissioning Solr
to prevent indefinite dual-write drift.

---

## Key External References

### Migration Guides
- [BigData Boutique — Solr to OpenSearch Deep Dive](https://bigdataboutique.com/blog/solr-to-opensearch-migration-deep-dive)
- [BigData Boutique — Schema Migration](https://bigdataboutique.com/blog/schema-migration-from-solr-to-elasticsearch-opensearch-a0072b)
- [BigData Boutique — Full Migration Guide](https://bigdataboutique.com/blog/guide-to-migrating-from-apache-solr-to-opensearch-c0e755)
- [AWS Prescriptive Guidance — Full Migration Guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-solr-opensearch/introduction.html)
- [AWS Blog — Migrate from Solr to OpenSearch](https://aws.amazon.com/blogs/big-data/migrate-from-apache-solr-to-opensearch/)
- [Canva Engineering — Solr to ES Migration](https://www.canva.dev/blog/engineering/migrating-from-solr-to-elasticsearch-and-their-differences/)
- [Jason Stubblefield — SolrCloud to OpenSearch Practitioner's Guide](https://medium.com/@mr.jason.stubblefield/from-solrcloud-to-opensearch-a-practitioners-migration-guide-d6f71df06769)

### Relevance and Scoring
- [O19s — Solr vs ES Relevancy Part 1](https://opensourceconnections.com/blog/2015/12/15/solr-vs-elasticsearch-relevance-part-one/)
- [O19s — Solr vs ES Relevancy Part 2](https://opensourceconnections.com/blog/2016/01/22/solr-vs-elasticsearch-relevance-part-two/)
- [O19s — BM25 Next Generation](https://opensourceconnections.com/blog/2015/10/16/bm25-the-next-generation-of-lucene-relevation/)
- [O19s — LTR in OpenSearch](https://opensourceconnections.com/blog/2025/12/16/a-year-of-transformation-for-learning-to-rank-in-opensearch/)
- [Elastic Blog — Practical BM25](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)
- [KMW — TF-IDF and BM25](https://kmwllc.com/index.php/2020/03/20/understanding-tf-idf-and-bm-25/)
- [Sematext — Relevance Similarity](https://sematext.com/blog/search-relevance-solr-elasticsearch-similarity/)

### Comparisons
- [BigData Boutique — Solr vs OpenSearch Comparison](https://bigdataboutique.com/blog/apache-solr-vs-opensearch-comparison-and-key-differences-d7c790)
- [Sematext — OpenSearch vs Solr](https://sematext.com/opensearch-vs-solr/)
- [HeroDevs — Solr Migration Decision Guide](https://www.herodevs.com/blog-posts/should-you-migrate-from-solr-a-developers-guide-to-the-search-stack-dilemma)

### Tools
- [o19s/solr-to-es — Schema/Query Converter](https://github.com/o19s/solr-to-es)
- [OpenSearch Migration Assistant](https://docs.opensearch.org/latest/migration-assistant/is-migration-assistant-right-for-you/)
- [O19s — Choosing Relevance Metrics](https://opensourceconnections.com/blog/2020/02/28/choosing-your-search-relevance-metric/)
- [OpenSearch — Search Quality Metrics](https://opensearch.org/blog/measuring-and-improving-search-quality-metrics/)

### Case Studies
- [Abhishek Mishra — 100M Document Migration](https://innocentcoder.medium.com/migration-of-solr-to-opensearch-a3b04ce0378f)
- [Ten Mile Square — ES Migration Case Study](https://tenmilesquare.com/resources/software-development/migrating-to-elastic-search-a-case-study/)
- [tecRacer — Solr to OpenSearch 2024](https://www.tecracer.com/blog/solr-to-opensearch-migration-2024/)
