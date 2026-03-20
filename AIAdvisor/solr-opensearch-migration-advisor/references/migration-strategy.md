# Migration Strategy: Solr to OpenSearch

This reference distills the strategic choices, decision heuristics, and operational patterns for executing a Solr-to-OpenSearch migration. Use this to plan your approach before diving into implementation.

---

## Why Full Refactor Beats Lift-and-Shift

### The Lift-and-Shift Failure Modes

Attempting 1:1 porting of Solr configurations causes critical failures:

1. **Query syntax incompatibilities** (highest impact)
   - Solr's DisMax and eDisMax parsers have no direct equivalents
   - Query parameters (qf, mm, pf, bf) don't map cleanly to Query DSL
   - Failure mode: Complex queries break; must rewrite manually
   - Cost: 40-60% of migration effort spent on query mapping

2. **Relevance scoring divergence**
   - Solr defaults to TF-IDF; OpenSearch uses BM25
   - Even identical data ranks differently
   - Failure mode: Users see "wrong" results; business credibility damaged
   - Symptom: Top-10 result overlap < 60%

3. **Operational model differences**
   - Solr's ZooKeeper coordination vs OpenSearch's embedded consensus
   - Solr's shard leader election vs OpenSearch's quorum-based
   - Failure mode: Operational assumptions break (timeouts, scaling)

4. **Schema translation friction**
   - Solr's XML schema ↔ OpenSearch's JSON mappings
   - Dynamic field naming patterns (_s, _t, _i) don't auto-translate
   - Analyzer chains map differently; custom filters may not exist
   - Failure mode: Analyzer behavior diverges; text analysis breaks

