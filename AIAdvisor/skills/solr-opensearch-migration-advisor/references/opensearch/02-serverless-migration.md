# Self-Managed OpenSearch to AWS OpenSearch Serverless Migration

This document covers migrating from a self-managed OpenSearch cluster to Amazon OpenSearch Serverless collections.

## 1. Fundamental Architecture Shift

OpenSearch Serverless eliminates the concept of clusters, nodes, and shards. Understanding this shift is critical before migrating.

| Concept | Self-Managed Cluster | OpenSearch Serverless |
| :--- | :--- | :--- |
| Deployment unit | Cluster of nodes | Collection (logical grouping of indices) |
| Scaling | Manual node/shard management | Automatic (OCU-based) |
| Capacity planning | Shard count, node sizing, heap tuning | Set max OCU limits; AWS handles the rest |
| Storage | EBS / local disk per node | S3-backed managed storage |
| Availability | Manual replica placement across racks/AZs | Built-in multi-AZ redundancy |
| OpenSearch version | Operator chooses and upgrades | AWS manages (currently 2.17.x); auto-upgraded |
| Configuration | `opensearch.yml`, index settings, JVM options | Minimal — collection type and policies only |
| Cost model | EC2 + EBS + operational overhead | OCU-hours (compute) + S3 storage (GB-month) |

### 1.1 Collection Types

Every serverless collection must be one of three types, chosen at creation and immutable:

| Type | Use Case | Key Behavior |
| :--- | :--- | :--- |
| **Search** | Full-text search, e-commerce, document search | Supports all CRUD operations; optimized for low-latency queries |
| **Time series** | Logs, metrics, traces, event data | Append-only (no updates/deletes on individual documents); optimized for time-based ingestion |
| **Vector search** | k-NN, semantic search, RAG, embeddings | Supports vector indexing and approximate nearest neighbor queries |

**Migration decision**: Map each self-managed index to the appropriate collection type. If a single cluster serves mixed workloads (e.g., search + logs), split into separate collections.

## 2. Feature Compatibility

### 2.1 Supported Operations

Serverless supports the core OpenSearch data-plane APIs:

- Index, bulk, get, delete, update (search and vector types only for update)
- `_search`, `_msearch`, `_count`, `_mget`
- `_mapping`, `_settings` (create and update)
- Index aliases, index templates, component templates
- Ingest pipelines, search pipelines
- SQL and PPL queries
- Point in Time (PIT) for pagination
- ML Commons (model registration, deployment, prediction)

### 2.2 Unsupported Operations and Features

These self-managed features have **no equivalent** in Serverless:

| Feature | Status | Migration Action |
| :--- | :--- | :--- |
| Cluster APIs (`_cluster/*`) | Not available | Remove from client code; not needed (AWS manages cluster) |
| Node APIs (`_nodes/*`) | Not available | Remove; use CloudWatch for monitoring |
| Snapshot / restore | Not available | Use OpenSearch Ingestion or reindex for data migration |
| Index State Management (ISM) | Not available | Time-series collections handle retention automatically via hot/warm tiers |
| Alerting plugin | Not available | Use CloudWatch Alarms or EventBridge |
| Anomaly Detection plugin | Not available | Move to application layer or use CloudWatch Anomaly Detection |
| Cross-Cluster Replication | Not available | Not needed; Serverless handles replication internally |
| Cross-Cluster Search | Not available | Query each collection separately; merge in application |
| Custom plugins | Not available | Replace with built-in functionality or application logic |
| Script-based updates (`_update` with script) | Limited | Reindex with transformed data instead |
| Scroll API | Not available | Use Point in Time (PIT) + `search_after` |
| `_cat` APIs | Partial | `_cat/indices` available (without health/status); others not available |
| Shrink / split / clone index | Not available | Create a new index and reindex |
| `_reindex` API | Not available | Use OpenSearch Ingestion or external tooling |
| Force merge | Not available | Managed automatically |
| Index open / close | Not available | Delete and recreate if needed |
| Custom scoring (function_score scripts) | Supported | Painless scripting works in queries |
| Aggregations | Supported | All standard aggregations available |

