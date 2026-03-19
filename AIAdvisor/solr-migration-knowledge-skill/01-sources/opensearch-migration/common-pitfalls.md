# Common Migration Pitfalls: Solr to OpenSearch

**Sources**:
- https://bigdataboutique.com/blog/solr-to-opensearch-migration-deep-dive
- https://opensearch.org/docs/latest/
- https://solr.apache.org/guide/
- Community migration experiences and incident reports

---

## Overview

Real-world Solr to OpenSearch migrations reveal predictable patterns of failure. This document captures lessons learned from production migrations, highlighting architectural differences that cause runtime issues, performance surprises, and data inconsistencies.

---

## Pitfall 1: Shard Collocation Differences

### The Issue

**Solr**: Allows primary shard and replica on the same node.

```
Node A: [Shard 1 Primary, Shard 2 Replica]
Node B: [Shard 1 Replica, Shard 2 Primary]
```

**OpenSearch**: Explicitly prevents primary and replica on the same node (by design).

```
Node A: [Shard 1 Primary]
Node B: [Shard 1 Replica]
```

### Why It Matters

**In Solr**: You can run a 3-node cluster with each node holding both shard 1 primary and shard 2 replica. This is dense and efficient.

**In OpenSearch**: The same setup requires 4 nodes minimum (2 for shard 1, 2 for shard 2). If you attempt co-location, OpenSearch rejects the allocation:

```
RoutingException: primary and replica of the same shard may not be allocated to the same node
```

### Remediation

**Pre-migration planning**:
1. Count Solr shards and replica count in your largest collections
2. Calculate minimum nodes needed: `shards * (1 + replicas)`
3. Provision OpenSearch cluster with this minimum
4. Budget 30% extra capacity for heap overhead (OpenSearch uses more memory than Solr for same data)

**Example**:
- Solr: 3 nodes, 4 shards, 1 replica per shard (fits via collocation)
- OpenSearch minimum: 8 nodes (4 shards × (1 primary + 1 replica), no collocation allowed)

---

## Pitfall 2: Relevance Scoring Differences (TF-IDF vs BM25)

### The Core Issue

**Solr** uses TF-IDF (Term Frequency - Inverse Document Frequency) by default.

**OpenSearch** uses BM25 (Best Matching 25) by default.

These scoring algorithms produce different result rankings, even with identical queries and documents.

### Concrete Example

**Query**: `title:machine learning`
**Document A**: Title contains "machine" once, "learning" once
**Document B**: Title contains "machine" three times, "learning" twice

| Scoring Metric | TF-IDF Result | BM25 Result |
|----------------|---------------|------------|
| Doc A Score | Lower | Higher |
| Doc B Score | Higher | Lower |

**Why**: BM25 saturates repetition—term frequency above ~2-3 provides diminishing returns. TF-IDF rewards raw frequency.

### Migration Symptoms

- Top 10 results are completely different between Solr and OpenSearch
- A/B testing shows 30-40% top-10 overlap instead of expected 80%+
- Customer complaints: "Search results got worse"
- No query logic is wrong; just ranking algorithm differs

### Remediation Strategies

**Option 1: Accept the difference**
- Run A/B testing for 2-4 weeks
- Collect user feedback on which system's results are "better"
- Many teams find BM25 produces better relevance
- If acceptable, move forward; no code change required

**Option 2: Custom similarity scoring**

Create a custom similarity class in Solr that matches BM25:

**Solr similarity plugin** (if migrating backward, less common):
```xml
<similarity class="org.apache.solr.similarity.BM25SimilarityFactory">
  <float name="k1">1.2</float>
  <float name="b">0.75</float>
</similarity>
```

**OpenSearch similarity** (can customize, but default BM25 is solid):
```json
{
  "settings": {
    "index": {
      "similarity": {
        "my_similarity": {
          "type": "BM25",
          "k1": 1.2,
          "b": 0.75
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "similarity": "my_similarity"
      }
    }
  }
}
```

**Option 3: Use function_score to boost specific signals**

If Solr relies on custom boost functions, replicate them in OpenSearch:

```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": "machine learning" } },
      "functions": [
        {
          "field_value_factor": {
            "field": "popularity",
            "modifier": "log1p",
            "factor": 1.2
          }
        }
      ],
      "boost_mode": "multiply"
    }
  }
}
```

