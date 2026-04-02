# Solr Concepts: Migration-Focused Reference

This reference covers Solr architecture and features from a **migration perspective**. Focus: what must change, what has equivalents, what requires redesign.

---

## Concepts with Direct OpenSearch Equivalents

### Collections ↔ Indices

| Solr | OpenSearch | Notes |
|------|-----------|-------|
| Collection (logical group of shards) | Index (logical group of shards) | Functionally identical; naming changes in application code |
| Shard (partition of data) | Shard (partition of data) | Same semantics |
| Replica (copy of shard) | Replica shard | Same semantics |

**Migration impact:** Low. Just rename `collection=X` to `index=X` in all API calls.

### Field Types

| Solr | OpenSearch | Migration Notes |
|------|-----------|---|
| `string` | `keyword` | Exact matching, no analysis |
| `text_general` | `text` with standard analyzer | Default full-text search |
| `int`, `long`, `float`, `double` | `integer`, `long`, `float`, `double` | Direct mapping |
| `boolean` | `boolean` | Direct mapping |
| `pdate` (date with slop) | `date` | Use standard ISO 8601 format |
| `location` (LatLon) | `geo_point` | Geospatial queries differ slightly |

**Migration impact:** Low. Most types map 1:1.

### Analyzers and Tokenizers

| Solr Component | OpenSearch Equivalent | Effort |
|---|---|---|
| StandardTokenizerFactory | standard tokenizer | Low (identical) |
| LowerCaseFilterFactory | lowercase filter | Low (identical) |
| StopFilterFactory | stop filter | Low (similar; wordlist format differs) |
| PorterStemFilterFactory | porter_stem filter | Low (identical) |
| SynonymFilterFactory | synonym filter | Medium (syntax differs; needs testing) |
| EdgeNGramFilterFactory | edge_ngram filter | Low (parameters slightly different) |
| NGramFilterFactory | ngram filter | Low (parameters slightly different) |

**Migration impact:** Medium. Most filters exist; syntax and configuration differ. Test each analyzer chain.

### Faceting

| Solr | OpenSearch | Complexity |
|------|-----------|---|
| Field facet (`facet.field=X`) | Terms aggregation | Low (semantic match) |
| Range facet (`facet.range=X`) | Range aggregation | Low (semantic match) |
| Date facet (`facet.range=date, gap=+1MONTH`) | Date histogram aggregation | Low (similar semantics) |
| Pivot facet (`facet.pivot=X,Y`) | Nested aggregations | Medium (requires careful nesting) |

**Migration impact:** Low-medium. Must rewrite facet requests as aggregations.

### Sorting and Pagination

| Solr | OpenSearch | Notes |
|------|-----------|---|
| `sort=field asc` | `sort: [{field: {order: "asc"}}]` | Direct translation |
| `start=N, rows=K` | `from: N, size: K` | Direct translation; avoid for deep pagination |
| Cursor-based pagination (not built-in) | `search_after` | Better than `from/size` for large offsets |

**Migration impact:** Low. Parameter names change; semantics identical.

### Basic Queries

| Solr | OpenSearch | Effort |
|------|-----------|---|
| Lucene parser (`title:value AND status:published`) | Bool query with must/filter | Low-medium; verbose in DSL but equivalent |
| Term query (`field:exact`) | Term query | Low (identical) |
| Phrase query (`"exact phrase"`) | Match phrase | Low (identical) |
| Range query (`field:[1 TO 100]`) | Range query | Low (identical) |
| Wildcard (`field:*`) | Wildcard query | Low; less common in production; can rewrite with prefix |

**Migration impact:** Low-medium. All supported; syntax and DSL style differs.

### DocValues vs Stored Fields

| Solr | OpenSearch | Semantic |
|------|-----------|---|
| `docValues="true"` | `"doc_values": true` | Efficient column-oriented access for sorting/aggs |
| `stored="true"` | `"store": true` | Return original field in results |

**Migration impact:** Low. Enable docValues for all fields you sort/facet on.

---

## Concepts with Partial Equivalents (Caveats)

### Atomic Updates

