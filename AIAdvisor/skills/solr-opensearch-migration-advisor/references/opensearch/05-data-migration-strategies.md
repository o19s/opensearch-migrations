# Data Migration Strategies: Self-Managed to AWS OpenSearch

This document covers the available methods for migrating data from a self-managed OpenSearch cluster to AWS managed domains or Serverless collections.

## 1. Strategy Overview

| Strategy | Target: Managed Domain | Target: Serverless | Downtime | Complexity |
| :--- | :--- | :--- | :--- | :--- |
| Snapshot and restore | ✅ Recommended | ❌ Not supported | Minutes (restore time) | Low |
| Reindex from remote | ✅ Supported | ❌ Not supported | Near-zero (live) | Medium |
| OpenSearch Ingestion (OSI) | ✅ Supported | ✅ Recommended | Near-zero (live) | Medium |
| Logstash / Data Prepper | ✅ Supported | ✅ Supported | Near-zero (live) | Medium |
| Custom bulk API script | ✅ Supported | ✅ Supported | Varies | High |
| Reindexing from Snapshot (RFS) | ✅ Supported | ❌ Not supported | Near-zero (live) | Medium |

## 2. Snapshot and Restore (Managed Domain Only)

The fastest and simplest method for migrating to a managed domain.

### 2.1 Prerequisites

- Self-managed cluster and managed domain must be compatible OpenSearch versions (target >= source).
- An S3 bucket accessible by both the self-managed cluster and the managed domain.
- IAM role with S3 permissions for the managed domain to access the snapshot bucket.

### 2.2 Steps

**On the self-managed cluster:**

1. Install the `repository-s3` plugin (if not already installed).
2. Register the S3 snapshot repository:

```json
PUT _snapshot/migration-repo
{
  "type": "s3",
  "settings": {
    "bucket": "my-migration-snapshots",
    "region": "us-east-1"
  }
}
```

3. Take a snapshot:

```json
PUT _snapshot/migration-repo/snapshot-1
{
  "indices": "*",
  "ignore_unavailable": true,
  "include_global_state": false
}
```

**On the managed domain:**

4. Register the same S3 bucket as a snapshot repository (requires passing an IAM role ARN):

```json
PUT _snapshot/migration-repo
{
  "type": "s3",
  "settings": {
    "bucket": "my-migration-snapshots",
    "region": "us-east-1",
    "role_arn": "arn:aws:iam::123456789012:role/OpenSearchSnapshotRole"
  }
}
```

5. Restore the snapshot:

```json
POST _snapshot/migration-repo/snapshot-1/_restore
{
  "indices": "*",
  "ignore_unavailable": true,
  "include_global_state": false
}
```

### 2.3 Important Notes

- Do **not** restore the `.opendistro_security` index — recreate security configuration on the managed domain.
- Use `rename_pattern` and `rename_replacement` if index names need to change.
- For large datasets, consider taking incremental snapshots to reduce restore time.
- The managed domain must have enough storage to hold all restored indices.

## 3. Reindex from Remote (Managed Domain Only)

Pull data directly from the self-managed cluster into the managed domain.

### 3.1 Prerequisites

- Network connectivity between the managed domain and the self-managed cluster.
- The self-managed cluster endpoint must be allowlisted in the managed domain's remote reindex settings.

### 3.2 Configuration

Add the self-managed cluster to the managed domain's allowlist via the AWS console or API:

```
reindex.remote.whitelist: ["self-managed-host:9200"]
```

### 3.3 Execution

```json
POST _reindex
{
  "source": {
    "remote": {
      "host": "https://self-managed-host:9200",
      "username": "admin",
      "password": "admin"
    },
    "index": "source-index",
    "size": 1000
  },
  "dest": {
    "index": "dest-index"
  }
}
```

### 3.4 Considerations

- Slower than snapshot/restore for large datasets.
- Useful for selective migration (specific indices or filtered documents).
- The source cluster must remain available during the entire reindex operation.
- Network bandwidth between source and destination affects throughput.

## 4. OpenSearch Ingestion (OSI)

AWS-managed pipeline service for data migration. Works with both managed domains and Serverless.

### 4.1 Architecture

```
Self-Managed Cluster → OSI Pipeline → Managed Domain / Serverless Collection
```

### 4.2 Pipeline Configuration

