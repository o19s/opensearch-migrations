# AWS OpenSearch Migration: Service Tooling and ETL Patterns

## Executive Summary

AWS does not provide a specialized "managed migration service" for OpenSearch specifically. Instead, migrations are accomplished using AWS general-purpose data integration services (AWS Glue, Lambda, Kinesis) combined with open-source tooling (Logstash, Data Prepper) running on AWS infrastructure (EC2, Fargate, ECS). This document covers the practical architectures, trade-offs, and implementation details for migrating data to OpenSearch Service at scale.

---

## Why No Dedicated OpenSearch Migration Service?

AWS's Database Migration Service (DMS) is optimized for relational databases (source and target both SQL-like). OpenSearch is a search engine with fundamentally different semantics:
- **No transactions**: OpenSearch indices are eventually consistent; DMS change data capture doesn't apply
- **Schema is optional**: OpenSearch allows documents with heterogeneous fields; relational normalization is not applicable
- **Indexing is computation-heavy**: Transformation and enrichment happen at ingest, not at rest

**Result**: Migration is a data *integration* problem, not a database replication problem. Use integration services instead.

---

## Service Tooling and Limitations

### AWS Database Migration Service (DMS) - Not Recommended
**What it does**: Replicates data from source database to target, supporting change data capture (CDC) for ongoing sync.

**For OpenSearch**:
- Source: Supported (any relational DB, MongoDB, etc.)
- Target: NOT supported (no native OpenSearch endpoint)

**Workaround**: DMS → S3 → Lambda → OpenSearch (adds 2 extra hops, defeats DMS value)

**Verdict**: Skip DMS; use service-specific tooling below.

### AWS Glue - Recommended for Batch Migration
**What it is**: Managed ETL service with pre-built connectors, Spark-based transformation, and job scheduling.

**Supported connectors**:
- **Source**: S3, RDS, DynamoDB, Kafka, JDBC (Solr via JDBC if available), or custom Python code
- **Target**: S3, Redshift, DynamoDB; OpenSearch via Glue PySpark custom script

**Typical Architecture**
```
Source (Solr) → JDBC/HTTP export to S3 → Glue Spark job → Transform/batch → OpenSearch Bulk API
```

**Strengths**
- Serverless (no infrastructure to manage)
- Fault-tolerant (Spark handles retries, partitioning)
- Scalable (handles 10+ GB documents/run)
- Cost-effective for periodic batches

**Weaknesses**
- Startup latency (~3-5 minutes before first record is processed)
- Not ideal for real-time/continuous migration
- Requires writing Spark code (PySpark preferred over Scala)

**Cost**: ~$0.48/DPU-hour; typical job uses 2-5 DPUs for 1-2 hours
- Small batch (100 GB): $5-10
- Large batch (1 TB): $20-40

**When to use**
- Migrating historical/archive data (bulk, one-time)
- Data requires complex transformation
- Source is a relational database; needs join/aggregation before indexing

---

### AWS Lambda - Best for Lightweight, Real-Time Migration

**What it is**: Serverless compute; runs custom code on event trigger.

**For OpenSearch migration**:
- **Trigger**: S3 upload, SQS queue, Kinesis stream, or scheduled
- **Code**: Python/Node.js using opensearch-py or opensearch-js library
- **Destination**: OpenSearch via HTTP/HTTPS

**Simple Architecture: S3 + Lambda**
```
1. Export Solr data to S3 (JSONL format, one doc per line)
2. Lambda function triggered on S3 upload
3. Lambda reads JSONL, batches docs, calls OpenSearch bulk API
4. OpenSearch indexes docs
```

**Example Lambda Function (Python)**
```python
import json
import boto3
from opensearchpy import OpenSearch

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    es = OpenSearch(
        hosts=['https://my-domain.us-east-1.es.amazonaws.com'],
        use_ssl=True,
        verify_certs=True,
        http_auth=None  # Use IAM role auth
    )

    # Get S3 object
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    obj = s3.get_object(Bucket=bucket, Key=key)

    # Process JSONL
    docs = []
    for line in obj['Body'].iter_lines():
        doc = json.loads(line)
        docs.append({
            '_index': 'migration-index',
            '_source': doc
        })
        if len(docs) >= 100:  # Batch
            es.bulk(index='migration-index', actions=docs)
            docs = []

    if docs:
        es.bulk(index='migration-index', actions=docs)

    return {'statusCode': 200, 'processed': len(docs)}
```

