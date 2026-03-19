# AWS Operational Best Practices for OpenSearch Service

**Source:** https://docs.aws.amazon.com/opensearch-service/latest/developerguide/bp.html

## Overview

AWS OpenSearch Service requires careful operational planning across instance sizing, storage configuration, and deployment topology. These practices ensure production reliability, performance, and cost efficiency.

## Domain Sizing

### Instance Type Selection

- **Data nodes**: Choose instance families based on workload characteristics:
  - CPU-intensive search: compute-optimized instances (c5, c6i)
  - Memory-intensive analytics: memory-optimized instances (r5, r6i, r7i)
  - General workloads: general-purpose instances (m5, m6i, m7i)
  - Graviton-based: r6g, m6g for cost efficiency and environmental benefits

- **Storage considerations**:
  - EBS-backed instances recommended for production
  - Local NVMe instances for temporary, non-critical data only
  - Ensure sufficient disk space for indices plus ~20% operational headroom

### Storage Architecture

**EBS Configuration (Recommended)**:
- **gp3 volumes**: Default choice—provides consistent IOPS independent of volume size
  - Baseline: 3,000 IOPS, 125 MB/s throughput
  - Scale IOPS up to 16,000 (up to 1,000 MB/s) as needed for throughput-heavy workloads
  - Cost-effective for mixed read/write patterns
- **io1 volumes**: Use when maximum IOPS consistency is critical and gp3 insufficient
  - Provision 50 IOPS per GB (higher cost)
  - Better for sustained high-concurrency scenarios

**Capacity Planning**:
- Calculate total index size including replicas
- Account for segment merging overhead (30-50% temporary growth)
- Reserve headroom for operations (snapshots, rebalancing)
- Right-size instances to distribute data across nodes without overloading individual disks

## Shard Strategy

### Shard Size Guidelines

Optimal shard sizes vary by use case:
- **Search workloads**: 10-30 GB per shard (smaller shards for better parallelism)
- **Logging/analytical workloads**: 30-50 GB per shard (fewer shards reduce overhead)
- **Hard limit**: Avoid exceeding 50 GB per shard (degrades query performance and recovery speed)

Smaller shards provide:
- Better query parallelism across nodes
- Faster shard allocation during node failures
- More flexible index routing

Larger shards reduce:
- Cluster state complexity
- Shard metadata overhead
- Index maintenance overhead

### Shard Count Formula

```
Number of primary shards = (Expected index size in GB / Optimal shard size in GB) × 1.5
```

The 1.5 multiplier accounts for growth and temporary overhead during operations.

**Validation**:
- `max_shards_per_node` default (1,000) should rarely be approached
- Monitor cluster state size with `GET /_cluster/stats`
- If state state exceeds 100 MB, reduce shard count

## Dedicated Master Nodes

### When to Use

Dedicated master nodes are essential for production clusters:
- Separate master node load from data/search operations
- Provide cluster stability during high write or search volumes
- Enable cluster scaling without master node bottlenecks

### Configuration for Production

- **Minimum**: 3 dedicated master nodes (ensures majority quorum for split-brain prevention)
- **Instance type**: Smaller general-purpose instances (m5.large or smaller)
  - Masters have light memory requirements (heap can be 512MB-1GB)
  - CPU needs are moderate (cluster state updates are not compute-intensive)
  - Network connectivity matters more than raw power
- **Placement**: Distribute across 3 Availability Zones for high availability

### Master Node Settings

```yaml
node.master: true
node.data: false
node.ingest: false
```

## Cluster Topology for Production

### Multi-AZ Deployment

**Mandatory for production**:
- Distribute data nodes across 3 Availability Zones
- Improves fault tolerance: single AZ failure doesn't cause downtime
- Ensures replica shards are on different AZs from primaries
- AWS applies shard allocation awareness automatically

**Configuration considerations**:
- Set `cluster.routing.allocation.awareness.attributes: aws_availability_zone`
- Replica allocation rules automatically enforce AZ diversity
- Monitor cross-AZ replication latency (typically <5ms within region)

### Node Role Separation

For medium to large clusters, separate concerns:

| Role | Purpose | Sizing |
|------|---------|--------|
| **Master** | Cluster coordination, state management | 3+ nodes, t3/m5 small |
| **Data** | Index storage, shard placement | Sized by storage needs |
| **Coordinating** | Query routing, aggregations (optional) | For clusters >20 data nodes |
| **Ingest** | Pipeline processing (optional) | If ingestion heavily transforms data |

