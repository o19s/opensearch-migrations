# Solr to OpenSearch Incompatibilities Steering

Use this reference when analyzing Solr configurations and producing migration reports.
For each incompatibility found, state severity and recommend a concrete remediation.

Severity levels:
- **Breaking** — Migration fails or produces errors without remediation
- **Behavioral** — Silently different behavior; results/performance change without errors
- **Unsupported** — Feature has no direct equivalent; requires architectural change

---

## Query Gaps

### Function Queries
**Severity: Breaking**

Solr `bf=sqrt(views)^2 log(1+clicks)` has no inline equivalent. OpenSearch requires
`function_score` with `script_score` or `field_value_factor`.

```json
{
  "function_score": {
    "query": { "match": { "title": "solr" } },
    "functions": [{
      "script_score": {
        "script": "Math.sqrt(doc['views'].value) * Math.log(1 + doc['clicks'].value)"
      }
    }]
  }
}
```

**Remediation**: Translate each `bf`/`bq` function to a `function_score` function.
For high-QPS use cases, pre-compute boost scores at index time to avoid script overhead.

### MoreLikeThis (MLT)
**Severity: Breaking**

Solr MLT handler (`/mlt?q=id:123&mlt.fl=title,body`) becomes a dedicated query type.

```json
{ "more_like_this": { "fields": ["title","body"], "like": [{"_id": "123"}] } }
```

**Remediation**: Rewrite MLT handler calls to `more_like_this` query. Parameter names
differ (`mlt.mintf` -> `min_term_freq`, `mlt.mindf` -> `min_doc_freq`).

### Spatial Queries
**Severity: Breaking**

Solr `latlon`/`SpatialRecursivePrefixTreeFieldType` map to `geo_point` and `geo_shape`.
Solr `{!geofilt}` becomes `geo_distance` query; `{!bbox}` becomes `geo_bounding_box`.

**Remediation**: Convert field types in mapping. Rewrite spatial filter queries to
OpenSearch geo query DSL. Verify coordinate order (Solr uses `lat,lon`; OpenSearch
uses `[lon,lat]` in GeoJSON or `{"lat":x,"lon":y}` object form).

### Relevance Scoring (TF-IDF vs BM25)
**Severity: Behavioral**

Solr defaults to TF-IDF; OpenSearch defaults to BM25. BM25 saturates term frequency,
so documents stuffed with repeated terms score lower than in TF-IDF. Expect 30-40%
difference in top-10 results without tuning.

**Remediation**: Run shadow queries comparing top-10 overlap for 2-4 weeks before
cutover. If results diverge unacceptably, tune BM25 `k1`/`b` parameters per-field:

```json
{
  "settings": { "index": { "similarity": {
    "tuned_bm25": { "type": "BM25", "k1": 1.2, "b": 0.75 }
  }}},
  "mappings": { "properties": {
    "title": { "type": "text", "similarity": "tuned_bm25" }
  }}
}
```

### Custom Similarity Classes
**Severity: Unsupported**

Solr allows custom Java similarity plugins (`<similarity class="com.x.Custom"/>`).
OpenSearch cannot load custom similarity code at runtime.

**Remediation**: (1) Rewrite as `function_score` + `script_score`, (2) accept BM25,
or (3) build a re-ranking microservice that scores top-N candidates externally.

---

## Feature Gaps

### Dynamic Fields / Schemaless Mode
**Severity: Behavioral**

Solr schemaless indexes everything as text. OpenSearch dynamic mapping infers types
aggressively: `"123"` becomes `long`, `"2024-01-15"` becomes `date`, `"true"` becomes
`boolean`. Queries that worked on text fields break on numeric fields.

**Remediation**: Disable dynamic mapping (`"dynamic": false`) and define explicit
mappings. Or use `dynamic_templates` to force all strings to `text`:

```json
{ "dynamic_templates": [{ "strings_as_text": {
    "match_mapping_type": "string",
    "mapping": { "type": "text", "fields": { "keyword": { "type": "keyword" } } }
}}]}
```

### Nested Documents
**Severity: Breaking**

Solr `_childDocuments_` / block-join queries map to OpenSearch `nested` type or
`join` field (parent-child). The query syntax is completely different.

**Remediation**: Map child documents as `nested` objects (preferred for performance)
or use `join` field type for true parent-child relationships. Rewrite all
`{!parent}`/`{!child}` queries to `nested` or `has_child`/`has_parent` queries.

### Joins
**Severity: Unsupported**

Solr `{!join from=X to=Y}` has no direct equivalent. OpenSearch offers `terms` lookup
query (cross-index), `nested` query, or denormalized index design.

**Remediation**: Prefer denormalization at index time. For large join cardinalities,
use `terms` lookup query or application-side join.

### Atomic Updates / Optimistic Locking
**Severity: Behavioral**

Solr atomic updates use `_version_` for concurrency control. OpenSearch partial updates
use `seq_no` + `primary_term` instead. If your code relies on Solr version checking,
the concurrency model must be ported.