**Strengths**
- Zero infrastructure management
- Scales automatically (concurrent Lambdas)
- Very cheap (~$0.0000002 per invocation)
- Great for event-driven migration

**Weaknesses**
- 15-minute timeout limit (entire migration must complete in 15 min or split into smaller batches)
- Cold start latency (~1 second) adds up for many parallel invocations
- Not ideal for > 50 GB files (need to stream/chunk)

**Cost**: Negligible; ~$0.10 per GB migrated (1M invocations free tier covers small migrations)

**When to use**
- Incremental migration of new data
- S3 as intermediate staging
- Lightweight transformation logic
- < 100 GB total data

---

### Kinesis Data Streams - For Continuous/Streaming Migration

**What it is**: Managed message queue (like Kafka) with configurable retention and shard scaling.

**For OpenSearch migration**:
- **Source**: Solr export process writes to Kinesis stream
- **Consumer**: Lambda or Fargate task reading stream, writing to OpenSearch
- **Retention**: 24 hours (default) to 365 days (long-term replay)

**Typical Architecture**
```
Solr export process (EC2) → Kinesis Data Stream → Lambda consumer → OpenSearch
```

**Strengths**
- Exactly-once delivery guarantees (with state management)
- Handles bursty ingest (auto-scales shards)
- Real-time replay capability (if migration fails, restart from checkpoint)
- Works with both batch and real-time sources

**Weaknesses**
- Cost per shard (~$0.03/hour per shard + data throughput)
- Operational overhead (monitoring shard scaling)
- Overkill for one-time migrations

**Cost**: ~$30/month per shard + $0.25 per million PUT requests
- Small continuous stream (1 shard): $40-50/month
- Large bursty stream (10 shards auto-scaling): $300-500/month

**When to use**
- Ongoing data sync during migration (dual-write period)
- Real-time failover testing (Solr and OpenSearch in parallel)
- Long retry window needed (24+ hours)

---

## Open-Source Tooling: Logstash and Data Prepper

### Logstash on EC2/Fargate - Battle-Tested, Widely Used

**What it is**: Open-source log/data pipeline tool (part of Elastic Stack). Reads from many sources, transforms, writes to many destinations.

**Logstash Architecture**
```
Input plugins (Solr HTTP, S3, file) → Filter plugins (grok, mutate, ruby) → Output plugins (OpenSearch, S3)
```

**For OpenSearch migration**:
- **Input**: Solr export (HTTP API, CSV, JSON file)
- **Filter**: Field mapping, data type conversion, enrichment
- **Output**: OpenSearch bulk API or direct indexing

**Example Logstash Pipeline (Solr → OpenSearch)**
```
input {
  # Option 1: Read exported JSON from S3
  s3 {
    bucket => "my-bucket"
    key => "solr-export/*.json"
    region => "us-east-1"
  }
  # Or: Option 2: Read from Solr API directly (less common)
}

filter {
  # Parse JSON lines
  json {
    source => "message"
    target => "parsed"
  }

  # Map Solr field names to OpenSearch (if needed)
  mutate {
    rename => {
      "[parsed][solr_field_1]" => "os_field_1"
      "[parsed][solr_field_2]" => "os_field_2"
    }
    # Remove unnecessary Solr metadata
    remove_field => ["[parsed][_version_]"]
  }
}

output {
  # Write to OpenSearch
  opensearch {
    hosts => ["https://my-domain.us-east-1.es.amazonaws.com:9200"]
    index => "migrated-index-%{+YYYY.MM.dd}"
    user => "migration-user"
    password => "${OPENSEARCH_PASSWORD}"  # Pass via env var or Secrets Manager
  }

  # Also write to S3 for backup/audit
  s3 {
    bucket => "my-bucket"
    key => "opensearch-migrated/%{+YYYY/MM/dd}/%{[@timestamp]}.json"
  }
}
```

