# Self-Managed OpenSearch to AWS Managed Cluster Migration

This document covers migrating from a self-managed OpenSearch cluster to an Amazon OpenSearch Service managed domain (provisioned).

## 1. Architecture Differences

| Concept | Self-Managed | AWS Managed Domain |
| :--- | :--- | :--- |
| Cluster provisioning | Manual EC2/bare-metal setup | AWS Console, CLI, CloudFormation, or Terraform |
| Node roles | Fully configurable (`cluster_manager`, `data`, `ingest`, `coordinating`, `ml`) | Data nodes, dedicated master nodes, UltraWarm, cold storage — fixed role assignments |
| OS / JVM patching | Operator responsibility | AWS-managed; minor version upgrades can be initiated by the user |
| Plugin installation | `opensearch-plugin install` on each node | Pre-installed plugin set; custom plugins not supported |
| Configuration files | `opensearch.yml`, `jvm.options` on each node | Subset exposed via Advanced Options in the console/API |
| TLS / certificates | Operator-managed PKI | AWS-managed node-to-node encryption; optional custom endpoint with ACM certificate |
| Storage | Any block device or NFS | EBS (gp2, gp3, io1, io2) or instance store for certain instance types |
| Networking | Any network topology | VPC (recommended) or public endpoint |

## 2. Domain Creation Checklist

When creating a managed domain, map your self-managed cluster configuration to these settings:

### 2.1 Instance Types and Count

- **Data nodes**: Choose an instance family based on workload profile:
  - General purpose (`m6g`, `m7g`) — balanced search and indexing.
  - Compute optimized (`c6g`, `c7g`) — CPU-bound query workloads.
  - Memory optimized (`r6g`, `r7g`) — large aggregations, high field cardinality.
  - Storage optimized (`im4gn`, `is4gen`) — high-density log/time-series data.
- **Dedicated master nodes**: Recommended for production. Use 3 dedicated master nodes (`m6g.large.search` or larger). Self-managed clusters that ran combined master/data roles must separate them.
- **UltraWarm nodes**: For infrequently accessed warm-tier data. Replaces self-managed warm-tier nodes backed by cheaper storage.
- **Cold storage**: S3-backed tier for rarely queried data. No self-managed equivalent — data must be detached from the cluster and reattached on demand.

### 2.2 Storage

| Self-Managed | Managed Equivalent |
| :--- | :--- |
| Local NVMe / SSD | Instance store (only on `i3`, `im4gn`, `is4gen` families) |
| EBS gp2/gp3 attached to EC2 | EBS gp3 (default), gp2, io1, io2 |
| Network-attached storage (NFS/EFS) | Not supported — EBS only |

- **gp3** is the default and recommended storage type. It provides a baseline of 3,000 IOPS and 125 MB/s throughput, independently configurable.
- Maximum EBS volume size per data node depends on instance type (up to 24 TB on some families).

### 2.3 Networking

- **VPC access** (recommended): The domain endpoint is placed inside a VPC. Access is controlled by security groups. Clients must be in the VPC or connected via VPN/Direct Connect/PrivateLink.
- **Public access**: The domain endpoint is internet-facing. Access is controlled by IAM resource-based policies and/or fine-grained access control.
- Self-managed clusters behind a load balancer should migrate to VPC access with appropriate security group rules.

### 2.4 Availability Zones

- Production domains should use **3 AZs** for high availability.
- The service automatically distributes primary and replica shards across AZs.
- Self-managed clusters using rack-awareness (`cluster.routing.allocation.awareness.attributes`) get this behavior automatically.

## 3. Configuration Translation

Many `opensearch.yml` settings are not directly configurable on a managed domain. The table below maps common self-managed settings to their managed equivalents.