| Aspect | Solr | OpenSearch | Caveat |
|---|---|---|---|
| Set field | `{"update": {"id": "1", "title": {"set": "new"}}}` | `_update` API with doc merge | Works for non-nested; semantics differ for arrays |
| Add to field | `{"add": {"inventory": {"inc": 5}}}` | `_update` with script | Less elegant; must write Painless script |
| Remove from array | `{"remove": {"tags": "old-tag"}}` | Not directly supported | Must read doc, filter, write back |

**Migration impact:** Medium. Redesign update logic; Solr's modifiers are more graceful.

**Gotcha:** Solr's atomic updates require all fields to be stored; OpenSearch's `_update` API is more flexible but requires explicit script logic.

### Nested Documents (Block Join)

| Aspect | Solr | OpenSearch | Difference |
|------|---|---|---|
| Indexing | `_childDocuments_` array | `nested` type (requires explicit mapping) | OpenSearch requires type declaration |
| Parent→child query | `{!child}` query parser | `nested` query with `path` | DSL required vs parser |
| Child→parent query | `{!parent}` query parser | N/A; use `nested` with reverse logic | OpenSearch less flexible; redesign queries |

**Migration impact:** High. Queries must be rewritten; consider denormalization if complex.

**Gotcha:** Solr's block join updates are atomic (entire family updated or rolled back). OpenSearch `_update` on nested docs still updates parent only; children don't auto-update.

### Grouped Results (Grouping)

| Solr | OpenSearch | Caveat |
|---|---|---|
| `group=true, group.field=X` | Terms aggregation + `top_hits` | Requires aggregation nesting |
| `group.limit=K` | Aggregation `size` parameter | Less intuitive; separate aggregation for each group |

**Migration impact:** Medium. Grouping queries must become aggregations with sub-aggregations.

### Filter Queries (fq)

| Solr | OpenSearch | Semantic |
|---|---|---|
| `fq=status:published&fq=date:[NOW-30DAYS TO NOW]` | `filter` context in bool query | Semantically identical; DSL syntax required |

**Migration impact:** Low. Concept translates cleanly to filter context (cached, non-scored).

---

## Concepts with No Equivalent (Require Redesign)

### 1. CDCR (Cross-Datacenter Replication)

**What it is:** Asynchronous replication of collections across Solr clusters (datacenters).

**Why it's unique to Solr:**
- OpenSearch uses master-replica replication within a cluster
- For multi-region, use different approach (snapshots, Kinesis, application-level dual-write)

**Migration impact:** High. Must redesign disaster recovery architecture.

**Alternative for OpenSearch:**
```
Old Solr approach:  Source DC → CDCR → Replica DC
New approach:
  - Option 1: Snapshots (async, slower, S3-based)
  - Option 2: Dual-write (application writes to both DCs)
  - Option 3: Kinesis (real-time stream, more operational overhead)
```

### 2. Custom Update Processors

**What it is:** Java classes that preprocess documents during indexing (Solr-specific feature).

**Examples:**
- `RegexReplaceProcessorFactory`: Replace field values via regex
- `CloneFieldProcessorFactory`: Copy field during indexing
- `FirstFieldValueUpdateProcessorFactory`: Use first value if multi-valued

**Why OpenSearch doesn't have them:**
- OpenSearch uses ingest pipelines (different model)
- Ingest pipelines run on data node, not cluster-wide

**Migration impact:** Medium-High. Must rewrite as:
1. Ingest pipeline (if simple transformations)
2. Application-level logic (if complex)
3. Denormalization (if critical for performance)

### 3. Complex Custom Analyzers

**What it is:** Multi-filter chains with unusual combinations (stemming + synonyms + phonetic).

**Problem:**
- Some analyzers depend on custom Solr tokenizers
- Phonetic filters may not exist in OpenSearch
- Custom filter orderings may have no parallel

**Migration impact:** Medium. Audit each analyzer:
- Common chains: 1:1 translation
- Phonetic: Find equivalent (Metaphone plugin, or redesign)
- Highly custom: Consider denormalization or pre-processing

### 4. Tlog-Based Replication Recovery

**What it is:** Solr's transaction log replication allows replicas to recover from leader via tlog replay.

**Why it's different:**
- OpenSearch uses segment-based recovery
- If replica falls behind, it requests segments, not tlogs

**Migration impact:** Low (operational). Both systems recover; behavior differs but end result same.