5. **Feature gaps that cause redesign**
   - Atomic updates (Solr's set/add/inc) behave differently in OpenSearch
   - Nested documents use block-join in Solr vs nested type in OpenSearch
   - CDCR (cross-datacenter replication) has no parallel in OpenSearch
   - Failure mode: Critical application features must be redesigned

### The Full Refactor Approach

Accept that OpenSearch is a different platform requiring intentional design:

1. **Audit source state** (1-2 weeks)
   - Document all active queries, faceting patterns, sorting behavior
   - Identify performance-critical query patterns
   - Measure baseline latency, throughput, relevance quality
   - Extract analyzer chain definitions and custom filters
   - **Output**: Query inventory, schema audit, relevance baseline

2. **Design OpenSearch target** (2-3 weeks)
   - Map Solr queries to Query DSL using conceptual equivalence, not mechanical translation
   - Design mappings with OpenSearch idioms (filter context, nested queries, aggregations)
   - Plan analyzer chains; identify custom filters needing replacement
   - Prototype relevance tuning (BM25 vs TF-IDF differences)
   - **Output**: OpenSearch mapping template, query DSL examples, tuning knobs

3. **Dual-write validation** (3-4 weeks)
   - Implement dual-write logic (application writes to both)
   - Run shadow reads: execute queries against both, compare results
   - Identify and fix query mapping bugs
   - Build correction matrices for known divergences
   - **Output**: Query mapping completeness; residual divergence < 5%

4. **Gradual traffic shift** (2-4 weeks)
   - Route 5% of production queries to OpenSearch
   - Monitor latency, error rate, result quality at each tier
   - Have rollback procedures ready (< 60 seconds to flip back)
   - **Output**: Confidence that OpenSearch can handle production load

5. **Maintain rollback path** (30-90 days post-migration)
   - Keep Solr operational and indexed during cutover window
   - If bugs emerge, revert to Solr without data loss
   - **Output**: Zero production data loss if cutover fails

---

## Dual-Write with Historical Catchup Pattern

### Architecture: Writing to Both Systems

```
Application Layer
       ↓
    [Dual-Write Logic]
       ↙        ↘
    Solr      OpenSearch
  (Primary)    (Secondary)
```

Write ordering is critical:
- **Write to OpenSearch first** (async, fire-and-forget) — fail silently if OpenSearch is unavailable
- **Write to Solr second** (sync, critical path) — fail fast if Solr unavailable
- This ensures Solr remains source of truth if OpenSearch write fails

### Implementation Phases

#### Phase 1: Dual-Write, Solr-Primary Reads (1-2 weeks)

**What to do:**
- Write every document to both Solr and OpenSearch
- Read all queries from Solr only
- Asynchronously compare search results (background job)
- Identify query mapping issues without impacting users

**Metrics to track:**
- Write latency p99 (should increase <50ms due to OpenSearch write)
- OpenSearch write error rate (target: <0.1%)
- Result divergence rate by query pattern

**Success criteria:**
- 99.9% of documents successfully written to both systems
- No user-facing latency increase > 50ms p99
- Query divergence baseline established

#### Phase 2: Shadow Reads (2-4 weeks)

**What to do:**
- Continue dual-write
- Execute every user query against both systems
- Log results but return only Solr results to users
- Monitor latency, relevance, functional correctness

**Metrics to track:**
- Query latency (Solr p99 vs OpenSearch p99)
- Top-10 result overlap percentage
- Error rate divergence (exceptions in OpenSearch vs Solr)
- Timeout rate (queries taking >5s)

**Success criteria:**
- OpenSearch latency within ±20% of Solr baseline
- Top-10 overlap > 80% across query types
- Error rate divergence < 0.5%

#### Phase 3: Gradual Traffic Shift (2-4 weeks)

**Tier progression: 5% → 25% → 50% → 100%**

At each tier:
1. Route percentage to OpenSearch for 24-48 hours
2. Monitor go/no-go criteria
3. If failures detected, rollback (< 60 seconds)
4. Fix issues; move to next tier

**Go/No-Go Criteria (per tier):**

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate | > 0.1% | **No-go**: Rollback; debug |
| p99 latency | > 1.5x Solr baseline | **No-go**: Optimize queries |
| Result divergence | > 5% | **No-go**: Fix query mappings |
| User complaints | > 2/hour | **No-go**: Halt shift |
| Success rate (2-hour window) | < 99.9% | **Pause**: Stabilize before advancing |

#### Phase 4: Historical Data Catchup (parallel to Phase 3)

**Problem:** Documents created before dual-write started are only in Solr.

**Solution:**
- Identify documents with timestamp < cutover date
- Reindex these documents to OpenSearch in bulk
- Use `refresh_interval=-1` during bulk to maximize throughput
- Set `refresh_interval: "1s"` after bulk completes

**Implementation:**
```
1. Query Solr: SELECT * WHERE created_at < cutover_date
2. Transform documents to OpenSearch format
3. Bulk index with refresh_interval=-1 (throughput: 10K-50K docs/sec)
4. Set refresh_interval="1s" and force refresh
5. Verify document count matches: count(Solr) == count(OpenSearch)
```

**Timing:** Run this in parallel with Phases 2-3 to minimize post-cutover data gap.

### Critical Implementation Details

**Idempotency Requirements:**
- Both systems must handle document re-indexing gracefully
- Network failures may cause retries; duplicate writes must be safe
- Use document ID as idempotency key
- Include write timestamp in both systems to detect divergence

**Timestamp-Based Auditing:**
- Add `_updated_at` timestamp to every document during write
- Query timestamp ranges to identify documents that diverged
- Run periodic audits: count(Solr where timestamp > T) vs count(OpenSearch where timestamp > T)

**Dual-Write Ordering:**
```kotlin
// CORRECT: Fail-open pattern
try {
    openSearchClient.index(doc)  // Fire-and-forget async
} catch (e: Exception) {
    logger.warn("OpenSearch write failed; continuing to Solr", e)
}
solrClient.add(doc)  // Must succeed
if (solrClient.commit() fails) throw Exception  // Fail if Solr fails

// WRONG: Would lose Solr data if OpenSearch succeeds but Solr fails
openSearchClient.index(doc)  // Succeeds
solrClient.add(doc)  // Fails → silent data loss
```

---

## Gradual Traffic Shift Strategy

### 5% → 25% → 50% → 100% Progression

**Why small increments?**
- Each tier exposes different failure modes (cache misses, connection pools, GC)
- Reduces blast radius if issues emerge
- Allows operational learning before full cutover

**Tier 1: 5% (24-48 hours)**
- Route 5% of read queries to OpenSearch
- Monitor: error rate, p99 latency, timeouts
- Expected findings: Connection pool sizing, GC behavior, network latency
- **Decision point:** If all metrics green, advance to 25%

**Tier 2: 25% (1 week)**
- Many issues surface here (cache effectiveness, query plan misses)
- Have engineering on-call for debugging
- Expected findings: Query performance regressions, missing indices
- **Decision point:** If error rate < 0.1%, advance to 50%

**Tier 3: 50% (1 week)**
- Run in true parallel; half of traffic each direction
- This is your true production validation
- Expected findings: Rare edge cases, specific query patterns problematic
- **Decision point:** If monitoring shows confidence > 95%, advance to 100%

**Tier 4: 100% (cutover day)**
- All reads go to OpenSearch
- Solr remains indexed but read-only
- Keep Solr operational for 30 days

### Rollback Procedures

**Automatic triggers (real-time monitoring):**
```
Error rate > 0.1% for 5 minutes → Page on-call
p99 latency > 2x baseline for 5 minutes → Page on-call
Timeouts > 1% → Auto-rollback to Solr
Circuit breaker: 10 consecutive OpenSearch failures → Auto-rollback
```

**Manual rollback (< 60 seconds):**
```kotlin
// In load balancer or application config
if (rollback_triggered) {
    routing_destination = SOLR  // Flip switch
    // All new queries route to Solr
    // In-flight OpenSearch queries drain (timeout after 5s)
}
```

**Post-rollback actions:**
1. Disable OpenSearch writes (stop dual-write)
2. Preserve OpenSearch data (for analysis)
3. Debug root cause
4. Fix issues
5. Attempt re-cutover only after fixing

**30-Day Retention:**
- After cutover, keep Solr indexed and accessible for 30 days
- If critical bugs emerge in OpenSearch, you can:
  1. Disable OpenSearch reads
  2. Redirect traffic to Solr
  3. Preserve user data without re-indexing

---

## Phase Timeline with Realistic Estimates

### Full Migration Timeline (90-180 days)

| Phase | Duration | Key Activities | Deliverables |
|-------|----------|---|---|
| Planning & Audit | 2-3 weeks | Query inventory, schema audit, baseline metrics | Query DSL mapping doc, OpenSearch design |
| Design & Prototyping | 2-3 weeks | Map queries, design mappings, prototype relevance | Test mappings, query examples, tuning knobs |
| Dual-Write Implementation | 1-2 weeks | Code dual-write logic, shadow read infrastructure | Dual-write service, comparison framework |
| Validation (Phase 1) | 1-2 weeks | Dual-write with Solr reads, compare results | Query mapping completeness > 95% |
| Shadow Reads (Phase 2) | 2-4 weeks | Shadow execution, result comparison, debugging | Divergence baseline < 5%, latency baseline |
| Historical Data Reindex | 2-3 weeks | Bulk reindex from Solr, verify completeness | 100% document count match |
| Gradual Shift (Phase 3) | 2-4 weeks | 5% → 25% → 50% → 100% progression | Production validation, no issues at each tier |
| **Total** | **12-19 weeks** | | **Full cutover** |
| Post-Cutover (monitoring) | 30-90 days | Monitor OpenSearch stability, debug edge cases | Zero incidents, decommission Solr |

### Risk Buffer

- Add 2 weeks for issues discovered during traffic shift
- Add 1 week for query optimization if divergence > 5%
- Add 1 week for infrastructure tuning (connection pools, GC)

**Realistic end-to-end: 4-6 months for enterprise deployment**

---

## Decision Tree: Choosing Data Migration Approach

Choose based on data size, complexity, source availability:

```
START: How much data?

├─ < 10 GB
│  └─ Use: Lambda + S3 (hours, $5-20)
│     Why: Overhead not worth it
│
├─ 10-100 GB
│  ├─ Complex transformations needed?
│  │  ├─ Yes → Use: Glue ETL (hours-days, $20-100)
│  │  │   Why: Spark handles joins/aggregations
│  │  └─ No → Use: Logstash on Fargate (hours, $100-300)
│  │      Why: Lightweight, reliable
│  │
│  └─ Already have transformation logic?
│     ├─ Yes → Custom ETL (days, $500-2000)
│     │   Why: Reuse existing logic
│     └─ No → Logstash
│
├─ 100 GB - 5 TB
│  └─ Use: Logstash on Fargate (days, $500-2000)
│     Why: Proven, flexible, scales
│
├─ 5-50 TB
│  └─ Use: Logstash on Fargate (multi-task) + Kinesis (days-weeks, $1000-5000)
│     Why: Parallelism + real-time sync capability
│
└─ > 50 TB
   └─ Use: Custom multi-stage ETL + consulting (weeks-months, custom)
      Why: Need deep optimization
```

### Detailed Decision Matrix

| Factor | Reindex-from-Source | Logstash | Custom ETL | Glue |
|--------|---|---|---|---|
| Data size | Any | 100GB-10TB | Any | 10GB-5TB |
| Transformation complexity | Low | Medium | High | Medium |
| Time to implement | 1-2 weeks | 1 week | 2-3 weeks | 1 week |
| Operational overhead | Low | Medium | High | Low |
| Cost | $100-500 | $500-2000 | $1000-5000 | $500-1000 |
| When to use | Have DB source | ETL needed, flexible | Complex logic | Join heavy |

---

## Rollback Plan: What to Keep, For How Long

### Post-Cutover Solr Role

**Keep Solr operational for 30-90 days after cutover:**

```
Days 1-7:   Full operational readiness (all writes dual, reads switchable)
Days 8-30:  Read-only (no new writes, can revert if bugs found)
Days 31-90: Archival (snapshot for forensics, rare emergency access)
```

**Solr during post-cutover phase:**
- Stop all new writes (only OpenSearch indexed)
- Keep indices available for rapid switchback
- Monitor cost vs risk (often easier to re-index than maintain)
- After 30 days, most edge cases found; decommission if clean

**Switchback timeline (if needed):**
1. Detect OpenSearch failure (< 5 min)
2. Flip routing to Solr (< 1 min)
3. Investigate root cause (hours)
4. Fix OpenSearch (hours-days)
5. Re-cutover to OpenSearch

**Cost of keeping Solr 30 days:**
- Instance hours: ~$300 (r6g.xlarge × 30 days)
- Storage: ~$50 (snapshot retention)
- Total: ~$350 (often cheaper than emergency re-index)

---

## Summary: Checklists for Each Phase

### Pre-Migration
- [ ] Document all active queries and their frequency
- [ ] Baseline relevance metrics (top-10 overlap within same system)
- [ ] Baseline latency (p50, p99)
- [ ] Inventory analyzers, filters, custom query parsers
- [ ] Identify performance-critical query patterns

### Design Phase
- [ ] Map Solr queries to Query DSL
- [ ] Design OpenSearch mappings
- [ ] Create analyzer chain translations
- [ ] Prototype relevance tuning (BM25 parameters)
- [ ] Plan shard count and replica strategy

### Implementation
- [ ] Implement dual-write logic with idempotency
- [ ] Build shadow read infrastructure
- [ ] Reindex historical data to OpenSearch
- [ ] Set up monitoring dashboards

### Validation (Phases 1-3)
- [ ] Run Phase 1 (dual-write, Solr reads) for 1-2 weeks
- [ ] Run Phase 2 (shadow reads) for 2-4 weeks
- [ ] Reindex historical data (2-3 weeks, in parallel)
- [ ] Execute gradual traffic shift (5% → 25% → 50% → 100%)
- [ ] Monitor go/no-go criteria at each tier

### Cutover
- [ ] All queries successfully routed to OpenSearch
- [ ] Document count matches between Solr and OpenSearch
- [ ] Rollback procedures tested and ready
- [ ] Solr kept operational for 30 days

### Post-Cutover (30-90 days)
- [ ] Monitor for anomalies (latency, error rate, result quality)
- [ ] Debug edge cases as they surface
- [ ] After 30 days, decommission Solr if stable