**Deployment Options**

1. **EC2 (Single Large Instance)**
   - Instance type: m5.2xlarge or larger (16+ GB RAM for buffering)
   - Throughput: 1K-10K docs/sec (depends on transformation complexity)
   - Cost: ~$300-500/month (plus storage for staging)
   - Advantage: Simple; one place to monitor/debug
   - Disadvantage: Single point of failure; not elastic

2. **Fargate (Containerized, Elastic)**
   - Container image: `logstash:8.x` from Docker Hub
   - CPU/memory: 2 CPU, 4 GB RAM (for 1K docs/sec); scale up as needed
   - Throughput: Auto-scales with task count (add tasks for parallel pipelines)
   - Cost: ~$100-300/month for 2-3 tasks + data transfer
   - Advantage: Stateless; replicas are redundant; auto-scaling
   - Disadvantage: Slightly higher latency; need to manage task replacement

**Strengths**
- Mature, production-proven (used by thousands of organizations)
- Extensive filter library (100+ plugins available)
- Good error handling and backpressure
- Easy to debug (stdout logging, dry-run mode)

**Weaknesses**
- Memory-hungry (JVM + buffering; requires 4-8 GB per pipeline)
- Startup time (30-60 seconds to warm up)
- Maintenance burden (JVM upgrades, plugin compatibility)
- Cost for long-running pipelines (Fargate hourly vs Lambda per-invocation)

**Cost Comparison** (migrating 1 TB)
- Lambda (S3-triggered): ~$5 (if < 15 min per file)
- Glue (1-hour job): ~$25
- Logstash on Fargate (2 tasks, 10 hours): ~$20
- Logstash on EC2 (1 week, reserved instance): ~$70

**When to use Logstash**
- Complex field transformations (multiple filters needed)
- Long-running pipeline (> 15 minutes; exceeds Lambda timeout)
- Multiple sources into one destination (Solr + Kafka → OpenSearch)
- Team is already familiar with ELK Stack

---

### OpenSearch Ingestion (Managed Data Prepper)

**What it is**: AWS-managed, serverless alternative to Logstash; uses Data Prepper pipeline DSL under the hood.

**Announcement**: Generally available as of late 2024 (new service, still being expanded)

**Architecture**
```
Data source (HTTP, S3, OTel) → Managed OpenSearch Ingestion → Pipeline (transform, enrich, filter) → OpenSearch domain
```

**Supported Sources** (as of 2024)
- **HTTP**: Custom push (application sends data)
- **S3**: Batch import
- **Trace**: OpenTelemetry Protocol (OTLP)
- **CloudWatch Logs**: Log ingestion (via log group subscription)
- Limited compared to Logstash

**Pricing**
- Per OpenSearch Ingestion Unit (IU): ~$0.50/hour (~$365/month per IU)
- Auto-scales from 1-10 IUs based on throughput
- Typical cost: $500-2000/month for production pipeline

**Example OpenSearch Ingestion Pipeline (Minimal)**
```yaml
source:
  http:
    path: "/logs"
processor:
  - grok:
      pattern: '%{COMMONLOGFORMAT}'
sink:
  - opensearch:
      hosts: ["https://my-domain.us-east-1.es.amazonaws.com"]
      aws_sigv4: true
      index: "logs-%{+YYYY.MM.dd}"
```

**Strengths**
- Fully serverless (no infrastructure to manage)
- AWS-native (excellent IAM integration, CloudWatch monitoring)
- Low operational overhead
- Good for log pipelines (tight CloudWatch integration)

**Weaknesses**
- Much newer; fewer plugins and filters than Logstash
- Higher cost than self-managed (Logstash on Fargate)
- Limited source support (Solr migration not directly supported; need intermediate S3)
- Pipeline DSL is less mature/documented than Logstash

