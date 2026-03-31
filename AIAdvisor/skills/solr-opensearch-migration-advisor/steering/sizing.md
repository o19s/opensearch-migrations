# Sizing and Infrastructure Steering

When recommending OpenSearch cluster sizing for a Solr migration, apply these rules.
All recommendations must be grounded in the inspected Solr topology and data volumes.

## Shard Sizing Rules

Choose target shard size by workload type:

| Workload | Target Shard Size | Rationale |
|----------|-------------------|-----------|
| Search (e-commerce, site search) | 10-30 GB | Smaller shards give better query parallelism and faster failover |
| Logging / analytics | 30-50 GB | Fewer shards reduce cluster state overhead |
| Hard ceiling | 50 GB | Beyond this, query performance and recovery time degrade significantly |

When the Solr inspection shows mixed workloads, classify each collection individually
and size shards per-collection.

## Shard Count Formula

Calculate primary shard count per index:

```
primary_shards = ceil( (source_data_GB * (1 + growth_factor)) / target_shard_size_GB )
```

- `source_data_GB`: total data size of the Solr collection (from inspection)
- `growth_factor`: expected growth over 12-18 months (default 0.5 if unknown)
- `target_shard_size_GB`: from the table above (use 25 GB as default for search, 40 GB for logs)

Example: A 120 GB Solr product catalog with 50% expected growth:
```
primary_shards = ceil( (120 * 1.5) / 25 ) = ceil(7.2) = 8 shards
```

Validate: total shards across all indices should stay well under 1,000 per node.
If cluster state exceeds 100 MB (`GET /_cluster/stats`), reduce shard count.

## Replica Strategy

**Production (steady state)**:
- `number_of_replicas: 1` (2 total copies) is the standard recommendation
- Ensures HA: one copy survives a single node or AZ failure
- For critical search workloads needing high read throughput, consider `number_of_replicas: 2`

**During migration / bulk load**:
- Set `number_of_replicas: 0` to eliminate replication overhead
- This doubles indexing throughput (single write per document)
- Restore replicas after bulk load completes:
  ```json
  PUT <index>/_settings
  { "number_of_replicas": 1 }
  ```
- Monitor `relocating_shards` in cluster health during replica allocation

Always call out this two-phase approach in migration plans.

## JVM Heap Sizing

- Allocate **50% of available RAM** to JVM heap; the rest goes to OS filesystem cache
- **Maximum heap: 32 GB** -- beyond this, JVM loses compressed ordinary object pointers (CompressedOops), and effective memory usage worsens
- Minimum recommended: 16 GB per node (8 GB heap)
- Sweet spot for most production clusters: 64 GB RAM per node (32 GB heap)

When mapping from Solr:
- If Solr nodes had N GB heap, recommend the same or slightly more for OpenSearch
- OpenSearch relies more heavily on OS cache for segment reads, so total RAM matters more than heap alone

## Dedicated Master Nodes

**When to recommend them**:
- Any production cluster
- Clusters with more than 3 data nodes
- Clusters handling concurrent indexing and search

**Configuration**:
- Always deploy **3 dedicated master nodes** (ensures quorum, prevents split-brain)
- Use small general-purpose instances (e.g., m5.large or m6g.large)
- Masters need minimal heap (512 MB - 1 GB) and moderate CPU
- Distribute across 3 Availability Zones

**What masters do**: cluster state management, shard allocation, index creation.
They must be isolated from data/search load to keep the cluster stable under pressure.

## Multi-AZ Deployment

**Mandatory for production**:
- Distribute data nodes across 3 Availability Zones
- Single AZ failure causes no downtime when replicas exist in other AZs
- AWS OpenSearch Service applies shard allocation awareness automatically

**Configuration** (self-managed):
```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "zone"
  }
}
```

Cross-AZ replication latency is typically <5 ms within a region.

## Node Role Separation

For clusters beyond ~10 data nodes, separate roles:

| Role | Purpose | When to add |
|------|---------|-------------|
| Master | Cluster coordination | Always in production (3 nodes) |
| Data | Index storage + search | Sized by storage and throughput needs |
| Coordinating | Query routing, aggregation reduction | Clusters with >20 data nodes or heavy aggregations |
| Ingest | Pipeline processing | When using complex ingest pipelines (e.g., enrich, grok) |

