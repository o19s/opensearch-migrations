# Solr to OpenSearch Migration: Technical Steering Document

**Project**: Migration Advisor Knowledge Base & Skill for Solr → OpenSearch
**Audience**: Platform engineers, architects, migration leads
**Date**: 2024-01-15

---

## Source Stack: Apache Solr Landscape

### Current Solr Deployment

**Solr Versions in Production**
- **Core clusters** (search, analytics): Solr 8.11.2 (latest 8.x, security patches only)
- **Logging/metrics clusters**: Solr 7.7.3 (legacy, unsupported; scheduled for EOL)
- **Topology**: SolrCloud (not standalone); quorum-based via ZooKeeper
- **Collections**: Typically 4-8 shards per collection; 2-3 replicas per shard
- **Index stores**: Default Lucene codec; no custom codecs

**Hardware Baseline**
- **Nodes**: m5.2xlarge EC2 (8 vCPU, 32 GB RAM)
- **Storage**: EBS gp2, 500 GB per node
- **Cluster**: 10-15 nodes per collection; multi-AZ (2 AZs in us-east-1)
- **ZooKeeper**: Embedded in SolrCloud (3-5 nodes for quorum)

### SolrJ Client Patterns

Solr deployments typically use a client library for querying and indexing. SolrJ is the Java/JVM reference implementation:

- **Topology-aware clients**: Libraries discover shard/replica topology via ZooKeeper
- **Connection pooling**: HTTP client pooling with configurable timeouts
- **Query patterns**: Query DSL for full-text search, faceting, aggregations
- **Indexing patterns**: Batch indexing with commit strategies, soft vs. hard commits

**General client usage** (language-agnostic concept):
1. Initialize client with ZooKeeper quorum or direct cluster endpoint
2. Set default collection for queries/indexing
3. Build query object from filters, fields, aggregations
4. Execute query or index operation
5. Batch writes with periodic commits for indexing throughput

For language-specific implementations, see `sources/opensearch-fundamentals/` guides.

### Solr-Specific Features Currently Used

| Feature | Collection | Migration Path |
|---|---|---|
| **Faceted Search** | search-products | Direct OpenSearch facets via aggregations |
| **MoreLikeThis** | product-details | OpenSearch More Like This query |
| **DistributedSearch** | analytics | OpenSearch cross-cluster search (CCS) |
| **DIH (DataImportHandler)** | logs | Migrate to Logstash / Data Prepper pipeline |
| **UpdateChain** | events | Custom application logic pre-indexing |
| **CustomAnalyzer** | all | Map to OpenSearch analyzers via Index API |

---

## Target Stack: AWS OpenSearch Service

### OpenSearch Version Selection

- **Target**: OpenSearch 2.11 LTS (latest stable, Q1 2024)
- **AWS release lag**: 1-2 releases behind upstream (acceptable)
- **Support window**: 18 months of patches post-release
- **Rationale**: Better performance, stabilized FGAC API, improved observability vs. 2.9

### Deployment Model

- **Service**: AWS OpenSearch Service (managed, VPC-native)
- **Instance type**: r6g.xlarge Graviton2 (cost-optimized; strong performance)
- **Data nodes**: 5-7 (start with 5 for 3-way replication)
- **Master nodes**: 3 (dedicated; required for 3+ data nodes)
- **Storage**: EBS gp3, 1 TB initial (scales elastically)
- **Multi-AZ**: Yes (3 AZs in us-east-1)
- **Networking**: VPC endpoint, IAM roles + internal user database for auth

### OpenSearch Client Libraries

OpenSearch provides official client libraries for popular languages. The opensearch-java library is the JVM reference implementation; other languages have equivalent clients:

- **Java/JVM**: opensearch-java (official, OpenSearch-maintained)
- **Other languages**: Python, JavaScript, Go, Rust clients available
- **Common patterns**: Connection pooling, SigV4 auth (AWS), bulk indexing APIs
- **Comparison to Solr client**: Similar concepts (topology discovery, batching) but OpenSearch uses HTTP/JSON instead of XML

Client integration patterns vary by platform — see `sources/opensearch-fundamentals/` for language-specific guides.

---

## Infrastructure: AWS Services and Topology

### Compute & Connectivity

- **Application layer**: ECS on Fargate, EKS, or EC2 (all supported)
- **OpenSearch connectivity**: Via VPC (private endpoint, no internet exposure)
- **Security**: IAM roles for service-to-service auth; internal OpenSearch user database for tools

### Storage & Backups

- **Data storage**: AWS OpenSearch Service (managed, multi-AZ)
- **Snapshots**: Automated daily snapshots to S3 (AWS-managed)
- **Backup retention**: 30 days (configurable)
- **Data transfer**: Cross-AZ replication cost ~$0.02/GB (typically < $100/month)

### Monitoring & Observability

- **CloudWatch Metrics**: CPU, memory, disk, JVM heap (auto-collected)
- **CloudWatch Logs**: Application logs, slow query logs, cluster logs
- **OpenSearch Dashboards**: Optional visualization (can use Grafana instead)
- **Key metrics to track**:
  - CPUUtilization, IndexingRate, SearchLatency (p50/p95/p99)
  - QueryRate (queries/sec), JVMHeapUsage (%)

**Alerting**: CloudWatch Alarms + SNS for:
- Cluster status YELLOW/RED (unhealthy)
- CPU > 80% (scaling needed)
- Disk > 85% (storage pressure)
- Indexing latency > 2000 ms (pipeline backlog)
- Search latency p99 > 2x baseline (performance degradation)

---

## Migration Tooling

### Data Migration Options