### Testing Recommendation

**Before cutover**: Run shadow reads for 2-4 weeks, comparing top-10 result overlap. Target 75-85% overlap in top 10. If lower, investigate:
1. Is it just TF-IDF vs BM25?
2. Are custom boosts missing?
3. Are filter queries correctly translated?

---

## Pitfall 3: Commit and Refresh Semantics

### Solr Commit Types

**Soft commit**: Makes documents visible to searchers without persisting to disk.
```
q=*:*&commit=true&softCommit=true
```

**Hard commit**: Persists to disk, guarantees durability.
```
q=*:*&commit=true
```

**Auto-commit**: Background process commits periodically.
```xml
<autoCommit>
  <maxTime>15000</maxTime>
  <maxDocs>10000</maxDocs>
  <openSearcher>false</openSearcher>
</autoCommit>
```

### OpenSearch Refresh Semantics

**Refresh**: Makes documents visible to searchers; does NOT persist to disk.
```
POST /index/_refresh
```

**Fsync**: Persists transaction log to disk; does NOT refresh searchers.
```json
{
  "index": {
    "translog": {
      "durability": "request"
    }
  }
}
```

**Key difference**: Solr's soft commit ≈ OpenSearch's refresh. Solr's hard commit includes fsync; OpenSearch separates these concerns.

### Migration Pitfall

**Symptom**: After indexing, documents appear immediately in Solr but take seconds to appear in OpenSearch.

**Cause**: OpenSearch's default `refresh_interval` is 1 second. Solr's default auto-commit is immediate.

**Remediation**:

```json
{
  "settings": {
    "index": {
      "refresh_interval": "100ms"
    }
  }
}
```

**Trade-off**: Faster refresh = more indexing overhead. For high-throughput, use `refresh_interval: "1s"` or higher. For real-time search, use `"100ms"` or lower.

**Durability configuration**:

For guaranteed durability on every write (slower, like Solr hard commit):

```json
{
  "settings": {
    "index": {
      "translog": {
        "durability": "request",
        "sync_interval": "100ms"
      }
    }
  }
}
```

### Batch Indexing Best Practice

During migration, disable refresh entirely:

```json
{
  "settings": {
    "index": {
      "refresh_interval": "-1",
      "translog": {
        "durability": "async"
      }
    }
  }
}
```

Then, after bulk indexing completes:

```json
{
  "settings": {
    "index": {
      "refresh_interval": "1s",
      "translog": {
        "durability": "request"
      }
    }
  }
}
```

---

## Pitfall 4: Atomic Updates Have Different Semantics

### Solr Atomic Updates

Solr supports partial document updates:

```json
POST /update
{
  "add": { "price": 9.99, "last_modified": "NOW" }
}
```

Only the specified fields are updated; others preserved.

### OpenSearch Partial Updates

```json
POST /index/_update/doc_id
{
  "doc": {
    "price": 9.99,
    "last_modified": "2024-01-15"
  }
}
```

Semantically similar, but **important difference**: The document must exist, or you must use:

```json
POST /index/_update/doc_id
{
  "doc": { "price": 9.99 },
  "doc_as_upsert": true
}
```

### The Pitfall: Race Conditions

In Solr, atomic updates use versioning to prevent lost updates:

```json
{
  "set": { "price": 9.99 },
  "_version_": 5
}
```

**OpenSearch does NOT have built-in versioning for concurrent updates**. Instead, use `seq_no` and `primary_term`:

```json
PUT /index/_update/doc_id?if_seq_no=5&if_primary_term=1
{
  "doc": { "price": 9.99 }
}
```

### Remediation

If your application relies on Solr atomic updates with version checking:

1. **Option 1**: Migrate to full document replacements (simpler, less efficient)
2. **Option 2**: Implement optimistic locking using `seq_no` and `primary_term`
3. **Option 3**: Use document versioning in application layer (timestamp, UUID)

**Example with seq_no locking**:

```python
def update_price(doc_id, new_price):
    # First, get current seq_no
    doc = es.get(index="products", id=doc_id)
    seq_no = doc["_seq_no"]
    primary_term = doc["_primary_term"]

    # Update with version check
    try:
        es.update(
            index="products",
            id=doc_id,
            body={"doc": {"price": new_price}},
            if_seq_no=seq_no,
            if_primary_term=primary_term
        )
    except ConflictError:
        # Retry logic here
        retry_update_price(doc_id, new_price)
```