**When to use OpenSearch Ingestion**
- AWS-first mindset; prefer managed services
- CloudWatch Logs as primary source
- Budget allows $500+/month for convenience
- Don't need highly custom transformations

---

## Data Prepper: Deep Dive on the Engine

**What it is**: Open-source, standalone pipeline framework (similar to Logstash) developed and maintained by OpenSearch community.

**Key difference from Logstash**: Data Prepper is lightweight, Java-based, and focuses on observability pipelines (metrics, traces, logs).

**Pipeline Model**
```
Source (read data) → Processors (transform) → Sink (write data)
```

**Example Processors** (transformations available)
- **grok**: Parse unstructured text (regex patterns)
- **mutate**: Rename, add, remove fields
- **aggregate**: Group events by field (e.g., sum metrics)
- **service-map**: Build dependency graphs (for traces)
- **date**: Parse timestamps
- **translate**: Map values (e.g., HTTP status 200 → "OK")

**Solr Source Plugin (Availability and Limitations)**

As of 2024:
- **Official plugin**: No first-class Solr source in Data Prepper core
- **Workaround**: Export Solr → JSON/CSV → S3 or HTTP → Data Prepper → OpenSearch
- **Future**: Community contributions for Solr source plugin are possible

**Example Data Prepper Pipeline for Solr Migration**
```yaml
# File: solr-migration.yaml
source:
  s3:
    bucket: "my-bucket"
    key_path: "solr-export/*.jsonl"
    region: "us-east-1"

processors:
  - json:
      source: "message"
      destination: "payload"
  - mutate:
      remove_entries_with_empty_values: true
      rename_keys:
        solr_id: "_id"
        solr_title: "title"
        solr_body: "content"

sink:
  - opensearch:
      hosts: ["https://my-domain.us-east-1.es.amazonaws.com"]
      username: "${OPENSEARCH_USER}"
      password: "${OPENSEARCH_PASSWORD}"
      index: "solr-migrated-%{+YYYY.MM.dd}"
      batch_size: 500
```

**Deployment** (Data Prepper as a service)
- Docker container: `opensearchproject/data-prepper:latest`
- Run on EC2, ECS, Kubernetes
- Lightweight (512 MB RAM sufficient for 1K docs/sec)

**Cost** (compared to Logstash on Fargate)
- EC2 t3.medium: ~$30/month + storage
- Fargate 0.5 CPU, 1 GB: ~$50/month
- Data Prepper is ~30% lighter on resources than Logstash (JVM tuning)

**When to use Data Prepper**
- Observability workload (metrics, traces, logs)
- Want to avoid Elastic Stack licensing concerns
- Lightweight pipeline (1-2 simple transforms)
- Team prefers open-source tooling

---

## Common Migration Patterns: Recommended Architectures

### Pattern 1: Small Migration (< 100 GB) - S3 + Lambda

**Scenario**: Solr cluster has < 100 GB; migration is one-time; downtime acceptable.

**Architecture**
```
1. Export Solr to S3 (using Solr export API or SolrJ)
   solr_exporter.sh → s3://my-bucket/solr-export/

2. Lambda function triggered on S3 upload
   - Reads JSONL file
   - Maps Solr fields to OpenSearch schema
   - Batches into bulk API calls
   - Writes to OpenSearch

3. Monitor via CloudWatch Logs
```

**Solr Export** (using curl)
```bash
# Query Solr, export to JSON
curl 'http://solr-host:8983/solr/my-collection/select?q=*:*&rows=10000&wt=json' \
  | jq -r '.response.docs[]' > solr-docs.jsonl

# Upload to S3
aws s3 cp solr-docs.jsonl s3://my-bucket/solr-export/
```

**Lambda Handler** (simplified version above in Lambda section)

**Pros**
- Simple, minimal moving parts
- Cheap (~$5-20 total)
- Fast (hours, not days)
- Easy to retry or replay

**Cons**
- Not suitable for > 100 GB (Lambda timeout, file size limits)
- Limited transformation logic
- No real-time sync capability