| Tool | Use Case | Pros | Cons |
|---|---|---|---|
| **Logstash** | Bulk migration from Solr | Flexible filtering, battle-tested | Operational overhead |
| **Data Prepper** | Pipeline-based ingestion | AWS-native, serverless option | Newer, less docs |
| **AWS Glue** | Large batch jobs | Scalable, AWS-native | Slower than Logstash for streaming |
| **Reindex API** | Index-to-index copy | No external tooling | Slower; requires both systems online |

**Recommended**: Logstash during migration; direct application indexing in steady-state.

### Migration Architecture

```
Solr Collections (10-15 TB)
    ↓
Export (HTTP API / client library)
    ↓
S3 Staging Bucket (JSONL)
    ↓
[Logstash tasks × 3] ← Parallel chunked reads
    ↓
OpenSearch Domain
```

**Logstash configuration** (migration-specific):
- Input: S3 files (chunked JSONL)
- Filter: Field mapping (solr_* → opensearch_*)
- Output: OpenSearch bulk API (1000 docs per batch)
- Parallelism: 3 tasks; each reads subset of S3 files
- **Estimated time**: 5-10 hours for 10-15 TB (1.5-3 TB/hour)

---

## Infrastructure Decisions (Made)

### Decision: AWS OpenSearch (Managed) vs. Self-Managed / Elasticsearch

**Selected**: AWS OpenSearch Service (managed)

**Rationale**:
- Eliminates operational burden (auto-patching, multi-AZ, backups)
- Cost-effective (~$5K/month vs. ~$8K for self-managed HA)
- AWS-native integrations (VPC, IAM, CloudWatch)
- Open-source; no licensing concerns

**Trade-offs**:
- Cannot run custom plugins (pre-approved only)
- 1-2 release lag behind upstream
- Less control over JVM tuning (acceptable for our use case)

### Decision: ISM (Index State Management) Policies

**Status**: Pending (Week 8, post-Phase 2)

**Options**:
1. **Enable ISM** (recommended): Automatic warm tier transition after 30 days
   - Pros: 60% storage savings for time-series data
   - Cons: Slightly slower warm-tier queries
   - Cost impact: -$800/month on 10 TB deployment

2. **Manual lifecycle**: Keep all data on hot tier
   - Pros: Simpler operations, predictable latency
   - Cons: Higher storage costs

**Recommendation**: Enable ISM for new indices; apply retroactively post-migration

### Decision: Replica Count (Durability vs. Cost)

**Status**: Confirmed for Phase 1

**Selected**: 3-way replication (1 primary + 2 replicas)

**Rationale**:
- Tolerates loss of 1 node without data loss
- Data durability is critical
- Storage multiplier acceptable (~3x cost)

**Alternative**: 2-way replication
- Pros: 2x storage, faster writes
- Cons: Can only lose 1 node; higher data loss risk

### Decision: Query Timeout Configuration

**Status**: Pending (Week 3, Phase 1)

**Recommended**:
- **30 seconds** for user-facing APIs (allows complex aggregations)
- **10 seconds** for internal analytics (prevents resource exhaustion)

---

## Testing Strategy

### Unit Testing Concepts

- **Framework**: JUnit / pytest / comparable language-native framework
- **Approach**: Mock OpenSearch client; test query building, result parsing
- **Coverage**: Logic tests, not integration

### Integration Testing Concepts

- **Framework**: Testcontainers / comparable container test framework
- **Approach**: Spin up real OpenSearch container; verify indexing and queries
- **Performance**: 30-60 seconds per test (acceptable for integration layer)
- **Scope**: Index creation, document indexing, search queries, aggregations

### Load Testing

- **Tool**: JMeter or equivalent load framework
- **Scenarios**:
  - 1000 docs/sec indexing (10-thread pool)
  - 1000 queries/sec (100-thread pool)
  - Mixed workload (50% read, 50% write)
- **Success criteria**: < 200 ms p95 latency, < 1% error rate

---

## Migration Implementation Phases

### Phase 1: Bulk Migration

1. Export Solr collections to S3 (chunked JSONL)
2. Configure Logstash pipeline (parallelized across 3 tasks)
3. Monitor indexing progress and errors
4. Validate document counts

**Estimated time**: 5-10 hours for 10-15 TB

### Phase 2: Dual-Write Implementation

1. Modify application indexing to write to both Solr (primary) and OpenSearch (async, non-blocking)
2. Daily consistency validation: Query both systems, compare results
3. Alert if mismatch > 0.01%

### Phase 3: Query Routing

1. Introduce feature flag to route queries to OpenSearch
2. Canary rollout: 1% → 10% → 50% → 100% over 3 days
3. Fallback logic in place (switch back to Solr if errors)
4. Monitor latency, error rates, data consistency

### Phase 4: Cleanup

1. Remove Solr dependency from code
2. Archive Solr cluster
3. Close Solr client connections

---

## Success Criteria

### Technical Metrics
- ✅ Search latency p95 < 500 ms (parity with Solr)
- ✅ Indexing throughput 1000 docs/sec sustained
- ✅ Index size < 120% of Solr size
- ✅ Zero data loss (100% document count match)
- ✅ Uptime 99.95% (4.4 hours/month downtime acceptable)

### Operational Metrics
- ✅ MTTR < 30 minutes (down from 2+ hours)
- ✅ Platform team effort < 5 hours/month (down from 15-20)
- ✅ Automated incident response covers 90% of failure modes

---

**Document owner**: Platform Engineering Lead
**Last updated**: 2024-01-15
**Review cycle**: Bi-weekly during phases; monthly post-launch