---

## Pitfall 5: ZooKeeper Removal - Operational Blindness

### What You Lose

In Solr, ZooKeeper is external, observable:

```bash
zkCli.sh -server localhost:2181
ls /collections/my_collection/shards
```

You can inspect cluster state independently, debug issues, even manually manipulate state.

**OpenSearch**: Cluster state is embedded in the cluster itself. You lose external observability.

### Migration Pitfall

**Symptom**: Node goes down, shards don't reallocate, customer data is unavailable, operators have no way to debug.

**Cause**: OpenSearch's cluster state is stored on master nodes. If too many masters fail, cluster loses quorum and stops accepting writes.

### Remediation

1. **Healthy master configuration**: Minimum 3 master-eligible nodes (5 recommended for production)

```yaml
# elasticsearch.yml
node.roles: [master, data]
cluster.initial_master_nodes: ["node-1", "node-2", "node-3"]
discovery.seed_hosts: ["node-1", "node-2", "node-3"]
```

2. **Observability**: Implement health checks

```bash
GET /_cluster/health
{
  "status": "green",
  "number_of_nodes": 6,
  "number_of_data_nodes": 3,
  "active_primary_shards": 10,
  "active_shards": 20
}
```

3. **Alerting**: Monitor cluster state continuously

```yaml
# Example Prometheus scrape
- alert: OpenSearchClusterUnhealthy
  expr: opensearch_cluster_health_status != 1  # 1 = green
  for: 5m
  action: page on-call
```

4. **Runbooks**: Document recovery procedures

- Single master failure: Automatically elected new master (quorum-based)
- Multiple master failures: Manual intervention (UnsafeBootstrapMasterNodeCommand)
- Data node failure: Shard rebalancing triggered automatically

---

## Pitfall 6: Schemaless Mode Defaults Differ

### Solr Schemaless

Enable with:
```
curl -X POST http://localhost:8983/solr/admin/configs?action=set-user-property&property.name=update.autoCreateFields&property.value=true
```

Any field in a document is automatically indexed as text. Very permissive.

### OpenSearch Dynamic Mapping

Default behavior (similar to Solr schemaless):

```json
{
  "mappings": {
    "dynamic": true
  }
}
```

**But OpenSearch's auto-mapping is more conservative**:

| Value Type | Solr | OpenSearch |
|------------|------|-----------|
| "2024-01-15" | text | date (if detected) + keyword |
| "true" | text | boolean |
| "123" | text | long |
| "123.45" | text | float |

### The Pitfall

During migration, if you relied on Solr schemaless with all fields as text, OpenSearch will auto-map numeric strings as numbers. Queries that worked in Solr break:

```
# Solr: Field is text, range query works
price:[100 TO 200]  # Finds "150" (string)

# OpenSearch: Field is auto-mapped as integer
"range": { "price": { "gte": 100, "lte": 200 } }  # Expects integer, rejects "150"
```

### Remediation

**Option 1**: Disable dynamic mapping and create explicit schema

```json
{
  "mappings": {
    "dynamic": false
  }
}
```

Then define all fields explicitly.

**Option 2**: Control auto-mapping behavior

```json
{
  "mappings": {
    "dynamic": "strict",  # Reject unmapped fields
    "properties": {
      "price": { "type": "keyword" }  # Force text even if numeric
    }
  }
}
```

**Option 3**: Use dynamic templates to force text

```json
{
  "mappings": {
    "dynamic_templates": [
      {
        "all_strings": {
          "match_mapping_type": "string",
          "mapping": {
            "type": "text"
          }
        }
      }
    ]
  }
}
```

---

## Pitfall 7: Custom Similarity Classes Don't Port

### Solr Custom Similarity

Solr allows custom similarity plugins:

```java
public class CustomSimilarity extends TFIDFSimilarity {
    @Override
    public float score(float freq, long norm) {
        return Math.log(freq) * norm;
    }
}
```

Configured in solrconfig.xml:

```xml
<similarity class="com.company.CustomSimilarity"/>
```

### OpenSearch Limitations

OpenSearch has **no way to upload custom Java code** at runtime. Plugin system exists but is cumbersome for similarity.