### 2.3 Time-Series Collection Restrictions

Time-series collections are append-only:

- `PUT <index>/_doc/<id>` — **not supported** (no explicit document IDs)
- `POST <index>/_update/<id>` — **not supported**
- `DELETE <index>/_doc/<id>` — **not supported**
- Only `POST <index>/_doc` (auto-generated ID) and `POST _bulk` (index action only) are allowed.

If your self-managed indices require document updates or deletes, use a **search** collection type instead.

## 3. Security Model

Serverless uses a completely different security model from the self-managed OpenSearch Security plugin.

### 3.1 Three Policy Types

| Policy | Purpose | Self-Managed Equivalent |
| :--- | :--- | :--- |
| **Encryption policy** | Defines KMS key for data at rest | `opensearch.yml` encryption settings |
| **Network policy** | Controls VPC vs. public access per collection | `network.host`, firewall rules |
| **Data access policy** | Controls who can read/write which indices | `roles.yml` + `roles_mapping.yml` |

### 3.2 Authentication

- **IAM only**: All requests must be signed with SigV4. There is no internal user database, no basic auth, no SAML, no LDAP.
- **SAML for Dashboards**: SAML authentication is supported for OpenSearch Dashboards access only (not API access).

### 3.3 Data Access Policies

Data access policies replace the entire OpenSearch Security role/permission model:

```json
[
  {
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/my-collection/logs-*"],
        "Permission": [
          "aoss:ReadDocument",
          "aoss:WriteDocument",
          "aoss:CreateIndex",
          "aoss:DescribeIndex"
        ]
      }
    ],
    "Principal": [
      "arn:aws:iam::123456789012:role/my-app-role"
    ]
  }
]
```

### 3.4 Migration Steps

1. Identify all roles and users from `roles.yml` and `internal_users.yml`.
2. Map each role to an IAM role or IAM user.
3. Create data access policies granting the equivalent permissions.
4. Create encryption and network policies for each collection.
5. Update all client code to use SigV4 request signing.

## 4. Index and Mapping Migration

### 4.1 What Carries Over

- Field mappings (`properties`, types, analyzers)
- Custom analyzers defined in index settings (`settings.analysis`)
- Dynamic templates
- Index aliases
- Index templates and component templates

### 4.2 What Does Not Carry Over

| Setting | Reason | Action |
| :--- | :--- | :--- |
| `number_of_shards` | Managed by Serverless | Remove from index creation; Serverless handles sharding |
| `number_of_replicas` | Managed by Serverless | Remove; redundancy is controlled by the network policy |
| `refresh_interval` | Managed by Serverless | Remove; Serverless manages refresh |
| `index.codec` | Not configurable | Remove |
| `index.store.type` | Not applicable | Remove |
| ISM policy attachments | ISM not available | Remove; use collection-level retention for time-series |
| `index.routing.allocation.*` | No node/shard concept | Remove |

### 4.3 Synonyms and Analysis Files

Self-managed clusters load synonym and stopword files from the node filesystem. Serverless does not have a filesystem. Options:

- **Inline synonyms**: Define synonyms directly in the analyzer settings using the `synonyms` parameter instead of `synonyms_path`.
- **Packages**: Upload synonym/stopword files as OpenSearch Serverless packages and reference them in index settings.

## 5. Data Migration Strategies

### 5.1 OpenSearch Ingestion (Recommended)

AWS-native pipeline service purpose-built for migrating to Serverless:

1. Create an OpenSearch Ingestion pipeline with your self-managed cluster as the source.
2. Set the Serverless collection as the destination.
3. The pipeline reads data from the source and writes to the collection using SigV4 auth.
4. Supports both one-time migration and continuous replication.

### 5.2 Bulk API via Application Code

Write a migration script that:

1. Reads documents from the self-managed cluster (scroll or PIT + search_after).
2. Transforms documents if needed (remove unsupported fields, adjust IDs).
3. Writes to the Serverless collection using the Bulk API with SigV4 signing.