```
PUT /index/_update/id?if_seq_no=5&if_primary_term=1
{ "doc": { "price": 9.99 } }
```

**Remediation**: Replace `_version_` checks with `if_seq_no`/`if_primary_term`.
Use `doc_as_upsert: true` if the document may not yet exist.

### Commit / Refresh Semantics
**Severity: Behavioral**

Solr soft commit ~ OpenSearch refresh. Solr hard commit = refresh + fsync; OpenSearch
separates these. Default `refresh_interval` is 1s, so documents are not instantly
searchable after indexing (unlike Solr's default immediate soft commit).

**Remediation**: Set `refresh_interval` to match application needs. During bulk
migration, set to `"-1"` (disabled) and re-enable after. For near-real-time apps,
`"100ms"` works but increases indexing overhead.

---

## Infrastructure Gaps

### Shard Collocation
**Severity: Breaking**

Solr allows primary + replica of the same shard on one node. OpenSearch forbids this.
A Solr cluster running 3 nodes with 4 shards + 1 replica (8 shard copies, collocated)
needs minimum 8 nodes in OpenSearch.

**Remediation**: Calculate minimum nodes as `shards * (1 + replicas)`. Budget 30%
extra capacity for OpenSearch's higher per-shard memory overhead.

### ZooKeeper Removal
**Severity: Behavioral**

Solr's external ZooKeeper provides independent cluster state inspection. OpenSearch
embeds cluster state in master nodes — no external observability tool.

**Remediation**: Deploy minimum 3 dedicated master-eligible nodes (5 for production).
Implement `_cluster/health` monitoring, Prometheus alerting on cluster status, and
document recovery runbooks for master/data node failures.

### JVM Tuning
**Severity: Behavioral**

OpenSearch defaults to 2GB heap (vs Solr's typical 8GB+). OpenSearch uses more memory
per shard. Migrating with default JVM settings causes OOM errors and GC pauses.

**Remediation**: Set heap to 50% of system RAM, capped at 31GB (`-Xms16g -Xmx16g`).
Use G1GC. Tune `-XX:MaxGCPauseMillis=30` for low-latency query workloads.

### Write Latency / Replication
**Severity: Behavioral**

Solr leader election allows unacknowledged replica writes. OpenSearch waits for in-sync
replicas by default, adding 100-400ms write latency.

**Remediation**: Tune `write.wait_for_active_shards`: `1` = primary-only (fast, weaker
consistency), `"all"` = full consistency (slow). Default is quorum.

---

## Plugin Gaps

### Custom Request Handlers
**Severity: Unsupported**

Solr request handlers (`/select`, `/spell`, custom endpoints) have no equivalent.

**Remediation**: Rebuild custom handler logic as application-layer code calling the
standard OpenSearch `_search` API. Simple handlers often become a single query template.

### Search Components (spellcheck, suggest, grouping)
**Severity: Breaking**

Solr search components (spellcheck, suggest, stats, grouping) are configured in
`solrconfig.xml`. OpenSearch equivalents exist but use different APIs:
- Spellcheck -> `suggest` API or `phrase` suggester
- Grouping -> `collapse` field or `terms` aggregation
- Stats -> `stats` aggregation

**Remediation**: Inventory all active search components. Map each to its OpenSearch
equivalent API. Some (like custom chain components) require application-layer reimplementation.

### Connection Pooling / Client Libraries
**Severity: Behavioral**

SolrJ and OpenSearch clients have different default pool sizes and behaviors. Pool
exhaustion under load is common post-migration.

**Remediation**: Explicitly configure `maxConnPerRoute` and `maxConnTotal` in the
OpenSearch REST client. Match or exceed the concurrency level of your application threads.

### Monitoring / Admin UI
**Severity: Behavioral**

Solr's built-in Admin UI has no OpenSearch equivalent. OpenSearch Dashboards is a
separate service that must be deployed and configured.

**Remediation**: Deploy OpenSearch Dashboards. Set up Prometheus + Grafana for cluster
health, query latency (p50/p95/p99), indexing rate, JVM heap, and shard status.

---

## Quick Reference: Severity by Category

| Incompatibility | Severity | Category |
|---|---|---|
| Function queries | Breaking | Query |
| MLT syntax | Breaking | Query |
| Spatial queries | Breaking | Query |
| Scoring (TF-IDF vs BM25) | Behavioral | Query |
| Custom similarity | Unsupported | Query |
| Dynamic field mapping | Behavioral | Feature |
| Nested documents | Breaking | Feature |
| Joins | Unsupported | Feature |
| Atomic updates / versioning | Behavioral | Feature |
| Commit / refresh | Behavioral | Feature |
| Shard collocation | Breaking | Infra |
| ZooKeeper removal | Behavioral | Infra |
| JVM tuning | Behavioral | Infra |
| Write latency | Behavioral | Infra |
| Custom request handlers | Unsupported | Plugin |
| Search components | Breaking | Plugin |
| Client connection pooling | Behavioral | Plugin |
| Admin UI / monitoring | Behavioral | Plugin |