| Self-Managed Setting | Managed Equivalent | Notes |
| :--- | :--- | :--- |
| `cluster.name` | Domain name | Set at creation time; cannot be changed |
| `node.roles` | Instance type selection | Data, master, UltraWarm roles chosen at domain creation |
| `path.data` / `path.logs` | Managed by AWS | EBS volumes and CloudWatch Logs |
| `network.host` / `http.port` | VPC endpoint or public endpoint | Port is always 443 (HTTPS) |
| `discovery.seed_hosts` | Managed by AWS | No manual discovery configuration |
| `cluster.initial_cluster_manager_nodes` | Managed by AWS | Dedicated master node count set at creation |
| `plugins.security.*` | Fine-grained access control + IAM | See Section 5 |
| `thread_pool.*` | Not configurable | AWS manages thread pools |
| `indices.query.bool.max_clause_count` | Advanced Options | Configurable via API/console |
| `indices.fielddata.cache.size` | Advanced Options | Configurable via API/console |
| `indices.breaker.*` | Not configurable | AWS manages circuit breakers |

### 3.1 Index Settings That Carry Over

These index-level settings work the same way on managed domains:

- `number_of_shards`, `number_of_replicas`
- `refresh_interval`
- `analysis` (analyzers, tokenizers, filters)
- `mappings` (field types, dynamic templates)
- `index.codec` (best_compression, etc.)
- Index lifecycle via ISM policies

### 3.2 Settings Not Available on Managed Domains

- Custom JVM options (`jvm.options`) — AWS manages heap sizing (50% of instance RAM, capped at ~32 GB).
- File-system level settings (`index.store.type`).
- Custom plugin installation — only pre-bundled plugins are available.
- Node-level `opensearch.yml` overrides beyond Advanced Options.

## 4. Plugin Compatibility

AWS managed domains include a fixed set of plugins. If your self-managed cluster uses custom or community plugins, check availability:

| Plugin Category | Available on Managed | Notes |
| :--- | :--- | :--- |
| Security (OpenSearch Security) | Yes | Bundled; configured via fine-grained access control |
| Alerting | Yes | Bundled |
| Anomaly Detection | Yes | Bundled |
| Index State Management (ISM) | Yes | Bundled |
| k-NN (vector search) | Yes | Bundled |
| SQL / PPL | Yes | Bundled |
| ML Commons | Yes | Bundled |
| Cross-Cluster Replication | Yes | Bundled |
| Observability | Yes | Bundled |
| Ingest processors | Yes | Standard processors bundled |
| Custom plugins (`.zip` install) | No | Must find an alternative or use ingest pipelines |
| Repository plugins (S3, etc.) | Yes (S3 only) | S3 snapshot repository is built-in; no other repository types |

**Migration action for custom plugins**: If your self-managed cluster relies on a custom plugin (e.g., a custom token filter, ingest processor, or scoring plugin), you must either:
1. Replace it with a built-in equivalent.
2. Move the logic to an ingest pipeline or application layer.
3. Use a search pipeline (if the plugin modifies query/response behavior).

## 5. Security Migration

Self-managed OpenSearch Security plugin configuration must be translated to the managed domain's security model.

### 5.1 Authentication

| Self-Managed | Managed Equivalent |
| :--- | :--- |
| Internal user database (`internal_users.yml`) | Internal user database (via Dashboards or API) |
| LDAP / Active Directory | LDAP integration via fine-grained access control |
| SAML | SAML authentication for Dashboards |
| OpenID Connect | Not directly supported; use Cognito or SAML |
| Client certificate (mTLS) | Not supported for end-user auth; node-to-node TLS is AWS-managed |
| Basic Auth | Supported via internal user database |
| Kerberos | Not supported on managed domains |

### 5.2 Authorization

| Self-Managed | Managed Equivalent |
| :--- | :--- |
| `roles.yml` | Roles defined via Dashboards Security UI or REST API |
| `roles_mapping.yml` | Role mappings via Dashboards Security UI or REST API |
| `action_groups.yml` | Action groups via REST API |
| Backend roles | IAM roles mapped to OpenSearch roles |
| Document-level security | Supported via fine-grained access control |
| Field-level security | Supported via fine-grained access control |
| Tenant isolation | Supported via Dashboards multi-tenancy |

### 5.3 IAM Integration (Managed-Only)

Managed domains add IAM-based access control not available in self-managed clusters:

- **Resource-based policies**: Attach an IAM policy to the domain to control which AWS principals can access it.
- **IAM request signing**: Clients sign requests with SigV4. The managed domain validates the IAM identity.
- **Fine-grained access control + IAM**: Map IAM roles to OpenSearch Security roles for unified authorization.

### 5.4 Migration Steps

1. Export your `roles.yml`, `roles_mapping.yml`, and `internal_users.yml`.
2. Enable fine-grained access control on the managed domain.
3. Recreate roles and role mappings via the Security REST API or Dashboards.
4. Recreate internal users or switch to IAM-based authentication.
5. Update client code to use SigV4 signing if switching to IAM auth.

## 6. Data Migration Strategies

### 6.1 Snapshot and Restore

The most common approach for migrating data from self-managed to managed:

1. Register an S3 snapshot repository on the self-managed cluster.
2. Take a snapshot of all indices.
3. Register the same S3 bucket as a snapshot repository on the managed domain (requires an IAM role with S3 access).
4. Restore the snapshot on the managed domain.

**Limitations**:
- The managed domain OpenSearch version must be >= the source version.
- Snapshots from OpenSearch 1.x can be restored on 2.x domains, but not vice versa.
- Security index (`.opendistro_security`) should not be restored — recreate security configuration on the managed domain.

### 6.2 Reindex from Remote

Use the `_reindex` API with a `remote` source to pull data directly:

```json
POST _reindex
{
  "source": {
    "remote": {
      "host": "https://self-managed-cluster:9200",
      "username": "admin",
      "password": "admin"
    },
    "index": "my-index"
  },
  "dest": {
    "index": "my-index"
  }
}
```

**Requirements**: The managed domain must be able to reach the self-managed cluster (VPC peering, VPN, or public endpoint). The remote cluster must be allowlisted in the managed domain's connection settings.

### 6.3 OpenSearch Ingestion (OSI)

AWS-native pipeline service for migrating data:

- Supports self-managed OpenSearch as a source and managed domain as a destination.
- Handles both public and VPC-based source clusters.
- Supports transformations during migration.
- Can run continuously for live migration with minimal downtime.

### 6.4 Logstash / Data Prepper

Use Logstash or Data Prepper as an intermediary:

1. Read from the self-managed cluster using the OpenSearch input plugin.
2. Write to the managed domain using the OpenSearch output plugin with SigV4 signing.

## 7. Operational Differences

| Operation | Self-Managed | Managed Domain |
| :--- | :--- | :--- |
| Version upgrades | Rolling restart with new binaries | In-place blue/green upgrade via console/API |
| Scaling (add nodes) | Provision new EC2, join cluster | Change instance count via console/API (blue/green) |
| Scaling (storage) | Attach larger EBS, migrate | Modify EBS volume size via console/API (online) |
| Monitoring | Prometheus, Grafana, `_cat` APIs | CloudWatch metrics, CloudWatch Logs, `_cat` APIs |
| Alerting on cluster health | Custom setup | CloudWatch Alarms + OpenSearch Alerting plugin |
| Automated snapshots | Cron + snapshot API | Hourly automated snapshots (retained 14 days) |
| Manual snapshots | Snapshot API + any repository | Snapshot API + S3 repository only |
| Log access | File system logs | CloudWatch Logs (slow logs, error logs, audit logs) |
| OS-level access | Full SSH access | No SSH access; no OS-level access |

## 8. Cost Considerations

- **Instance hours**: Billed per hour per node (data, master, UltraWarm, cold).
- **EBS storage**: Billed per GB-month for provisioned storage.
- **Data transfer**: Standard AWS data transfer charges apply.
- **No license cost**: OpenSearch is open source; the managed service fee is the instance/storage cost.
- **Reserved Instances**: Available for 1-year or 3-year terms with significant discounts.
- **Savings Plans**: Compute Savings Plans can apply to OpenSearch Service.

Use the `opensearch-pricing-calculator` to estimate costs based on your workload profile (see `scripts/pricing_calculator.py`).