## Bulk Indexing Tuning

These settings apply during the migration data load phase.

**Batch size**: 5-15 MB per bulk request (not a fixed document count).
Start with 1,000 docs or 5 MB, measure throughput, adjust upward.

**Concurrency**: 2-4 concurrent bulk requests per data node.
Example: 8-node cluster = 16-32 concurrent requests.

**Refresh interval**: Disable during bulk load for maximum throughput:
```json
PUT <index>/_settings
{ "index.refresh_interval": "-1" }
```
Restore to `"1s"` (or `"30s"` for logs) after load completes.

**Translog**: For throughput-critical migration loads:
```json
PUT _cluster/settings
{
  "persistent": {
    "index.translog.durability": "async",
    "index.translog.sync_interval": "5s"
  }
}
```
Restore to `"sync"` after migration for data safety.

**Index buffer**: Increase from default 10% to 20-30% of heap for indexing-heavy loads:
```json
PUT _cluster/settings
{ "persistent": { "indices.memory.index_buffer_size": "20%" } }
```

**Migration load checklist** (include in every migration plan):
1. Set `refresh_interval: -1`
2. Set `number_of_replicas: 0`
3. Use bulk API with 5-15 MB batches
4. Set translog to async
5. After load: restore refresh_interval, replicas, and translog durability
6. Run `_forcemerge?max_num_segments=1` on completed indices

## ISM Lifecycle Patterns

Recommend ISM policies when Solr data has time-series characteristics
(logs, events, metrics) or when retention management is needed.

**Standard hot/warm/cold/delete pattern**:

| Phase | Age | Actions | Storage |
|-------|-----|---------|---------|
| Hot | 0-7 days | Rollover at 50 GB or 1 day; priority 100 | Fast SSD (gp3/io1) |
| Warm | 7-30 days | Force merge to 1 segment; shrink shards; priority 50 | Standard SSD |
| Cold | 30-90 days | Searchable snapshot to S3 | S3 (~$0.023/GB/month) |
| Delete | 90+ days | Delete index | None |

**Rollover configuration** (hybrid approach, recommended):
```json
"rollover": {
  "min_age": "1d",
  "min_primary_shard_size": "50GB",
  "min_doc_count": 100000
}
```
Rolls over when ANY condition is met. Prevents both undersized and oversized indices.

**When NOT to recommend ISM**: Static search indices (product catalogs, knowledge bases)
that don't have time-based retention needs. These use fixed indices, not rollover.

## Storage Configuration

**EBS volumes (AWS)**:
- **gp3**: Default choice. Baseline 3,000 IOPS, 125 MB/s. Scale up to 16,000 IOPS as needed.
- **io1**: Only when gp3 cannot meet sustained IOPS requirements.

**Capacity planning**:
- Calculate total size including replicas: `data_GB * (1 + num_replicas)`
- Add 30-50% headroom for segment merging overhead
- Trigger alerts at 20% free space; OpenSearch applies read-only block at 5%

## Monitoring Metrics

Include these monitoring recommendations in every migration plan:

**Critical alerts**:
- `JVMMemoryPressure` > 85% -- risk of GC pauses, scale up or add nodes
- `ClusterStatus` = Red -- missing primary shards, investigate immediately
- `FreeStorageSpace` < 20% -- trigger rollover or archive; read-only block at 5%

**Performance tracking**:
- `IndexingRate` and `IndexingLatency` -- track during and after migration
- `SearchRate` and `SearchLatency` (p50, p99) -- compare against Solr baselines
- `CPUUtilization` sustained > 70% -- indicates undersized cluster
- `NodeCount` drops -- network or availability issue

**Slow logs** (enable post-migration for query tuning):
```json
PUT _settings
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s"
}
```

## Topology Mapping from Solr

- SolrCloud (ZooKeeper coordination) maps to OpenSearch cluster manager (no external ZK needed)
- Start with a 1:1 resource mapping from Solr nodes to OpenSearch data nodes as a baseline
- Adjust based on actual shard sizing calculations above
- If Solr used overshard (many small shards), consolidate in OpenSearch
- If Solr had very large shards (>50 GB), split in OpenSearch