```yaml
version: "2"
opensearch-migration-pipeline:
  source:
    opensearch:
      hosts: ["https://self-managed-host:9200"]
      username: "admin"
      password: "admin"
      indices:
        include:
          - index_name_regex: ".*"
  sink:
    - opensearch:
        hosts: ["https://search-my-domain.us-east-1.es.amazonaws.com"]
        aws:
          sts_role_arn: "arn:aws:iam::123456789012:role/OSIPipelineRole"
          region: "us-east-1"
        index: "${getMetadata(\"opensearch-index\")}"
```

### 4.3 Advantages

- Managed infrastructure — no pipeline servers to maintain.
- Supports both one-time migration and continuous replication.
- Built-in transformations (rename fields, filter documents, etc.).
- Works with VPC-based and public source clusters.
- Supports Serverless as a destination (unlike snapshot/restore and reindex).

### 4.4 Considerations

- Additional cost for the OSI pipeline compute.
- Pipeline must have network access to both source and destination.
- For VPC-based sources, the pipeline must be in the same VPC or a peered VPC.

## 5. Logstash / Data Prepper

Use open-source pipeline tools as an intermediary.

### 5.1 Logstash Configuration

```ruby
input {
  opensearch {
    hosts => ["https://self-managed-host:9200"]
    user => "admin"
    password => "admin"
    index => "my-index"
    query => '{ "query": { "match_all": {} } }'
    scroll => "5m"
    size => 1000
  }
}

output {
  opensearch {
    hosts => ["https://search-my-domain.us-east-1.es.amazonaws.com"]
    auth_type => {
      type => "aws_iam"
      aws_access_key_id => ""
      aws_secret_access_key => ""
      region => "us-east-1"
    }
    index => "my-index"
  }
}
```

### 5.2 Data Prepper Configuration

```yaml
source:
  opensearch:
    hosts: ["https://self-managed-host:9200"]
    username: "admin"
    password: "admin"
    indices:
      include:
        - index_name_regex: "my-index"

sink:
  - opensearch:
      hosts: ["https://search-my-domain.us-east-1.es.amazonaws.com"]
      aws:
        sts_role_arn: "arn:aws:iam::123456789012:role/DataPrepperRole"
        region: "us-east-1"
```

### 5.3 Considerations

- Requires running and managing the pipeline infrastructure yourself.
- More flexible than OSI for complex transformations.
- Can run on EC2, ECS, or Kubernetes.

## 6. Reindexing from Snapshot (RFS)

An open-source tool from the OpenSearch Migrations project that reads directly from snapshot files and writes to the target cluster.

### 6.1 When to Use

- Large datasets where snapshot/restore is preferred but the target is a different version.
- Need to transform data during migration.
- Want to parallelize the migration across multiple workers.

### 6.2 How It Works

1. Take a snapshot of the self-managed cluster to S3.
2. RFS reads the snapshot files directly (without restoring to an intermediate cluster).
3. RFS writes documents to the target managed domain via the Bulk API.

See: [opensearch-migrations GitHub repository](https://github.com/opensearch-project/opensearch-migrations)

## 7. Validation

After migration, validate data integrity:

### 7.1 Document Count

```json
GET source-index/_count    // on self-managed
GET dest-index/_count      // on AWS
```

### 7.2 Spot-Check Documents

```json
GET dest-index/_doc/<known-id>
```

### 7.3 Query Equivalence

Run representative queries against both clusters and compare:
- Result counts
- Top-N document IDs
- Aggregation values

### 7.4 Mapping Verification

```json
GET dest-index/_mapping
```

Compare with the source mapping to ensure all fields and types migrated correctly.

## 8. Cutover Strategies

### 8.1 Big Bang

1. Stop writes to the self-managed cluster.
2. Take a final snapshot or run a final sync.
3. Switch all clients to the AWS endpoint.
4. Resume writes.

**Downtime**: Minutes to hours depending on data volume.

### 8.2 Blue-Green with Dual Writes

1. Set up the AWS deployment and migrate historical data.
2. Configure applications to write to both clusters simultaneously.
3. Validate query results from the AWS deployment.
4. Switch reads to the AWS deployment.
5. Stop writes to the self-managed cluster.

**Downtime**: Near-zero.

### 8.3 DNS-Based Cutover

1. Migrate data and run both clusters in parallel.
2. Switch the DNS record from the self-managed endpoint to the AWS endpoint.
3. Monitor and roll back if needed.

**Downtime**: DNS propagation time (seconds to minutes with low TTL).