### Remediation

**Option 1**: Rewrite logic as function_score query

```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": "solr" } },
      "functions": [
        {
          "script_score": {
            "script": {
              "source": "Math.log(_score + 1)"
            }
          }
        }
      ]
    }
  }
}
```

**Option 2**: Accept OpenSearch's BM25 (often superior)

**Option 3**: Build a custom scoring microservice

- Index in OpenSearch with `_id` only
- Return top 1000 candidates
- Score in application layer with custom logic
- Return top 10 to user

Trade-off: Latency increases; flexibility increases.

---

## Pitfall 8: Function Queries Have Limited Equivalents

### Solr Function Queries

Solr supports in-query math functions:

```
q=title:solr&bf=sqrt(views)^2 log(1+clicks) product(rating,popularity)
```

### OpenSearch Equivalents

OpenSearch uses scripts:

```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": "solr" } },
      "functions": [
        {
          "script_score": {
            "script": {
              "source": "Math.sqrt(doc['views'].value) * Math.log(1 + doc['clicks'].value)"
            }
          }
        }
      ]
    }
  }
}
```

**Limitation**: Scripts are slower than field-value-factor. For high-QPS applications, scripts incur 10-50% latency penalty.

### Remediation

1. **Pre-compute scores**: Add a `boost_score` field computed offline
2. **Use field_value_factor**: For simple cases (faster)
3. **Cache scripts**: OpenSearch compiles and caches scripts
4. **Consider index-time boosting**: Increase boost during indexing for hot documents

---

## Pitfall 9: SolrCloud Leader Election vs OpenSearch Primary Shard Allocation

### Solr Leader Election

In SolrCloud, one replica per shard is elected "leader":

```
Shard 1: Leader (replicated from)
         Replica 1 (replicated to)
         Replica 2 (replicated to)
```

Writes go to any replica; then forwarded to leader; leader coordinates.

### OpenSearch Primary Shard Allocation

Primary shard handles all writes. Replicas follow via primary term + seq_no:

```
Shard 1: Primary (all writes)
         Replica 1 (follows primary)
         Replica 2 (follows primary)
```

### The Pitfall: Replication Lag

**Solr**: Leader can coordinate, replicas might be out-of-sync; leader handles reads.

**OpenSearch**: Primary writes must be replicated to in-sync replicas before acknowledgment (by default).

**Symptom**: Write latency is higher in OpenSearch (100-500ms) vs Solr (50-100ms).

**Cause**: OpenSearch waits for replicas; Solr doesn't.

### Remediation

If latency is critical, tune consistency level:

```json
PUT /index/_settings
{
  "index": {
    "write.wait_for_active_shards": 1
  }
}
```

`1` = wait for primary only (faster, weaker consistency).
`"all"` = wait for all replicas (slower, stronger consistency).
`2` = default; wait for primary + 1 replica.

---

## Pitfall 10: Monitoring Differences (Admin UI vs Dashboards)

### Solr Admin UI

- Built-in, no external dependencies
- Graphs for cache hit ratio, query QPS, avg latency
- Per-collection dashboard
- Query analyzer tools

### OpenSearch

- No built-in UI (comes with Dashboards, a separate service)
- Requires additional infrastructure
- Plugins required for security, backups, etc.

### Migration Pitfall

**Symptom**: Post-migration, operators lack visibility into cluster performance.

**Remediation**:

1. **Install OpenSearch Dashboards**

```bash
docker run -p 5601:5601 \
  -e OPENSEARCH_HOSTS='["https://opensearch-node:9200"]' \
  opensearchproject/opensearch-dashboards:latest
```

2. **Set up Prometheus metrics**

```yaml
scrape_configs:
  - job_name: opensearch
    static_configs:
      - targets: ['localhost:9200']
    metrics_path: '/_prometheus/metrics'
```

3. **Create Grafana dashboards** for:
   - Cluster health (green/yellow/red)
   - Query latency (p50, p95, p99)
   - Indexing rate (docs/sec)
   - JVM heap usage
   - Shard allocation status

---

## Pitfall 11: Connection Pooling and Client Behavior

### Solr Client Libraries

- SolrJ (Java): Connection pooling built-in, configurable pool size
- Direct HTTP (curl): Stateless, new connection per request