**Cost**: ~$10-50 (mostly S3 storage, Lambda is negligible)

---

### Pattern 2: Medium Migration (100 GB - 10 TB) - Logstash on Fargate

**Scenario**: Solr cluster 100 GB - 10 TB; can tolerate 1-7 days of migration; want transformation logic.

**Architecture**
```
1. Export Solr to S3 in parallel chunks
   - Split Solr collection into ranges (by ID or date)
   - Each range exported as separate JSONL file
   - Store in s3://bucket/solr-export/chunk-*.jsonl

2. Fargate task runs Logstash pipeline
   - Input: S3 bucket (reads all chunks in parallel)
   - Filter: Field mapping, type conversion
   - Output: OpenSearch bulk API

3. Logstash outputs to CloudWatch for monitoring

4. On success, checkpoint and clean up S3
```

**Logstash Dockerfile**
```dockerfile
FROM docker.elastic.co/logstash/logstash:8.11.0

COPY logstash-pipeline.conf /usr/share/logstash/pipeline/
COPY logstash.yml /usr/share/logstash/config/
RUN logstash-plugin install logstash-output-opensearch
```

**Logstash Config (solr-to-opensearch.conf)**
```
input {
  # Read multiple S3 files
  s3 {
    bucket => "my-bucket"
    key => "solr-export/chunk-*.jsonl"
    region => "us-east-1"
    codec => json
  }
}

filter {
  # Map Solr fields
  mutate {
    rename => {
      "id" => "_id"
      "title" => "title"
      "body" => "content"
      "timestamp" => "@timestamp"
    }
    convert => {
      "likes" => "integer"
      "rating" => "float"
    }
    remove_field => ["_version_", "_timestamp_", "internal_field"]
  }

  # Parse timestamp if needed
  date {
    match => ["@timestamp", "ISO8601"]
    target => "@timestamp"
  }
}

output {
  # Write to OpenSearch with bulk API
  opensearch {
    hosts => ["https://${OPENSEARCH_HOST}:9200"]
    aws_sigv4 => true
    region => "us-east-1"
    iam_role => "my-iam-role"  # Fargate task IAM role
    index => "solr-migrated-%{+YYYY.MM.dd}"
    batch_size => 1000
    flush_interval => 5
  }

  # CloudWatch Logs for progress tracking
  cloudwatch_logs {
    log_group_name => "/ecs/solr-migration"
    log_stream_name => "logstash-pipeline"
    region => "us-east-1"
  }
}
```

**Fargate Task Definition** (simplified)
```json
{
  "family": "solr-migration",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "logstash",
      "image": "my-account.dkr.ecr.us-east-1.amazonaws.com/logstash:solr-migration",
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/solr-migration",
          "awslogs-region": "us-east-1"
        }
      },
      "environment": [
        {
          "name": "OPENSEARCH_HOST",
          "value": "my-domain.us-east-1.es.amazonaws.com"
        }
      ]
    }
  ]
}
```

**Pros**
- Scales to 10+ TB easily
- Flexible transformation logic
- Parallel processing (multiple tasks/workers)
- Checkpointing + replay on failure

**Cons**
- Requires containerization knowledge
- Ongoing Fargate costs (~$200-500/month while running)
- Some operational overhead (monitoring tasks, troubleshooting)

**Cost**: ~$500-2000 (Fargate runtime 3-10 days, ~$150-400/day)

---

### Pattern 3: Large-Scale, Real-Time Sync (> 10 TB) - Kinesis + Lambda

**Scenario**: Solr cluster > 10 TB; need continuous sync during cutover; want dual-write capability.

**Architecture**
```
1. Phase 1: Bulk migration (use Logstash/Glue)
   - Export all historical Solr data to OpenSearch

2. Phase 2: Enable dual-write (application code changes)
   - Application writes to both Solr and OpenSearch
   - Reduces cutover risk; allows A/B testing

3. Phase 3: Real-time catch-up (Kinesis)
   - Solr replication stream → Kinesis Data Stream
   - Lambda consumer reads stream, writes to OpenSearch
   - Handles any updates between Phase 1 and cutover

4. Cutover: Switch application to read from OpenSearch
   - Solr remains live as fallback for 24 hours
```

