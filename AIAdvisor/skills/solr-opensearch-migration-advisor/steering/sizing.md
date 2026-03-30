# Solr to OpenSearch Sizing Steering

## General Heuristics

- Shard Count: Aim for 1-2 OpenSearch shards per Solr shard. Keep shard sizes between 10GB and 50GB.
- Replica Factor: Standard `number_of_replicas: 1` (total 2 copies) for production.
- JVM Heap: OpenSearch heap should be around 50% of available RAM, up to 32GB (pointer compression).
- CPU/RAM: Start with a 1:1 resource mapping from Solr nodes to OpenSearch nodes as a baseline.

## Topologies

- SolrCloud (ZooKeeper) → OpenSearch (Cluster Manager).
- No external ZooKeeper needed for OpenSearch.

## Sizing From Live Solr Metrics

When a live Solr instance is available (via `inspect_solr` or individual inspection tools), use the actual metrics to produce concrete sizing recommendations instead of generic heuristics.

### Document Count (from Luke API `numDocs`)

| Solr numDocs | OpenSearch Primary Shards | Rationale |
|---|---|---|
| < 10M | 1 | Single shard is sufficient; avoid overhead of multi-shard coordination |
| 10M–100M | 2–5 | Target 10–50GB per shard; calculate from index size |
| > 100M | index_size_gb / 30 | 30GB per shard is the sweet spot for search latency |

### Query Throughput (from MBeans `requestTimes.meanRate`)

| Solr QPS | OpenSearch Replicas | Additional Guidance |
|---|---|---|
| < 50 | 1 replica | Standard HA setup is sufficient |
| 50–500 | 2 replicas | Consider coordinating-only nodes for query routing |
| > 500 | 3+ replicas | Dedicated coordinating nodes; consider read/write isolation |

### Cache Hit Ratio (from Metrics API)

Calculate `filterCache.hits / (filterCache.hits + filterCache.inserts)`:
- **> 0.9:** Filter caching is effective. Size OpenSearch request cache similarly.
- **0.7–0.9:** Moderate caching benefit. Review query patterns for optimization opportunities.
- **< 0.7:** Poor cache hit ratio. Investigate whether queries are too diverse for caching. May need request cache tuning or query pattern changes after migration.

### JVM Heap (from System Info API)

- Use **Solr max heap × 1.2** as the OpenSearch starting point.
- Never exceed **32GB** (compressed ordinary object pointers limit).
- Reserve **50% of machine RAM** for OS page cache — OpenSearch relies heavily on filesystem cache for segment reads.
- If Solr heap is already at 32GB, do not increase further; instead add data nodes.

### Latency Baseline (from MBeans `requestTimes`)

- `requestTimes.mean` → target **p50** for OpenSearch.
- `requestTimes.max` → set alerting threshold at **2× this value**.
- If mean > 200ms or max > 2000ms, flag as a risk: query optimization may be needed before or during migration.
- Compare latency across handlers: if `/edismax` is significantly slower than `/select`, the translated Query DSL may need tuning.

### Worked Example

Given a Solr instance reporting:
- 25M documents, 45GB index size
- 120 QPS average
- filterCache hit ratio 0.85
- 16GB heap, 8 CPUs

Recommendation:
- **Shards:** 2 primary shards (45GB / 2 ≈ 22GB per shard)
- **Replicas:** 2 replicas (120 QPS warrants extra capacity)
- **Heap:** 19GB (16 × 1.2, rounded)
- **Nodes:** 2 data nodes (matching Solr), 1 coordinating node
- **Cache:** Request cache enabled, sized to match Solr's filterCache