## Monitoring and Observability

### Critical CloudWatch Metrics

**JVM Memory Pressure**:
- `JVMMemoryPressure`: % of JVM heap in use
- **Alert threshold**: >85% (approaching GC pause risk)
- **Action**: Scale up node memory or add nodes

**Cluster Health**:
- `ClusterStatus`: Green (all shards assigned), Yellow (missing replicas), Red (missing primaries)
- Monitor status changes as leading indicator of rebalancing events
- Red status requires immediate investigation

**Storage**:
- `FreeStorageSpace`: Available disk space in bytes
- **Warning**: <20% free space (triggers read-only block at 5%)
- **Proactive**: Trigger rollover/archive at 30% free

**Throughput and Latency**:
- `IndexingRate`: Documents indexed per second
- `SearchRate`: Search requests per second
- `IndexingLatency`: Mean time for index operations
- `SearchLatency`: p50, p99 query latencies

**Node Health**:
- `NodeCount`: Active nodes in cluster
- Unusual decreases indicate network/availability issues
- `CPUUtilization`: Watch for sustained >70% (query complexity, cluster operations)

### Slow Logs Configuration

Enable slow logs to identify problematic queries:

```json
PUT _settings
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.threshold.index.info": "5s"
}
```

- Analyze slowlog patterns to identify:
  - Expensive aggregations
  - Large `must_not` clauses (negations filter early, reducing efficiency)
  - Missing field-level caching directives

## Index Template Strategies

### Dynamic Template Usage

Use component templates for consistency:

```json
PUT _component_template/search-index-component
{
  "template": {
    "settings": {
      "number_of_shards": 5,
      "number_of_replicas": 1,
      "index.codec": "best_compression"
    },
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "message": {
          "type": "text",
          "analyzer": "standard"
        }
      }
    }
  }
}

PUT _index_template/search-template
{
  "index_patterns": ["search-*"],
  "composed_of": ["search-index-component"],
  "priority": 100
}
```

### Template Best Practices

- Define explicit mappings (disable dynamic mapping for predictable schemas)
- Set `index.codec: best_compression` for storage-heavy workloads
- Use component templates to avoid duplication across index patterns
- Version templates with priority ordering for gradual rollouts
- Set appropriate `refresh_interval` based on use case (1s for real-time, 30s for analytical)

## Capacity Planning: Reserved Instances vs On-Demand

### Cost Optimization Strategy

**Reserved Instances**:
- **1-year or 3-year commitments**: 30-40% discount vs on-demand
- Best for predictable baseline capacity (data nodes with stable size)
- Break-even: ~8 months for 1-year, ~4 months for 3-year

**On-Demand**:
- Suitable for temporary scaling (burst traffic, dev/test environments)
- Master nodes: minimal cost, use on-demand for simplicity
- Burst-capable data nodes: mix reserved baseline + on-demand spikes

### Sizing for Growth

- Commit reserved instances to 70-80% of typical capacity
- Use on-demand for upper 20-30% (growth headroom, spike absorption)
- Quarterly review: shift commitments as baseline grows
- Avoid over-provisioning: cold data is cheaper in S3 than warm nodes

## Index Lifecycle and Archival

### Time-Based Indices with Rollover

For time-series data (logs, metrics, events):

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
      "warm": {
        "min_age": "7d",
        "actions": {
          "set_priority": {"priority": 50}
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "searchable_snapshot": {}
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

- Hot phase: current day's data, 0 replicas acceptable for ingest
- Warm phase: previous 6 days, 1 replica
- Cold phase: use searchable snapshots (S3-backed) to reduce compute cost
- Delete phase: compliance retention windows

## Cost Optimization Checklist

- Use gp3 volumes (15-20% cheaper than io1 at equivalent performance)
- Enable UltraWarm for infrequently accessed data (searchable snapshots)
- Set appropriate replica counts: 0 for non-critical, 1 for standard HA
- Use lifecycle policies to move old data off hot nodes
- Right-size instances to actual workload (avoid over-provisioning)
- Monitor utilization and consolidate if average CPU <30%

## Security Considerations

- Enable encryption at rest (default in AWS OpenSearch Service)
- Use VPC endpoints for network isolation
- Enable subnet diversity across AZs for DDoS resilience
- Implement fine-grained access control with IAM or OpenSearch internal users
- Enable audit logging for compliance workloads
- Use Cognito authentication for external user management