**Dual-Write Application Code** (Spring Boot example)
```java
@Service
public class SearchService {
    private final OpenSearchTemplate opensearchTemplate;
    private final SolrTemplate solrTemplate;

    public void indexDocument(DocumentDTO doc) {
        // Write to both systems
        opensearchTemplate.save(doc);  // Non-blocking, async preferred
        solrTemplate.save(doc);         // Sync, primary

        logger.info("Indexed to Solr and OpenSearch: {}", doc.getId());
    }

    public List<DocumentDTO> search(String query) {
        // Read from OpenSearch (new system)
        // Fallback to Solr if OpenSearch unavailable
        try {
            return opensearchTemplate.search(query, DocumentDTO.class);
        } catch (Exception e) {
            logger.warn("OpenSearch unavailable, falling back to Solr", e);
            return solrTemplate.search(query, DocumentDTO.class);
        }
    }
}
```

**Kinesis Lambda Consumer**
```python
def lambda_handler(event, context):
    es = OpenSearch(
        hosts=['https://my-domain.us-east-1.es.amazonaws.com'],
        use_ssl=True,
        http_auth=None
    )

    docs_to_index = []

    for record in event['Records']:
        # Kinesis payload: Solr document (JSON)
        payload = json.loads(base64.b64decode(record['kinesis']['data']))

        # Transform Solr doc to OpenSearch
        transformed = transform_solr_to_opensearch(payload)
        docs_to_index.append({
            '_id': transformed['_id'],
            '_source': transformed
        })

    # Bulk index to OpenSearch
    if docs_to_index:
        es.bulk(index='solr-sync', actions=docs_to_index)

    # Mark Kinesis record as processed
    return {
        'batchItemFailures': []  # Empty if all successful
    }
```

**Pros**
- Handles large-scale, continuous sync
- Supports fallback (Solr remains available during cutover)
- Kinesis replay capability (if lambda fails, restart from checkpoint)
- Minimal latency (Kinesis stream → Lambda → OpenSearch ~1-5 seconds)

**Cons**
- Application code changes (dual-write logic)
- Kinesis operational overhead (monitoring, scaling, retries)
- Higher cost (~$300-500/month for stream + Lambda)
- Complexity: 3-phase migration requires careful coordination

**Cost**: ~$30/month (Kinesis stream, 1 shard) + Lambda (~$50-100/month)

---

### Pattern 4: Glue ETL for Complex Transformations

**Scenario**: Source is relational DB (RDS) feeding Solr; migration requires join/aggregation before indexing.

**Architecture**
```
1. Glue Crawler scans RDS schema
2. Glue Spark job:
   - Read from RDS (using JDBC)
   - Join multiple tables
   - Aggregate/enrich data
   - Output to OpenSearch via Spark connector
3. Schedule Glue job weekly/daily for incremental updates
```

**Glue PySpark Code**
```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql.types import *

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'OPENSEARCH_HOST'])

spark = SparkSession.builder.appName(args['JOB_NAME']).getOrCreate()

# Read from RDS
jdbc_url = "jdbc:postgresql://my-rds.us-east-1.rds.amazonaws.com:5432/mydb"
table = "documents"

df = spark.read \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", table) \
    .option("user", "postgres") \
    .option("password", "secret") \
    .load()

# Transform: rename fields, add computed fields
df_transformed = df \
    .withColumnRenamed("doc_id", "_id") \
    .withColumnRenamed("doc_title", "title") \
    .withColumn("indexed_at", current_timestamp())

# Write to OpenSearch via S3 (Glue → S3 → OpenSearch)
# (Direct write not supported; use S3 intermediate)
df_transformed.coalesce(1).write \
    .format("json") \
    .mode("overwrite") \
    .save("s3://my-bucket/glue-output/")

print("Successfully wrote to S3")
```