### OpenSearch Client Libraries

- Java client: Connection pooling, but requires explicit HttpHost configuration
- Python (opensearchpy): Connection pool size tunable
- Go (opensearch-go): Connection pool size different than other clients

### Migration Pitfall

**Symptom**: Post-migration, connection exhaustion, "Connection refused" errors.

**Cause**: Default pool sizes differ. Solr might have 10; OpenSearch default 30. If you have 50 concurrent threads, OpenSearch exhausts pools.

### Remediation

**Java OpenSearch client**:

```java
HttpHost[] hosts = {
    new HttpHost("node-1", 9200, "https"),
    new HttpHost("node-2", 9200, "https"),
    new HttpHost("node-3", 9200, "https")
};

RestClientBuilder builder = RestClient.builder(hosts);
builder.setHttpClientConfigCallback(httpClientBuilder -> {
    return httpClientBuilder.setMaxConnPerRoute(100)
                           .setMaxConnTotal(200);
});
RestClient client = builder.build();
```

**Python OpenSearch client**:

```python
from opensearchpy import OpenSearch, helpers

client = OpenSearch(
    hosts=['node-1', 'node-2', 'node-3'],
    http_auth=('user', 'pass'),
    use_ssl=True,
    connection_class=ConnectionPool,
    connection_pool_kwargs={'pool_size': 50}
)
```

---

## Pitfall 12: JVM Tuning Differences

### Solr JVM Defaults

- Heap: Often 8GB for modest deployments
- GC: CMS (Concurrent Mark Sweep) or G1GC
- Young gen focus

### OpenSearch JVM Defaults

- Heap: Often 2GB (conservative)
- GC: G1GC (modern default)
- Larger old gen

### Migration Pitfall

**Symptom**: Out-of-memory errors, GC pauses, slow queries post-migration.

**Cause**: Heap tuned for Solr, not OpenSearch. OpenSearch uses more memory per shard.

### Remediation

Set heap to **50% of available system RAM**, capped at 31GB:

```bash
export ES_JAVA_OPTS="-Xms16g -Xmx16g"
./opensearch/bin/opensearch
```

**GC tuning**:

```bash
# Aggressive young gen for low-latency queries
-XX:NewRatio=1 -XX:SurvivorRatio=6
# Use G1GC with tuned regions
-XX:+UseG1GC -XX:MaxGCPauseMillis=30
```

---

## Pre-Migration Validation Checklist

- [ ] Solr cluster analysis: shards, replicas, data size, avg doc size
- [ ] Query audit: catalog all active queries, their frequency, latency
- [ ] Custom analyzers: List all custom tokenizers/filters, verify OpenSearch equivalents
- [ ] Custom similarity: Document any custom scoring logic, plan porting strategy
- [ ] Atomic updates: Count frequency of partial updates, plan versioning approach
- [ ] Client libraries: Audit all Solr client connections, connection pool sizes
- [ ] Monitoring: Document current alerting, plan new Dashboards/Prometheus setup
- [ ] JVM configuration: Document current heap, GC settings
- [ ] Cluster topology: Document shard/replica layout, plan OpenSearch allocation
- [ ] Failure recovery: Document Solr recovery procedures, plan OpenSearch procedures
- [ ] A/B testing infrastructure: Implement logging of both result sets, comparison metrics
- [ ] Rollback procedures: Document 30-day retention plan, fallback routing logic

---

## Summary: Top 3 Most Common Issues

1. **Relevance differences (BM25 vs TF-IDF)**: Expect 30-40% difference in top-10 results without custom boosting. Plan 2-4 weeks of A/B testing.

2. **Cluster topology sizing**: Minimum nodes required is 2x Solr due to no co-location. Budget infrastructure accordingly.

3. **Connection pool exhaustion**: Default pool sizes are insufficient for high-concurrency workloads. Explicitly configure connection pool sizes.

---

## References

- OpenSearch Similarity Documentation: https://opensearch.org/docs/latest/query-dsl/compound/bool/
- Elasticsearch Migration Guide: https://www.elastic.co/blog/how-to-migrate-from-solr-to-elasticsearch
- BigData Boutique Solr Migration Series: https://bigdataboutique.com/
- Apache Solr vs Elasticsearch: https://solr.apache.org/guide/

