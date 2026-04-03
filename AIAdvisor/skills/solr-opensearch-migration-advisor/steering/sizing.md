# Solr to OpenSearch Sizing Steering

## Heuristics
- Shard Count: Generally, aim for 1-2 OpenSearch shards per Solr shard, depending on volume. Keep shard sizes between 10GB and 50GB.
- Replica Factor: Standard `number_of_replicas: 1` (total 2 copies) for production.
- JVM Heap: OpenSearch heap should be around 50% of available RAM, up to 32GB (pointer compression).
- CPU/RAM: Start with a 1:1 resource mapping (CPU/RAM) from Solr nodes to OpenSearch nodes as a baseline.

## Topologies
- SolrCloud (ZooKeeper) → OpenSearch (Cluster Manager).
- No external ZooKeeper needed for OpenSearch.

## Reference Architectures

### Small — Development / Low-Traffic
- **Profile:** ≤5M docs, ≤1GB index, ≤50 QPS, single collection
- **Solr source:** 1–2 Solr nodes, 1 shard, 1 replica
- **OpenSearch target:**
  - 2 data nodes (e.g., `r6g.large.search` or equivalent 2 vCPU / 16GB)
  - 1 primary shard, 1 replica
  - No dedicated cluster manager nodes needed
  - EBS `gp3` storage, 50GB per node
- **JVM heap:** 8GB (50% of 16GB)
- **Estimated AWS cost:** ~$150–250/month (on-demand)
- **When to use:** Dev/staging environments, small internal search apps, proof-of-concept migrations

### Medium — Production Workload
- **Profile:** 10–100M docs, 10–50GB index, 100–500 QPS, 1–5 indices
- **Solr source:** 3–5 SolrCloud nodes, 2–4 shards per collection, replication factor 2
- **OpenSearch target:**
  - 3 data nodes (e.g., `r6g.xlarge.search` or equivalent 4 vCPU / 32GB)
  - 3 dedicated cluster manager nodes (e.g., `m6g.large.search`)
  - 2–4 primary shards per index (target 10–30GB per shard), 1 replica
  - EBS `gp3` storage, 200–500GB per data node
  - Optional: 1–2 coordinating-only nodes for query isolation
- **JVM heap:** 16GB (50% of 32GB)
- **Estimated AWS cost:** ~$800–1,500/month (on-demand)
- **When to use:** Production ecommerce search, content sites, mid-size enterprise search

### Large — High-Scale / Mission-Critical
- **Profile:** 500M+ docs, 100GB+ index, 1,000+ QPS, 5+ indices, multi-tenant or multi-region
- **Solr source:** 6+ SolrCloud nodes, 4+ shards per collection, replication factor 2–3
- **OpenSearch target:**
  - 6+ data nodes (e.g., `r6g.2xlarge.search` or equivalent 8 vCPU / 64GB)
  - 3 dedicated cluster manager nodes (e.g., `m6g.large.search`)
  - 2+ coordinating-only nodes for query routing
  - 4–8 primary shards per index (target 20–50GB per shard), 1–2 replicas
  - EBS `gp3` or `io2` storage, 500GB–2TB per data node
  - Index lifecycle management (ISM) for time-series or rolling indices
  - Cross-cluster replication for DR / multi-region
- **JVM heap:** 31GB (stay under compressed oops threshold)
- **Estimated AWS cost:** ~$3,000–8,000+/month (on-demand; reserved instances reduce 30–40%)
- **When to use:** Large ecommerce platforms, enterprise-wide search, high-throughput logging/analytics

## Sizing Decision Checklist

When gathering sizing requirements, ask about:

1. **Document count and index size** — total docs, average doc size, growth rate
2. **Query throughput** — peak QPS, average QPS, acceptable p99 latency
3. **Indexing throughput** — bulk indexing rate, real-time indexing needs, refresh interval tolerance
4. **Data retention** — how long data lives in the index, time-series vs. static
5. **Availability requirements** — SLA targets, multi-AZ, cross-region DR
6. **Budget constraints** — monthly infrastructure budget, on-demand vs. reserved
7. **Growth trajectory** — expected doc count / QPS in 6 and 12 months
