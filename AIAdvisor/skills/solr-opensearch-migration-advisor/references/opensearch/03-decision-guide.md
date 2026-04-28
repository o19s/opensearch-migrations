# Managed Cluster vs. Serverless Decision Guide

This document helps determine whether a self-managed OpenSearch workload should migrate to an AWS managed domain (provisioned) or an OpenSearch Serverless collection.

## 1. Decision Matrix

| Criterion | Managed Domain | Serverless | Notes |
| :--- | :--- | :--- | :--- |
| **Full plugin support** | ✅ All bundled plugins | ❌ Limited subset | ISM, Alerting, Anomaly Detection, CCR only on managed |
| **Custom plugins** | ❌ Not supported | ❌ Not supported | Neither option supports custom `.zip` plugins |
| **Cluster-level control** | ✅ Instance types, node count, JVM | ❌ No cluster concept | Managed gives more tuning knobs |
| **Operational overhead** | ⚠️ Moderate (upgrades, scaling) | ✅ Minimal | Serverless eliminates capacity planning |
| **Auto-scaling** | ⚠️ Manual or Auto-Tune | ✅ Automatic OCU scaling | Managed requires scaling actions |
| **Snapshot / restore** | ✅ S3 snapshots | ❌ Not supported | Critical for backup/DR strategies |
| **ISM (lifecycle policies)** | ✅ Full support | ❌ Not available | Managed required for complex retention policies |
| **UltraWarm / cold storage** | ✅ Tiered storage | ⚠️ Hot/warm only (time-series) | Managed has more storage tiers |
| **Cross-cluster replication** | ✅ Supported | ❌ Not available | Multi-region DR requires managed |
| **Cross-cluster search** | ✅ Supported | ❌ Not available | Federated search requires managed |
| **Authentication options** | ✅ IAM, SAML, LDAP, internal DB | ⚠️ IAM only (SAML for Dashboards) | Serverless is IAM-only for API access |
| **Document updates/deletes** | ✅ All operations | ⚠️ Search/vector only | Time-series collections are append-only |
| **Minimum cost** | ~$50/mo (small instance) | ~$350/mo (minimum OCU floor with redundancy) | Serverless has a higher cost floor |
| **Cost at scale** | ✅ Reserved Instances available | ⚠️ No reservations | Managed is cheaper for steady large workloads |
| **Version control** | ✅ Choose version, control upgrades | ❌ AWS-managed version | Managed allows pinning to a specific version |
| **Ingest pipelines** | ✅ Full support | ✅ Supported | Both support ingest pipelines |
| **Search pipelines** | ✅ Full support | ✅ Supported | Both support search pipelines |
| **ML Commons** | ✅ Full support | ✅ Supported | Both support model registration and inference |
| **SQL / PPL** | ✅ Full support | ✅ Supported | Both support SQL and PPL queries |
| **Vector search (k-NN)** | ✅ Full support | ✅ Supported | Both support approximate k-NN |

## 2. Workload-Based Recommendations

### 2.1 Full-Text Search (E-commerce, Document Search)

- **Small / variable traffic** → Serverless (search collection type)
- **Large / steady traffic** → Managed domain with Reserved Instances
- **Requires ISM or complex lifecycle** → Managed domain

### 2.2 Log Analytics / Observability

- **< 100 GB/day ingestion, simple retention** → Serverless (time-series collection type)
- **> 100 GB/day or complex retention tiers** → Managed domain with UltraWarm + cold storage
- **Requires alerting or anomaly detection** → Managed domain

### 2.3 Vector / Semantic Search

- **Prototyping or small-scale** → Serverless (vector collection type)
- **Large-scale production (millions of vectors)** → Managed domain for instance type control and cost optimization
- **Requires hybrid search (text + vector)** → Either; managed gives more tuning control

### 2.4 Multi-Tenant SaaS

- **Tenant-per-index with shared cluster** → Managed domain (fine-grained access control with index-level permissions)
- **Tenant-per-collection** → Serverless (but watch OCU costs — each collection has a minimum OCU floor)

## 3. Migration Path Decision Tree

```
Is the workload append-only (logs, metrics, events)?
├── Yes → Is daily ingestion < 100 GB AND retention < 90 days?
│   ├── Yes → Consider Serverless (time-series)
│   └── No  → Managed domain with UltraWarm
└── No  → Does the workload require any of these?
    │   - ISM policies
    │   - Alerting / Anomaly Detection
    │   - Snapshot / restore
    │   - Cross-cluster replication
    │   - LDAP / Kerberos auth
    │   - Custom scoring plugins
    ├── Yes → Managed domain
    └── No  → Is traffic unpredictable or spiky?
        ├── Yes → Consider Serverless (search or vector)
        └── No  → Compare costs using pricing calculator
            ├── Managed cheaper → Managed domain
            └── Serverless cheaper → Serverless
```

## 4. Hybrid Approach

It is valid to use both managed domains and Serverless collections within the same AWS account:

- **Managed domain** for the primary search workload (full feature set, cost-optimized with RIs).
- **Serverless collection** for log ingestion (time-series, auto-scaling, minimal ops).
- **Serverless collection** for a vector search prototype while the team evaluates embedding models.

Each deployment is independent — they do not share data or configuration. Cross-collection queries are not supported; application-level aggregation is required.

## 5. Migration Effort Comparison

| Aspect | To Managed Domain | To Serverless |
| :--- | :--- | :--- |
| Index mappings | Copy as-is | Remove shard/replica settings; inline synonym files |
| Index settings | Most carry over | Remove cluster-level settings, ISM, codec |
| Security | Translate roles → FGAC | Rewrite entirely as IAM + data access policies |
| Client code | Minimal changes (add SigV4 if using IAM) | Significant changes (SigV4 required, remove unsupported API calls) |
| Data migration | Snapshot/restore (fastest) | OSI pipeline or bulk API (no snapshot support) |
| Monitoring | CloudWatch + existing `_cat` APIs | CloudWatch only (limited `_cat` support) |
| Operational runbooks | Update for managed (no SSH, blue/green upgrades) | Largely eliminate (no cluster ops) |