### 5. ZooKeeper Dependency

**What it is:** Solr uses ZooKeeper for distributed coordination (external service).

**Why it matters:**
- ZooKeeper adds operational complexity
- Network partition between Solr and ZK causes cluster issues
- ZooKeeper requires separate infrastructure (3+ nodes)

**OpenSearch alternative:**
- Embedded consensus (master nodes elect leader)
- Simpler; no external service
- But less observable from outside (can't query ZK state)

**Migration impact:** Low (but strategic). You eliminate ZooKeeper, but lose external visibility into cluster state.

---

## Pre-Migration Audit Checklist

Use this to inventory your Solr setup before migration planning.

### Schema Audit

- [ ] List all field types (`schema.xml` → `<fieldType>` tags)
- [ ] Identify custom analyzers or filters
- [ ] Count fields by type (text, keyword, numeric, date, geo)
- [ ] List dynamic field patterns (`*_s`, `*_t`, etc.)
- [ ] Document any copyField rules
- [ ] Identify nested document structures
- [ ] Check which fields use docValues
- [ ] Confirm required fields and uniqueKey

**Output:** `schema_audit.md` with field-by-field migration notes.

### Query Pattern Audit

- [ ] Export access logs (last 30 days)
- [ ] Identify unique query patterns (search, facet, grouping, sort)
- [ ] Classify by query parser (DisMax, eDisMax, Lucene)
- [ ] Count frequency of each pattern (top 100 queries)
- [ ] Document any custom request handlers
- [ ] Test each query pattern against OpenSearch DSL equivalents

**Output:** Query mapping spreadsheet with migration complexity per pattern.

### Performance Baseline

- [ ] Measure query latency (p50, p99) for top 20 queries
- [ ] Measure indexing throughput (docs/sec)
- [ ] Record index size and document count
- [ ] Baseline memory/GC behavior (JVM heap, GC pause times)
- [ ] Baseline cache hit rates (queryResultCache, filterCache)

**Output:** Baseline metrics to compare post-migration.

### Feature Inventory

- [ ] Do you use atomic updates? (Need to redesign in OpenSearch)
- [ ] Do you use nested documents? (Queries must change)
- [ ] Do you use custom analyzers/filters? (May need replacement)
- [ ] Do you use CDCR? (No equivalent; plan alternative)
- [ ] Do you use streaming expressions? (No equivalent; plan alternative)
- [ ] Do you rely on specific cache settings? (Need tuning in OpenSearch)

**Output:** Features needing redesign; prioritize effort.

### Operational Audit

- [ ] SLA requirements (availability, latency, RTO/RPO)
- [ ] Current incident rate and MTTR
- [ ] Monitoring/alerting setup (integrate into OpenSearch)
- [ ] Backup/snapshot strategy
- [ ] Failover procedures
- [ ] On-call rotation and escalation

**Output:** SLA preservation plan; validate OpenSearch meets requirements.

---

## Common Solr Patterns Causing Migration Complexity

### Pattern 1: Heavy Atomic Updates

**Symptom:** Application frequently updates specific fields (inventory, price) without full reindex.

**Why it's complex:**
- Solr's atomic updates are elegant (set, add, inc modifiers)
- OpenSearch requires explicit `_update` API with document merge or script
- For array updates (remove element), must read-modify-write

**Migration effort:** Medium-High

**Redesign options:**
1. **Accept more verbose code** (switch to `_update` with Painless scripts)
2. **Denormalize data** (store computed fields to avoid updates)
3. **Switch to event-driven architecture** (reindex on event, not update)

### Pattern 2: Complex Nested Document Hierarchies

**Symptom:** Deep nesting (product → reviews → replies → reactions).

**Why it's complex:**
- Solr's block join queries are powerful but queries get convoluted
- OpenSearch's nested queries less flexible; consider flattening

**Migration effort:** High

**Redesign options:**
1. **Flatten hierarchy** (denormalize at application level)
2. **Rewrite queries** to OpenSearch nested semantics
3. **Split into separate indices** (one per hierarchy level)

### Pattern 3: CDCR for Disaster Recovery

**Symptom:** You have CDCR replicating collection to backup DC.

**Why it's complex:**
- OpenSearch has no equivalent
- Must design alternative (snapshots, dual-write, streaming)

**Migration effort:** High

**Redesign options:**
1. **Snapshots to S3** (async, slower recovery, simpler)
2. **Kinesis for real-time sync** (operational overhead, operational cost)
3. **Application-level dual-write** (code change, but well-tested pattern)

### Pattern 4: Custom Update Processors

**Symptom:** Solr config includes custom `<updateRequestProcessorChain>`.

**Why it's complex:**
- OpenSearch doesn't have update processors
- Equivalent is ingest pipeline (different model)
- Complex Java logic requires rewrite

**Migration effort:** Medium-High

**Redesign options:**
1. **Ingest pipeline** (if transformations simple)
2. **Application pre-processing** (before sending to OpenSearch)
3. **Painless script on update** (for per-document logic)

### Pattern 5: Streaming Expressions for Large Exports

**Symptom:** Using streaming expressions to export/process millions of docs.

**Why it's complex:**
- OpenSearch has no streaming expressions equivalent
- Must use scroll API, search_after, or bulk export

**Migration effort:** Low-Medium

**Redesign options:**
1. **Bulk export via scroll/search_after** (simpler, covers 90% of use cases)
2. **Stream to files** (S3 bulk export)

---

## Decision Tree: Redesign vs Lift-and-Shift

For each feature identified in audit, ask:

```
Can this feature be easily replicated in OpenSearch?

├─ Yes: Direct equivalent exists
│  └─ Action: Translate queries/config (Low effort)
│
├─ Partially: Partial equivalent with caveats
│  ├─ Is the caveat acceptable?
│  │  ├─ Yes: Work around it (Medium effort)
│  │  └─ No: Redesign feature (High effort)
│  │
│  └─ Examples: Nested docs (caveats exist, queries change)
│             Atomic updates (caveats exist, verbose)
│
└─ No: No equivalent in OpenSearch
   ├─ Is this feature critical to business?
   │  ├─ Yes: Redesign architecture (High effort, long timeline)
   │  │   Examples: CDCR (switch to dual-write)
   │  │            Streaming Expressions (use search_after)
   │  │
   │  └─ No: Retire feature or workaround (Medium effort)
```

---

## Migration Readiness Scoring

Rate each area 1-5 (5 = no migration work needed):

| Area | Rating | Notes |
|------|--------|-------|
| Schema mapping | ✓ (4-5 typical) | Most types map 1:1 |
| Query patterns | ❌ (2-3 typical) | DisMax/eDisMax require rewrite |
| Analyzers | ✓ (3-4 typical) | Most filters exist, test each |
| Faceting | ✓ (4 typical) | Maps to aggregations cleanly |
| Atomic updates | ❌ (2 typical) | Requires code change |
| Nested docs | ❌ (1-2 if heavily used) | Queries must change |
| CDCR | ❌ (1 if used) | Redesign DR strategy |
| Custom logic | ❌ (2-3 typical) | Rewrite as ingest/application logic |

**Overall readiness = Average score**
- 4-5: Low complexity migration (6-12 weeks)
- 3-4: Medium complexity (12-24 weeks)
- 2-3: High complexity (24+ weeks; consider consulting)
- <2: Very high complexity; assess ROI of migration

---

## Summary: What Changes, What Doesn't

### Stays the Same (Operational continuity)

- Data (indexes) migrate 1:1; document structure, field values unchanged
- Multi-AZ, replication, resilience semantics equivalent
- Monitoring, alerting patterns similar
- Backup/snapshot concepts same

### Changes (Code/config updates required)

- Query syntax (Solr → OpenSearch Query DSL)
- Collection management (ZooKeeper gone; master-replica instead)
- Configuration (XML → JSON mappings)
- Schema definition (XML → JSON mappings)
- Request handlers (configuration changes)
- Custom analyzers (may need replacement)

### Redesign (Architecture changes)

- CDCR (no equivalent; use Kinesis, dual-write, or snapshots)
- Atomic updates (more verbose; redesign if critical)
- Streaming expressions (use search_after instead)
- Custom update processors (use ingest pipelines or pre-processing)
- Nested documents (queries change; consider denormalization)

**For most migrations: Expect 40-60% effort on query mapping, 20-30% on schema/configuration, 10-20% on operational changes and architecture redesign.**