**Important**: For time-series collections, do not include `_id` in the bulk request — IDs are auto-generated.

### 5.3 Logstash / Data Prepper

Use Logstash or Data Prepper with the OpenSearch output plugin configured for Serverless:

- Set the endpoint to the collection endpoint (e.g., `https://<collection-id>.<region>.aoss.amazonaws.com`).
- Enable SigV4 signing in the output plugin configuration.
- Note: The Serverless endpoint uses port 443, not 9200.

### 5.4 Snapshot and Restore

**Not supported** for Serverless. You cannot restore a snapshot into a Serverless collection. Use one of the above methods instead.

## 6. Client Code Changes

### 6.1 Endpoint

| Self-Managed | Serverless |
| :--- | :--- |
| `https://my-cluster:9200` | `https://<collection-id>.<region>.aoss.amazonaws.com` |

### 6.2 Authentication

All clients must switch to SigV4 request signing:

**Python (opensearch-py)**:
```python
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, 'us-east-1', 'aoss')

client = OpenSearch(
    hosts=[{'host': '<collection-id>.us-east-1.aoss.amazonaws.com', 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    connection_class=RequestsHttpConnection,
)
```

**Java (opensearch-java)**:
```java
SdkHttpClient httpClient = ApacheHttpClient.builder().build();
AwsSdk2Transport transport = new AwsSdk2Transport(
    httpClient,
    "<collection-id>.us-east-1.aoss.amazonaws.com",
    "aoss",
    Region.US_EAST_1,
    AwsSdk2TransportOptions.builder().build()
);
OpenSearchClient client = new OpenSearchClient(transport);
```

### 6.3 API Compatibility

Update client code to handle these differences:

- Remove any calls to `_cluster/*`, `_nodes/*`, `_snapshot/*` APIs.
- Replace Scroll API usage with PIT + `search_after`.
- For time-series workloads, remove explicit `_id` from index requests.
- Remove `_reindex` calls; handle reindexing externally.
- Remove ISM policy management calls.

## 7. Capacity and Cost

### 7.1 OCU Model

Serverless capacity is measured in OpenSearch Compute Units (OCUs):

- **Indexing OCUs**: Compute for data ingestion.
- **Search OCUs**: Compute for queries.
- Each OCU provides approximately 6 GiB of hot-tier memory.
- Minimum: 0.5 OCU for indexing + 0.5 OCU for search (with redundancy disabled) or 2 OCU each (with redundancy enabled).

### 7.2 Cost Components

| Component | Pricing Basis |
| :--- | :--- |
| Indexing compute | OCU-hours |
| Search compute | OCU-hours |
| Managed storage (S3) | GB-month |

### 7.3 When Serverless Is Cost-Effective

- Unpredictable or spiky traffic patterns.
- Small to medium data volumes (< 1 TB hot data).
- Teams without dedicated OpenSearch operational expertise.
- Workloads that can tolerate the minimum OCU floor cost.

### 7.4 When Provisioned Is More Cost-Effective

- Steady, predictable traffic.
- Large data volumes (> 1 TB).
- Need for features not available in Serverless (ISM, alerting, anomaly detection, snapshots).
- Cost-sensitive workloads where Reserved Instances provide savings.

Use the `opensearch-pricing-calculator` to compare provisioned vs. serverless costs (see `scripts/pricing_calculator.py`).

## 8. Monitoring

| Self-Managed | Serverless Equivalent |
| :--- | :--- |
| `_nodes/stats` | CloudWatch metrics (`SearchOCU`, `IndexingOCU`, `SearchableDocuments`) |
| `_cluster/health` | CloudWatch `CollectionStatus` metric |
| `_cat/indices` | Supported (without health/status columns) |
| Slow query logs | CloudWatch Logs (configure via collection settings) |
| Prometheus exporter | CloudWatch metrics (exportable to Prometheus via CloudWatch agent) |
| Custom dashboards (Grafana) | CloudWatch dashboards or Grafana with CloudWatch data source |