**Pros**
- Handles complex transformations (joins, aggregations)
- Batch processing (scheduled weekly/daily)
- Cost-effective for periodic updates
- Managed, serverless infrastructure

**Cons**
- S3 intermediate required (no direct OpenSearch write in Glue)
- Startup latency (3-5 min before processing)
- JDBC drivers may need custom Glue connector

**Cost**: ~$0.48/DPU-hour; typical job uses 2-5 DPUs × 1-2 hours
- Weekly run (~$10-20/week): ~$50-100/month

---

## VPC Considerations During Migration

### Network Topology
```
┌─────────────────────────┐
│ AWS Account (on-prem VPN, data center, etc.)
│
│ ┌──────────┐           ┌─────────────┐
│ │ Solr     │  Export   │ Lambda/      │
│ │ Cluster  │──────────→│ Logstash     │
│ │ (EC2)    │  HTTPS    │ (Fargate)    │
│ └──────────┘           └──────┬───────┘
│                                │
│  S3 Bucket (intermediate)      │
│  (s3://bucket/solr-export/)    │
│                                │
│        ┌────────────────────────┘
│        │
│  ┌─────▼──────────────────┐
│  │ OpenSearch VPC Endpoint│ (Private, no public IP)
│  │ (my-domain)            │
│  └────────────────────────┘
│
└─────────────────────────┘
```

### Key Points

1. **Source Solr**: Can be on-prem, EC2, or external (via VPN/bastion)
2. **S3 intermediate**: No VPC required; public Internet usage is fine
3. **Migration compute (Lambda/Logstash)**: Must be in same VPC as OpenSearch or have VPC peering
4. **OpenSearch domain**: Deployed in VPC (preferred) or public endpoint (discouraged)

**Recommended VPC Setup for Migration**
```
Primary VPC (application, OpenSearch):
  - Public subnets: NAT gateway (for Logstash outbound S3 access)
  - Private subnets: OpenSearch domain (2-3 subnets for multi-AZ)

Migration subnets (temporary):
  - Fargate task in private subnet
  - Security group allows outbound to OpenSearch on port 9200
  - Security group allows outbound to S3 (via S3 Gateway endpoint)
  - No inbound from internet
```

**S3 Gateway Endpoint** (saves data transfer costs)
```
S3 is AWS-internal service; data to S3 doesn't cross internet.
No NAT/IGW needed for S3 access from private subnets.
Set up S3 Gateway endpoint to avoid NAT charges (~$32/month).
```

---

## Data Transfer Costs During Migration

### Calculation Framework
- **Intra-AZ transfer**: $0.00 (free)
- **Cross-AZ transfer**: $0.02/GB
- **Cross-region transfer**: $0.02/GB (same as cross-AZ to another region)
- **Internet egress**: $0.09/GB (avoid this during migration)

### Migration Cost Example (1 TB Solr → OpenSearch)

**Scenario: Solr in us-east-1, OpenSearch in us-east-1 (same AZ)**
- Solr → S3: ~$0 (intra-AZ, if using S3 Gateway endpoint)
- S3 → Lambda/Logstash: ~$0 (S3 Gateway endpoint, intra-AZ)
- Lambda/Logstash → OpenSearch: ~$0 (intra-AZ, same VPC)
- **Total data transfer cost: ~$0**

**Scenario: Solr in on-prem, OpenSearch in AWS (cross-region)**
- On-prem → S3 (via VPN): ~$20 (1 TB × $0.02/GB cross-region)
- S3 → OpenSearch: ~$0 (intra-AWS, free with Gateway endpoint)
- **Total data transfer cost: ~$20**

**Scenario: Solr in us-east-1, OpenSearch in eu-west-1 (disaster recovery replica)**
- S3 (us-east-1) → S3 (eu-west-1): ~$20 (1 TB × $0.02/GB cross-region replication)
- S3 → OpenSearch (eu-west-1): ~$0
- **Total data transfer cost: ~$20**

