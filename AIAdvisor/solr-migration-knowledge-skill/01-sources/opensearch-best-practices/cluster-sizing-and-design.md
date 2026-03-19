# Cluster Architecture and Sizing for OpenSearch

**Source:** https://docs.opensearch.org/latest/tuning-your-cluster/

## Overview

Proper cluster design requires understanding node roles, shard distribution, and lifecycle patterns. Scaling decisions—vertical vs. horizontal—depend on bottleneck identification and workload characteristics.

## Node Roles and Responsibilities

### Master Nodes

**Purpose**: Cluster state management, shard allocation decisions, coordination

**Responsibilities**:
- Maintain authoritative cluster state (which shards exist, node membership)
- Coordinate shard allocation during node failures or scaling
- Manage index creation/deletion operations
- Process join/leave requests from nodes

**Configuration**:
```yaml
node.roles: ["master"]
node.data: false
node.ingest: false
node.ml: false
```

**Sizing**:
- **Production minimum**: 3 nodes (ensures quorum; tolerates 1 failure)
- **Large clusters (>50 nodes)**: 5-7 dedicated masters for resilience
- **Instance type**: m5.large or smaller (light compute, ~1GB heap)
- **Storage**: Minimal; cluster state is in-memory

**Master Election**:
- Voters use Raft protocol; need >50% quorum to elect leader
- 3 masters: tolerate 1 failure
- 4 masters: tolerate 1 failure (3-of-4 quorum)
- 5 masters: tolerate 2 failures (3-of-5 quorum)

### Data Nodes

**Purpose**: Index storage, shard hosting, search/aggregation execution

**Responsibilities**:
- Store index shards (primary and replicas)
- Execute search queries and aggregations
- Participate in rebalancing when cluster topology changes
- Maintain local translog and segment files

**Configuration**:
```yaml
node.roles: ["data"]
node.master: false
node.ingest: false
```

**Sizing Strategy**:
- Size based on total index volume / replication factor
- Example: 1 TB total storage needed, 1 replica = 2 TB raw data
- Distribute across nodes: 2 TB / 10 nodes = 200 GB per node
- Leave 20-30% headroom for merging operations

**Memory allocation**:
- Heap: 50% of RAM (remainder for OS cache)
- Maximum: 32 GB heap (preserves compressed object pointers)
- Example: 64 GB node = 32 GB heap, 32 GB OS cache
- Avoid single large node (prefer multiple medium nodes for scalability)

### Coordinating-Only Nodes (Optional)

**Purpose**: Query routing, aggregation consolidation for high-concurrency search

**When to use**:
- Clusters >20-30 data nodes
- Heavy aggregation workloads (hundreds of concurrent searches)
- Need to isolate search load from indexing

**Configuration**:
```yaml
node.roles: []
node.master: false
node.data: false
node.ingest: false
```

**Responsibilities**:
- Receive search requests, fan out to data nodes
- Consolidate results/aggregations from shards
- Do not store data; pure routing/aggregation
- Help when search requests are expensive (large aggregations, many fields)

**Trade-offs**:
- Additional network hop (slight latency increase)
- Reduces pressure on data node CPU (beneficial for mixed read/write)
- Not needed for read-only clusters (data nodes can route themselves)

### Ingest Nodes (Optional)

**Purpose**: Pre-processing documents before indexing (transformations, enrichment)

**When to use**:
- Bulk transformations (field extraction, type conversion, geolocation lookup)
- Heavy document parsing (JSON extraction, multiline consolidation)
- Avoid heavy logic; complex pipelines should pre-process outside cluster

**Configuration**:
```yaml
node.roles: ["ingest"]
node.data: false
node.master: false
```

**Responsibilities**:
- Execute ingest pipelines (processors for filtering, renaming, geocoding)
- Enrich documents before indexing
- Validate/standardize field formats

**Performance impact**:
- Ingest pipelines run synchronously with indexing
- Complex pipelines slow bulk requests 20-50%
- Better approach: pre-process in application code or Kafka/Lambda

## Memory Architecture

### JVM Heap Configuration

**Rule**: Allocate 50% of available RAM to JVM heap

```yaml
-Xms16g -Xmx16g  # For 32 GB node
```

**Why 50%**:
- Heap: Lucene segment memory, cluster state, field data caches
- OS cache: Lucene index files (most searches hit disk cache, not heap)
- OS cache is essential for search performance (avoids disk I/O)

**Heap sizing constraints**:
- **Minimum**: 8 GB (for any meaningful workload)
- **Maximum**: 32 GB (JVM uses compressed object pointers <32GB; >32GB loses compression)
- **Practical**: 16 GB (data nodes), 1 GB (master nodes)

### Example Node Configurations

| Role | RAM | Heap | Use Case |
|------|-----|------|----------|
| Master | 8 GB | 1 GB | Cluster coordination |
| Data (small) | 16 GB | 8 GB | Dev/test environments |
| Data (medium) | 32 GB | 16 GB | Production search clusters |
| Data (large) | 64 GB | 32 GB | High-volume logging |
| Coordinating | 32 GB | 16 GB | Heavy aggregations |

