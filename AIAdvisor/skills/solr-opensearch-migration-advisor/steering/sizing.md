# Solr to OpenSearch Cluster Sizing

**Trigger:** When sizing a cluster, planning shards, choosing JVM heap, or estimating storage. Always label outputs as estimates with stated assumptions; when in doubt, size up.

## Rules

- **Shard size:** 10–50 GB per shard. Split or merge shards outside this range before migration.
- **Shard count:** `primary_shards = ceil(expected_index_size_GB / target_shard_size_GB)`. Recalculate from data size — do not copy the Solr shard count.
- **Replicas:** `number_of_replicas: 1` (2 total copies) for production. Set to 0 during bulk load, restore after.
- **JVM heap:** `-Xms == -Xmx`. Never exceed 50% of RAM or 32 GB. Recommended 16–31 GB for data nodes.
- **Cluster manager nodes:** 3 dedicated, odd-number quorum. No external ZooKeeper.
- **Coordinating nodes:** ≥ 2 coordinating-only nodes behind a load balancer for production.
- **Disk watermarks:** alert at 75%; OpenSearch stops allocating at 85%, blocks writes at 90%. Size to stay below 75%.

## What counts as a sizing error

- Shard size outside 10–50 GB without explicit justification.
- JVM heap above 32 GB or above 50% of RAM.
- Fewer than 3 cluster manager nodes in production.
- Storage or shard estimate without stated assumptions.
- Replica count omitted from total storage calculation.

**Reference:** `references/09-sizing-and-performance.md` — storage formula, hardware tiers, hot-warm tiering, bulk indexing settings, monitoring metrics.