### Optimization Tips
1. **Use S3 Gateway endpoint**: Saves $0.02/GB on S3 access from VPC
2. **Keep source and target in same region/AZ**: Eliminates cross-AZ/cross-region charges
3. **Batch small files**: Combining many small transfers saves overhead
4. **Use Kinesis if real-time**: Kinesis → OpenSearch is free (same service, same region)

---

## Summary and Recommendations

| Migration Size | Recommended Tool | Estimated Time | Cost |
|---|---|---|---|
| < 10 GB | Lambda + S3 | Hours | $5-20 |
| 10-100 GB | Glue ETL or Lambda | Hours | $20-100 |
| 100 GB - 5 TB | Logstash on Fargate | Days (1-3) | $200-1000 |
| 5-50 TB | Logstash on Fargate (multi-task) + Kinesis | Weeks (parallel) | $1000-5000 |
| > 50 TB | Enterprise consulting + custom tooling | Weeks-months | Custom |

**For Solr-to-OpenSearch migrations specifically**:
1. **Bulk migration**: Use Logstash on Fargate (proven, flexible)
2. **Real-time sync**: Use Kinesis + Lambda with dual-write application
3. **Validation**: Run both systems in parallel for 24-72 hours post-cutover
4. **Fallback**: Keep Solr available for 1 week post-cutover in read-only mode

**Avoid**:
- Database Migration Service (DMS): No OpenSearch target support
- Direct Elasticsearch modules: OpenSearch is compatible but not identical to ES 7.10

---

## Appendix: Solr Export Strategies

### Strategy 1: Solr Export API (Simple, Recommended)
```bash
#!/bin/bash
# Export Solr collection to JSONL

SOLR_HOST="solr-host"
SOLR_PORT="8983"
COLLECTION="my-collection"
OUTPUT_DIR="/tmp/solr-export"

mkdir -p $OUTPUT_DIR

# Export in chunks (handles large collections)
for START in {0..1000000..100000}; do
  curl -s "http://${SOLR_HOST}:${SOLR_PORT}/solr/${COLLECTION}/select?q=*:*&start=${START}&rows=100000&wt=json" \
    | jq -r '.response.docs[]' >> "${OUTPUT_DIR}/docs-${START}.jsonl"

  # Check if we got results
  COUNT=$(jq '.response.numFound' <<< "$(curl -s "http://${SOLR_HOST}:${SOLR_PORT}/solr/${COLLECTION}/select?q=*:*&start=${START}&rows=1&wt=json")")
  if [ $START -gt $COUNT ]; then
    break
  fi
done

# Upload to S3
aws s3 cp $OUTPUT_DIR s3://my-bucket/solr-export/ --recursive
```

### Strategy 2: SolrJ (Programmatic, Recommended for Application Context)
```java
// In Spring Boot application
@Configuration
public class SolrExporter {

    @Bean
    public void exportSolrToFile() {
        CloudSolrClient solrClient = new CloudSolrClient.Builder()
            .withZkHosts("zk-host:2181")
            .build();
        solrClient.setDefaultCollection("my-collection");

        SolrQuery query = new SolrQuery("*:*");
        query.setRows(10000);

        List<SolrDocument> docs = new ArrayList<>();
        int offset = 0;

        while (offset < 1000000) {  // Adjust for your collection size
            query.setStart(offset);
            QueryResponse response = solrClient.query(query);

            List<SolrDocument> batch = response.getResults();
            docs.addAll(batch);

            if (batch.isEmpty()) break;
            offset += 10000;
        }

        // Write to JSONL
        try (Writer w = Files.newBufferedWriter(Paths.get("/tmp/solr-export.jsonl"))) {
            for (SolrDocument doc : docs) {
                w.write(doc.toString());
                w.write("\n");
            }
        }
    }
}
```

### Strategy 3: DataImportHandler (If using DIH for ingestion)
- Less common for export; primarily an ingestion tool
- Not recommended for migration

---

**Final recommendation**: For most Solr-to-OpenSearch migrations, start with **Logstash on Fargate** (100 GB - 10 TB) or **Lambda + S3** (< 100 GB). Both are battle-tested, AWS-native, and cost-effective.