## Shard Distribution Guidelines

### Shard-to-Node Ratio

**Target**: 1-3 shards per node (healthy cluster state)

**Examples**:
- 5-node cluster: 5-15 shards ideal
- 20-node cluster: 20-60 shards ideal
- Too many shards: Cluster state grows, more CPU overhead
- Too few shards: Uneven data distribution, single shard bottleneck

**Cluster state size**:
- Monitor with `GET /_cluster/stats` → `status.indices.shards`
- Warning: >100 MB cluster state (indicates over-sharding)
- Action: Reduce shard count via shrinking or reindexing

### Shard Placement

**Primary and replica placement rules**:
- Replicas never on same node as primary (shard availability)
- Use allocation awareness: `cluster.routing.allocation.awareness.attributes: aws_availability_zone`
- Enforce cross-AZ replicas (single AZ failure doesn't lose data)

**Index allocation filtering** (move shards away from specific nodes):

```json
PUT my-index/_settings
{
  "index.routing.allocation.exclude._name": "old-node-*"
}
```

## Index Lifecycle Patterns

### Time-Based Indices (Logs, Metrics, Events)

**Pattern**: Create one index per day/hour, apply lifecycle policies

**Advantages**:
- Clean deletion (drop entire index vs. delete individual documents)
- Efficient archival (move old indices to S3/Glacier)
- Enables hot-warm-cold architecture
- Easier to understand data retention

**Example naming**: `logs-2026-03-17`, `metrics-2026-03`

**Lifecycle pattern**:
```
logs-2026-03-17 (hot) → logs-2026-03-17 (warm, 7 days) → cold (30 days) → delete (90 days)
```

### Rollover Strategy

**Rollover action**: Create new index when current exceeds size/age/doc-count threshold

```json
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50GB",
            "max_age": "1d"
          }
        }
      },
      "warm": {"min_age": "7d"},
      "delete": {"min_age": "90d", "actions": {"delete": {}}}
    }
  }
}

PUT _index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs-policy",
      "index.lifecycle.rollover_alias": "logs"
    }
  }
}
```

**Benefits**:
- Automatic index creation and cleanup
- Predictable performance (new index = fresh segments)
- Easy retention management

### Static Indices (Reference Data, Non-Time-Series)

**Pattern**: Single large index; no rollover

**Use cases**:
- Product catalog (products, SKUs)
- User master data
- Reference lookups

**Sizing**: 
- Can be large (multiple TB) if sharded properly
- Replica strategy: 1-2 replicas for HA
- No lifecycle management needed

## Hot-Warm-Cold Architecture

### Three-Tier Design

Optimize cost by moving data through phases based on access patterns:

| Tier | Hardware | Retention | Access Pattern |
|------|----------|-----------|-----------------|
| **Hot** | Fast SSD, NVMe, high IOPS | Current day | High query volume, active indexing |
| **Warm** | Standard SSD, moderate IOPS | 1-30 days | Moderate query volume, read-heavy |
| **Cold** | Searchable snapshots (S3) | 30-90+ days | Low query volume, occasional analytics |

### Implementation

**Hot Phase** (current day):
```json
"hot": {
  "actions": {
    "rollover": {"max_primary_shard_size": "50GB", "max_age": "1d"},
    "set_priority": {"priority": 100}
  }
}
```
- High shard priority (allocates to best nodes first)
- No replicas acceptable (incoming data, can recreate)
- Aggressive indexing optimization

**Warm Phase** (1-7 days):
```json
"warm": {
  "min_age": "1d",
  "actions": {
    "set_priority": {"priority": 50},
    "forcemerge": {"max_num_segments": 1}
  }
}
```
- Add replicas (for HA, shift away from hot tier)
- Force merge to 1 segment (improves search speed, reduces CPU)
- Can move to cheaper node types (standard SSD)

**Cold Phase** (7-90+ days):
```json
"cold": {
  "min_age": "7d",
  "actions": {
    "searchable_snapshot": {"snapshot_repository": "s3-repo"},
    "set_priority": {"priority": 0}
  }
}
```
- Use searchable snapshots (data lives in S3, indices query S3 on demand)
- Eliminates local storage cost (major savings)
- Query latency increases slightly (S3 latency vs. local disk)
- Best for ad-hoc analytics, compliance audits

**Delete Phase** (retention window):
```json
"delete": {
  "min_age": "90d",
  "actions": {"delete": {}}
}
```

### Cost Impact

**Example**: 1 TB logs per day, 30-day retention

| Tier | Days | Nodes (16 GB) | Cost |
|------|------|---------------|------|
| Hot | 1 | 5 | $150/month |
| Warm | 7 | 7 | $210/month |
| Cold | 22 | S3 only | $20/month |
| **Total** | 30 | | $380/month |

Without tiering: 30 × 5 nodes = 150 nodes = $4,500/month (12x cost increase)

## Cross-Cluster Search (Multi-Tenant Isolation)

### Architecture

**Use case**: Multiple teams/tenants share cluster while maintaining separate indices

```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.remote.cluster-a.seeds": ["10.0.1.1:9300"],
    "cluster.remote.cluster-b.seeds": ["10.0.2.1:9300"]
  }
}

GET cluster-a:logs-*,cluster-b:logs-* /_search
{
  "query": {"match_all": {}}
}
```

**Benefits**:
- Query multiple clusters in single request
- Isolate data by cluster (security, performance)
- Scale independently (each cluster sizes itself)
- Easier migration (point remote to new cluster)

**Trade-offs**:
- Network latency between clusters (add 10-50ms to queries)
- Coordination overhead (more complex aggregations)
- Suitable for federated analytics, not real-time transactions

## Snapshot and Restore Strategy

### Repository Configuration

**S3 repository** (AWS):

```json
PUT _snapshot/s3-repo
{
  "type": "s3",
  "settings": {
    "bucket": "opensearch-backups",
    "region": "us-east-1",
    "compress": true,
    "max_snapshot_bytes_per_sec": "500mb"
  }
}
```

**File-based repository** (local/NFS):

```json
PUT _snapshot/file-repo
{
  "type": "fs",
  "settings": {
    "location": "/mnt/backup/opensearch",
    "compress": true
  }
}
```

### Backup Policies

**Incremental snapshots**:
- First snapshot: Full copy (baseline)
- Subsequent snapshots: Only changed segments
- Dramatic space savings (typically 20-50% of original)

**Automated scheduling** (via ISM or cron):

```json
PUT _ilm/policy/snapshot-policy
{
  "policy": {
    "phases": {
      "warm": {
        "min_age": "1d",
        "actions": {
          "snapshot": {
            "repository": "s3-repo",
            "snapshot": "snapshot-{{index | urlencode}}-{{now/d}}"
          }
        }
      }
    }
  }
}
```

**Retention**:
- Daily snapshots: Keep 7-30 days
- Weekly snapshots: Keep 12 weeks
- Monthly snapshots: Keep 1+ years
- Restore tests: Monthly (verify snapshot integrity)

### Restore Procedures

**Single index restore**:

```json
POST _snapshot/s3-repo/snapshot-logs-2026-03-01/_restore
{
  "indices": "logs-2026-03-01",
  "rename_pattern": "(.+)",
  "rename_replacement": "$1-restored"
}
```

**Partial restore** (specific shards only):

```json
POST _snapshot/s3-repo/snapshot/_restore
{
  "indices": "large-index",
  "include_global_state": false,
  "partial": true
}
```

## Cluster State Management

### Cluster State Size Limits

**Warning signs**:
- State size >100 MB: Too many shards or fields
- Response time on cluster state updates >1 second: Overload
- Master node CPU spikes on state updates: Inefficient routing

**Reduction strategies**:
1. Reduce shard count (consolidate indices)
2. Reduce field count (use fields relevant to queries only)
3. Use field aliases (avoid mapping duplicates)

**Monitoring**:

```json
GET /_cluster/stats
```

Look for: `status.indices.shards.total` and `status.indices.shards.count`

## Vertical vs. Horizontal Scaling

### When to Scale Up (Larger Nodes)

- Network bandwidth bottleneck (1 Gbps not sufficient)
- Single large node more cost-efficient (avoid coordinating node overhead)
- Workload is search-heavy (data locality matters)

**Limitations**:
- Max heap 32 GB (fundamental JVM limit)
- Physical RAM limits (most servers: 256-512 GB)
- Single node failure impacts more data

### When to Scale Out (More Nodes)

- Indexing throughput needed (distribute bulk across more nodes)
- High availability critical (more nodes = more failure tolerance)
- Shard count exceeds shard-to-node ratio (need to lower ratio)
- Simplifies operations (replacing failed nodes easier)

**Default approach**: Scale out (more medium nodes) preferred over up (fewer large nodes)

## Capacity Planning Formula

```
Required nodes = (Total index size GB × replication factor) / (Heap size GB × disk utilization %)
```

Example: 
- 100 GB index, 1 replica = 200 GB total data
- 16 GB heap per node, 80% disk utilization = 19.2 GB usable per node
- Nodes needed = 200 / 19.2 = ~11 nodes
- Plan for growth: 11 × 1.2 = 13 nodes

## Multi-Tenancy Isolation

### Index-Based (Separate Indices)

```json
GET /customer-a-*,customer-b-*/_search
```

- Query multiple indices simultaneously
- Security: Use role-based access control
- Scaling: Each tenant's indices sized independently
- Drawback: Must know all customer prefixes in query

### Shard-Based (Separate Shards)

```json
PUT tenant-a-index
{
  "settings": {
    "number_of_shards": 5,
    "index.routing.allocation.include.tenant": "a"
  }
}
```

- Dedicate nodes/shards to specific tenants
- Better isolation (noisy neighbor prevented)
- More complex operations
- Higher cost (underutilized nodes possible)

### Application-Level (Document Filtering)

```json
GET /shared-index/_search
{
  "query": {
    "term": {"tenant_id": "customer-a"}
  }
}
```

- Single index shared across tenants
- Security: Filter queries by tenant_id
- Cost-efficient (no data duplication)
- Risk: Accidental data leakage if filter forgotten
