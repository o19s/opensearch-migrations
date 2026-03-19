# Solr Architecture & Concepts: Migration Evaluation Guide

## Table of Contents
1. [SolrCloud Architecture](#solrcloud-architecture)
2. [Collection vs Core](#collection-vs-core)
3. [Configuration Management](#configuration-management)
4. [Lucene Layer](#lucene-layer)
5. [Replication Models](#replication-models)
6. [Transaction Logs & Commits](#transaction-logs--commits)
7. [Resilience & Split Brain](#resilience--split-brain)
8. [Cross-Datacenter Replication](#cross-datacenter-replication)
9. [Admin UI & Operations](#admin-ui--operations)
10. [Operational Pain Points](#operational-pain-points)

---

## SolrCloud Architecture

### ZooKeeper Ensemble

SolrCloud relies on a ZooKeeper ensemble for distributed coordination. The ensemble manages:

- **Cluster state**: Which nodes are active, which collections exist, shard assignments
- **Configuration distribution**: Centralized storage of configsets (schema + solrconfig)
- **Leader election**: Automatic election of shard leaders when nodes join/leave
- **Overseer coordination**: A designated node manages complex state transitions

**Ensemble best practices:**
- Minimum 3 nodes for production (1 fails, 1 lags, 1 leads)
- 5 nodes recommended for larger clusters to tolerate 2 simultaneous failures
- ZooKeeper ensemble can be separate from Solr nodes or co-located; co-location trades availability for simplicity
- Typical network latency between Solr and ZK should be <50ms; high latency causes frequent re-elections

### Overseer

The Overseer is a single Solr node elected by the ZooKeeper ensemble to orchestrate:

- Shard leader elections during node failures
- Collection creation/deletion
- Replica placement decisions
- State transitions (DOWN → ACTIVE, etc.)

**Overseer bottleneck**: In clusters with high churn (nodes frequently joining/leaving), the Overseer becomes a bottleneck. All state changes queue through it. A slow Overseer can delay replica recovery, causing temporary search latency increases.

**Overseer observations:**
- If a node crashes while serving as Overseer, ZK detects its loss and elects a new Overseer (~1-2 seconds)
- The Overseer node itself still serves search traffic normally; it's not dedicated infrastructure
- Monitor `overseer_queue` metrics; sustained queue depth >100 indicates bottleneck

### Leader Election

When a shard leader goes down:

1. ZooKeeper detects the node absence (via heartbeat timeout, configurable)
2. Overseer is notified and coordinates election among remaining replicas
3. One replica is elected leader; others become followers
4. New leader immediately begins accepting writes
5. Followers update their state and begin replicating from the new leader

**Election time**: Typically 5-15 seconds in healthy clusters. During this window, writes to that shard will fail; reads from followers continue.

### Shard Leaders & Replicas

A collection is partitioned into N shards. Each shard has:

- **1 leader**: Accepts all writes for that shard's documents. Assigns version numbers.
- **1+ replicas**: Read-only copies that replicate from the leader. Can serve queries.

Documents are routed to shards via a hash of the `uniqueKey` field. Queries span all shards and merge results.

**Leader behavior:**
- Maintains transaction log (tlog) of all updates
- Assigns global version numbers to documents
- Forwards updates to all replicas (asynchronously by default)
- Can go down without losing data (tlog survives; new leader reconstructs state)

**Replica behavior:**
- Pulls updates from leader via tlog replication
- Can be promoted to leader if leader fails
- Can be safely removed/restarted without data loss
- If a replica falls behind, it can recover by replaying missing tlogs or doing a full snapshot

---

## Collection vs Core

### Core (Standalone or Legacy)

A Core is a single searchable index instance on a Solr node. In standalone Solr:
- Each core is independent; no distributed coordination
- Updates don't replicate automatically (you set up master-replica manually)
- Configuration is stored on the node's filesystem
- No automatic recovery from node failure

### Collection (SolrCloud)

A Collection is a logical index distributed across a cluster:
- Composed of N shards, each shard has a leader + replicas
- Configuration is stored in ZooKeeper, distributed to all nodes running that collection
- Automatic replication from leader to replicas within each shard
- Automatic leader election on failure
- Queries transparently scatter to all shards and gather results

**What SolrCloud adds:**
- Automated failover: Lost node → new leader elected within 10 seconds
- Config management: Change schema, redeploy to entire cluster atomically
- Elasticity: Add/remove nodes; Solr automatically rebalances replicas
- Multi-datacenter support: CDCR can replicate collections across DCs

**Migration implication**: If you're moving from a custom master-replica setup, SolrCloud's automation reduces operational toil significantly. If you had a highly tuned singleton architecture, you trade simplicity for distribution complexity.

---

## Configuration Management

### Configsets in ZooKeeper

In SolrCloud, a configset is a directory containing:
- `schema.xml` (or schema files if using managed schema)
- `solrconfig.xml`
- Custom query parsers, analyzers, components
- Velocity templates (for response formatting)

**Deployment flow:**
1. Upload configset to ZooKeeper: `solr zk upconfig -z zk1:2181 -n my_config -d /path/to/config`
2. Reference configset when creating a collection: `POST /admin/collections?action=CREATE&name=mycol&configName=my_config`
3. Solr nodes watch ZK paths; changes propagate within seconds
4. No node restart required

### Schema: Static vs Managed

**Static schema.xml:**
- Schema defined in XML file
- Edited offline, uploaded to ZK
- Provides explicit control; no runtime mutations
- Required for complex analyzer chains with custom token filters

**Managed schema (field auto-expansion):**
- Solr creates/modifies fields at runtime via Schema API
- `POST /schema/fields` creates new fields dynamically
- Backed by ZK storage
- Convenient for ingestion pipelines that discover fields on-the-fly
- Trade-off: Less control; risk of unintended field creation if not carefully gated

**SchemaAPI:**
- `GET /schema` returns current schema as JSON
- `POST /schema/fields` adds a field
- `PUT /schema/fields/fieldname` modifies a field
- `DELETE /schema/fields/fieldname` removes a field

### solrconfig.xml

Defines request handlers, query parsers, update processors, and performance tuning:

- **Request handlers** (`<requestHandler>`): Maps URL paths to handler classes (select, update, query, custom)
- **Update chain** (`<updateRequestProcessorChain>`): Processors run before/after documents are indexed
- **Query parsers**: Defines behavior of eDisMax, DisMax, Lucene syntax
- **Cache configuration**: resultCache, filterCache, queryResultCache - sizes and warm-up behavior
- **Merge factor & commit settings**: How often Lucene segments merge, commit strategies
- **JVM memory allocation**: Not in solrconfig (that's SOLR_HEAP env var)

---

## Lucene Layer

Solr is built on Lucene, which provides the actual inverted index and search engine. Understanding Lucene internals explains Solr's behavior and tuning levers.

### Segments & Merging

Lucene stores the index as multiple segments (sub-indexes). Each segment:
- Is immutable once written
- Has its own term dictionary, posting lists, and per-document data (docValues, stored fields)
- Can be searched independently or merged with others

**Why multiple segments?** When you add a new document:
1. It goes into a buffer in RAM
2. When buffer fills (or on commit), a new segment is written to disk
3. Multiple segments now exist; they're searched together
4. Periodically, smaller segments are merged into larger ones

**Merge process:**
- Multiple segment readers are combined into a single new segment
- All per-document deletion flags are applied
- New segment is written; old segments deleted
- This is I/O intensive and can cause query latency spikes

**tunning merges** in solrconfig.xml:
```xml
<mergeFactor>10</mergeFactor>
<!-- Merge when ~10 segments exist. Lower = more frequent merges (worse query perf), higher = larger merges (worse update latency) -->
<maxMergeDocs>2147483647</maxMergeDocs>
<!-- Don't merge segments larger than this -->
<ramBufferSizeMB>100</ramBufferSizeMB>
<!-- Buffer in RAM before flushing a segment to disk -->
```

### Commits: Hard vs Soft

A **hard commit** (or "traditional commit"):
- Calls `IndexWriter.commit()` in Lucene
- Flushes all in-memory changes to disk
- Updates the `IndexSearcher` to point to the new index files
- Makes changes durable; safe if the JVM crashes

A **soft commit**:
- Opens a new `IndexSearcher` without flushing to disk
- Changes are visible to search but not yet durable
- If JVM crashes before a hard commit, soft-committed changes are lost (but can be replayed from tlog)
- Faster than hard commits (no fsync to disk)

**Typical SolrCloud strategy:**
- Soft commit every 100ms to 1s (keep search results fresh)
- Hard commit every 5-60 seconds (balance durability vs write performance)
- The transaction log ensures durability even if hard commit is delayed

### Near-Real-Time (NRT) Search

NRT allows indexing and searching to happen nearly simultaneously:
- Documents are added to a buffer and become searchable via soft commit
- No need to wait for hard commit (fsync to disk)
- Solr can open new searchers very quickly because only the in-memory buffer and recent segments are involved

**NRT implications:**
- Soft commits are critical for search freshness in high-throughput clusters
- Higher soft-commit frequency = lower search latency but more searcher overhead (memory, CPU)
- Trade off search freshness (soft-commit frequency) against searcher/cache overhead

---

## Replication Models

### SolrCloud (Shard-Level Replication)

In SolrCloud, replication happens at the shard level:
- Leader receives write
- Applies write locally
- Forwards write to all in-sync replicas (ISR list)
- Replicas pull the transaction log and apply the same write

**Advantages:**
- Automatic: no manual configuration
- Partition-aware: each shard has its own leader, improving resilience
- Scales: adding replicas doesn't increase load on a single leader

**Disadvantages:**
- ZooKeeper dependency: no ZK = no shard leadership
- Complex state machine: potential for subtle bugs in extreme failure scenarios

### Legacy Master-Replica (Single Master)

Before SolrCloud, Solr supported a simple master-replica pattern:
- One "master" node accepts writes
- Multiple "slave" replicas pull from master via HTTP polling
- No automatic leader election

**Why it's legacy:**
- Single master is a bottleneck and SPOF
- Replicas must be manually configured and monitored
- No built-in failure detection or recovery

**Still used when:**
- You have a single-machine deployment that must withstand brief downtime
- You're migrating gradually from older Solr versions
- You want simple, predictable replication behavior without ZK

---

## Transaction Logs & Commits

### Transaction Log (Tlog)

Each Solr node maintains a transaction log (`tlog`), a write-ahead log of all updates:
- New updates are appended to the tlog **before** being applied to the index
- If the JVM crashes, the tlog can be replayed to recover uncommitted changes
- The tlog is kept on disk; it persists across restarts

**Tlog file layout:**
```
$SOLR_BASE/server/solr/<corename>/data/tlog/
  tlog.0000000000000001
  tlog.0000000000000002
  ...
```

Each tlog file is a fixed size (~1 GB by default). When full, a new file is created. Old files are cleaned up after a hard commit syncs them to the index.

### Soft Commit vs Hard Commit

**Soft Commit:**
- `softCommit=true` in request parameters or via auto-commit config
- Opens new searcher, makes changes visible to queries
- Changes are in the buffer and recent segment files (still in OS cache, not fsync'd)
- Lost if JVM crashes before a hard commit

**Hard Commit:**
- `commit=true` or `commitWithin=5000` in request parameters
- Calls `IndexWriter.commit()`
- Fsync's index files to disk (durable)
- Updates on-disk index; can be served immediately after restart

**Durability guarantee in SolrCloud:**
Even if a replica crashes before hard commit:
1. Tlog is written to disk before update is applied to buffer
2. If replica restarts, tlog is replayed from disk
3. Updates are reapplied to the index
4. This is why tlog is safe even without frequent hard commits

### Default Autocommit Configuration

Typical solrconfig.xml includes:
```xml
<autoCommit>
  <maxDocs>10000</maxDocs>
  <maxTime>5000</maxTime>
</autoCommit>

<autoSoftCommit>
  <maxTime>100</maxTime>
</autoSoftCommit>
```

This means:
- Hard commit every 10,000 docs or 5 seconds
- Soft commit every 100ms
- Results are searchable within 100ms, durable within 5 seconds

---

## Resilience & Split Brain

### Quorum-Based Leadership

SolrCloud uses ZooKeeper as a quorum authority:
- When a node goes down, ZK detects it (heartbeat timeout, typically 30 seconds configurable)
- ZK doesn't form a quorum if more than half its nodes are gone
- When ZK loses quorum, Solr stops accepting writes (to avoid split brain)

**Example: 5-node ZK ensemble, 3 nodes down:**
- Remaining 2 nodes can't form quorum (need 3+)
- ZK stops accepting writes
- Solr can't elect new leaders
- Cluster is read-only until majority returns

### How Solr Prevents Split Brain

**Scenario:** Cluster partitions into two groups due to network failure.

**Without quorum:**
1. Partition A (majority): Continues operating, elects new leaders as needed
2. Partition B (minority): ZooKeeper nodes can't form quorum; Solr becomes read-only
3. When partition heals: Partition B rejoins Partition A's cluster state; no conflicts

**If ZK is misconfigured with no quorum requirement:**
1. Both partitions could elect leaders independently
2. Same document updated differently in both partitions
3. On healing, one partition's changes are silently lost → data loss

### Overseer & GC Pauses

A dangerous scenario: Overseer node experiences a long GC pause (>30 seconds):
- ZK detects no heartbeat, elects new Overseer
- Old Overseer awakens from GC, unaware it was deposed
- Two Overseers now exist, both trying to coordinate state transitions
- Potential for conflicting state changes

**Mitigation:**
- Tune JVM GC: use G1GC or ZGC, set max pause targets
- Monitor Overseer responsiveness; alert if elections happen frequently
- Separate ZK ensemble from Solr nodes if GC stability is critical

---

## Cross-Datacenter Replication (CDCR)

### What CDCR Does

CDCR replicates a Solr collection from one cluster (source) to another (target) across datacenters or regions:

- **Source cluster**: Serves queries, accepts writes
- **Target cluster**: Replica of source; can serve queries (read-only or with eventual consistency)
- **Replication**: Asynchronous pull from source to target

**Use cases:**
- Disaster recovery: Target cluster is hot backup; promote to primary if source fails
- Regional search: Source in US, target in EU for low-latency queries
- Analytics: Target cluster runs heavy aggregations without impacting source queries

### CDCR Architecture

```
Source Cluster          Target Cluster
  Leader ----tlog-->  Update Handler
  Replica  ------>   Replica
```

- Source publishes transaction logs to a shared location (or via HTTP)
- Target periodically polls source for new tlogs
- Target applies tlogs in order, maintaining version consistency
- If target falls behind, it can catch up by pulling older tlogs

### CDCR Limitations

1. **Asynchronous only**: No synchronous replication; target lags behind source by seconds to minutes
2. **Version conflicts**: If target accepts local writes, version numbers can diverge; on resync, one side's changes may be lost
3. **No automatic failover**: Target doesn't automatically become primary if source fails
4. **Operational complexity**: Requires monitoring replication lag, manual promotion if needed
5. **Tlog storage**: Source must keep tlogs for a long time; storage grows with data mutation rate
6. **Network bandwidth**: Replicating tlogs can consume significant bandwidth

### CDCR Configuration

In solrconfig.xml on source:
```xml
<requestHandler name="/cdcr" class="solr.CdcrRequestHandler">
  <lst name="replica">
    <str name="zkHost">target-zk:2181</str>
    <str name="collection">myindex</str>
  </lst>
</requestHandler>
```

On target:
```xml
<requestHandler name="/cdcr" class="solr.CdcrRequestHandler" >
  <lst name="source">
    <str name="zkHost">source-zk:2181</str>
    <str name="collection">myindex</str>
  </lst>
</requestHandler>
```

Start replication: `POST /cdcr?action=START`

### When to Avoid CDCR

- **High write rate + low latency requirement**: Eventual consistency lag will be noticeable
- **Cross-region failover within milliseconds**: Async replication can't guarantee RPO/RTO < 1 second
- **Active-active (bidirectional) replication**: CDCR doesn't handle conflicting writes well
- **Smaller deployments**: Operational overhead may not justify benefits

---

## Admin UI & Operations

### Solr Admin Console

The Admin UI (`/solr/admin/`) provides:

- **Dashboard**: Cluster overview, node status, JVM memory
- **Cloud > Cluster**: Visual representation of shards and replicas
- **Cloud > Nodes**: Node IP, port, and shard assignments
- **Core Selector > Plugins/Stats**: Per-core query/update metrics
- **Collection > Schema Browser**: Browse field types and fields
- **Query**: Execute queries with UI for params (q, fq, sort, facet, etc.)
- **Logging**: View/change log levels at runtime
- **Replication**: Monitor replication status if using legacy master-replica

### Metrics & Monitoring

Solr exposes metrics via JMX and HTTP:

**Key metrics search engineers track:**
- `solr_core_index_size_bytes`: Index size on disk
- `solr_core_num_docs`: Document count
- `solr_core_searcher_query_time_ms`: Query execution time
- `solr_core_cache_*_hitRatio`: Cache hit rates (queryResultCache, filterCache)
- `solr_core_indexer_updates_*`: Update throughput and latency
- `solr_jvm_memory_heap_used_percent`: JVM heap usage
- `solr_jvm_gc_concurrent_mark_sweep_time_ms`: GC pause times

**HTTP endpoint:** `GET /solr/admin/metrics?registry=all` returns Prometheus-format metrics.

### Luke Handler (Index Introspection)

The Luke handler provides detailed index statistics:
- Term frequencies and distributions
- Segment analysis
- Stored field access
- Useful for debugging schema issues or understanding index health

Access via: `GET /solr/<core>/admin/luke?show=schema`

---

## Operational Pain Points

### 1. ZooKeeper Dependency

**The issue:** Solr can't function without ZooKeeper. If ZK is down or partitioned:
- No new shard leaders can be elected
- Cluster can't scale or add replicas
- Configuration changes are blocked

**Mitigation:**
- Run ZK ensemble separately from Solr; size it for high availability
- Use 5-node ensemble in production; 3-node minimum
- Monitor ZK quorum health; alert if any node is unreachable
- Keep ZK version in sync with Solr's expectations

### 2. JVM Tuning & GC Pressure

**The issue:** Solr is Java; GC pauses directly impact search latency and coordination.

**Common GC problems:**
- Young generation GC too frequent (pause every 10-100ms) → search latency spikes
- Full GC pauses (>10 seconds) → Overseer re-election, replica sync disruptions
- Heap size too large (>32GB) → ZGC or G1GC mandatory; CMS deprecated

**Tuning guidance:**
- Heap: 8-16GB typical for medium clusters; monitor actual usage
- GC: Use G1GC for heaps 8-31GB, ZGC for >32GB
- Max pause: Set `-XX:MaxGCPauseMillis=50` for predictable latency
- Monitor GC logs; alert if full GC happens > 1x per minute

### 3. Overseer Bottleneck

**The issue:** Complex state transitions (large collection creations, many replicas) queue through the Overseer, causing delays.

**Symptoms:**
- Collection creation hangs (waits for Overseer)
- Leader election delayed when nodes fail
- `overseer_queue` metric grows unbounded

**Mitigation:**
- Monitor overseer_queue size; alert if > 100
- Avoid mass replica failures (e.g., rolling restart too aggressively)
- Create collections serially, not in parallel
- In extreme cases, dedicate a low-traffic node as Overseer-only (not recommended for most)

### 4. Segment Merge Spikes

**The issue:** When Lucene merges many segments, query latency can spike 5-10x as CPU and I/O focus on merge.

**Symptoms:**
- Query P99 latency suddenly spikes while updates continue
- CPU usage increases dramatically
- Slow query logs show 100ms+ latencies

**Mitigation:**
- Tune `mergeFactor` and `ramBufferSizeMB` based on update rate
- Use background merge scheduling (enable in solrconfig.xml)
- Consider separate query and indexing hardware in high-throughput clusters
- Monitor `mergesInProgress` metric; alert if > 2 concurrent merges

### 5. Cache Thrashing

**The issue:** queryResultCache and filterCache are effective but can churn if cluster is handling too many unique queries or filter combinations.

**Symptoms:**
- Cache hit ratios < 50% despite large cache
- Memory pressure increases even with constant query volume
- queries slow down as caches fill and evict

**Mitigation:**
- Analyze queries; look for unnecessary variations (e.g., tiny pagination differences)
- Use cache warming on slow-warming filters (geospatial, date ranges)
- Tune cache size vs memory available; typical: queryResultCache=512MB, filterCache=256MB
- Consider query normalization to improve cache hit rate

### 6. Leader Distribution & Hotspots

**The issue:** If leaders are unevenly distributed, one node becomes a write bottleneck.

**Symptoms:**
- One or two nodes show high CPU/disk I/O while others are idle
- Updates slow down; tlog growth on one node only
- Network traffic asymmetric

**Mitigation:**
- Use `replicaAssignment=random` during collection creation to spread leaders
- Monitor `solr_core_indexer_updates_*` per-core; leaders should be roughly balanced
- If unbalanced, create a new collection with even rebalancing, migrate data, delete old collection

### 7. Tlog Growth & Cleanup

**The issue:** Transaction logs grow unbounded if hard commits are infrequent or if replication lags.

**Symptoms:**
- Disk usage grows quickly despite index size stability
- `$SOLR_BASE/data/tlog/` directory contains GB of files

**Mitigation:**
- Ensure hard commits happen regularly (every 5-30 seconds)
- Monitor tlog file counts; alert if > 10 files exist
- In CDCR scenarios, target cluster must keep up; monitor replication lag
- Consider reducing soft-commit frequency if tlog I/O is bottleneck

---

## Summary for Migration

**Solr strengths (vs alternatives):**
- Mature, proven architecture; decades of battle-testing
- Query feature richness (faceting, grouping, spatial, streaming)
- Near-real-time search with soft commits
- Transparent sharding; no application-level routing needed

**Solr tradeoffs (vs alternatives like OpenSearch):**
- ZooKeeper adds operational complexity and introduces a new failure domain
- GC tuning required for stable, predictable latency
- CDCR is asynchronous and complex; not ideal for true active-active
- Legacy master-replica setup is fully deprecated; SolrCloud is the only path forward

For migration evaluation, prioritize:
1. Do you have operational capacity to manage ZooKeeper?
2. Are your query patterns suited to Solr's rich DSL?
3. Can you tolerate SolrCloud's distributed complexity?
4. Is NRT search (soft commits) critical to your SLA?
