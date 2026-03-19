# AWS Solr to OpenSearch Migration Strategy

**Source**: https://aws.amazon.com/blogs/big-data/migrate-from-apache-solr-to-opensearch/

---

## Executive Summary

The migration from Apache Solr to Amazon OpenSearch is a strategic architectural transition that requires careful planning beyond simple data movement. AWS recommends a "full refactor" approach over lift-and-shift due to fundamental differences in query semantics, configuration paradigms, and operational models. This document synthesizes AWS's recommended best practices for executing a successful migration with minimal risk and downtime.

---

## Migration Strategy: Full Refactor vs Lift-and-Shift

### Why Lift-and-Shift Fails

**Lift-and-shift** (attempting 1:1 porting of Solr configurations) is tempting but problematic:

- **Query syntax incompatibilities**: Solr's DisMax parser has no direct OpenSearch equivalent; queries must be rewritten using Query DSL
- **Configuration format differences**: XML config files cannot be directly translated to OpenSearch mappings and settings
- **Relevance scoring divergence**: Solr uses TF-IDF by default; OpenSearch uses BM25. Direct porting produces different ranking results
- **Operational differences**: Solr's replication model and SolrCloud management differ fundamentally from Elasticsearch/OpenSearch's shard allocation
- **Feature gaps**: Some Solr features (atomic updates, nested document types) have different semantics in OpenSearch

### AWS-Recommended Full Refactor Approach

The full refactor strategy treats OpenSearch as a destination platform requiring intentional design:

1. **Understand source state**: Audit current Solr queries, schema design, and performance requirements
2. **Map conceptually**: Design OpenSearch mappings, index structures, and queries with OpenSearch idioms in mind
3. **Dual-write validation**: Implement dual-write logic to validate query equivalence before cutover
4. **Gradual traffic shift**: Route production traffic gradually from Solr to OpenSearch, monitoring quality metrics
5. **Maintain rollback path**: Keep Solr operational for 30-60 days post-migration to handle edge cases

---

## Dual-Write with Historical Catchup Strategy

### Architecture Pattern

The dual-write pattern is the safest approach for minimizing cutover risk:

```
Application Layer
       ↓
    [Dual-Write Logic]
       ↙        ↘
    Solr      OpenSearch
     ↓            ↓
  (Primary)    (Secondary)

Read Phase 1: Read from Solr, compare results with OpenSearch
Read Phase 2: Shadow read from OpenSearch (no customer impact)
Read Phase 3: Gradual traffic shift to OpenSearch
```

### Implementation Phases

**Phase 1: Dual-Write, Solr-Primary Reads (1-2 weeks)**
- Write every document to both systems
- Read all queries from Solr
- Asynchronously compare search results
- Identify query mapping issues without impacting users
- Use difference detection to build correction matrices

**Phase 2: Shadow Reads (2-4 weeks)**
- Continue dual-write
- Execute every user query against both systems
- Log results but return only Solr results to users
- Monitor latency, relevance, and functional correctness
- Accumulate A/B test metrics

**Phase 3: Gradual Traffic Shift (2-4 weeks)**
- Continue dual-write for consistency
- Route increasing percentages of reads to OpenSearch (5% → 10% → 25% → 50% → 100%)
- Monitor for issues at each boundary
- Maintain canary alerts on unexpected result differences
- Have runbook-prepared rollback procedures

**Phase 4: Historical Data Catchup (parallel to Phase 3)**
- For documents updated before dual-write began, reindex from source of truth
- Use bulk indexing with `refresh_interval=-1` for performance
- After cutover, perform final validation that all documents indexed

### Critical Implementation Details

**Dual-write ordering**: Write to OpenSearch first (fire-and-forget async), then Solr (critical path). This ensures Solr remains source of truth if OpenSearch write fails.

**Timestamp-based auditing**: Include write timestamp in both systems. Query timestamp ranges to identify documents that have diverged.

**Idempotency requirements**: Ensure your dual-write logic handles duplicate writes gracefully. Network failures can cause retries—both systems must handle document re-indexing without data corruption.

---

## Architectural Differences: Deep Dive

### Clustering and Coordination

| Aspect | Solr | OpenSearch |
|--------|------|-----------|
| **Coordination Service** | ZooKeeper (external) | Distributed consensus (embedded) |
| **Cluster State** | Stored in ZooKeeper, synchronized via watches | Stored in cluster state on master nodes, gossip protocol |
| **Node Roles** | All nodes are equal; leaders elected per shard | Master-eligible, data, coordinating nodes (role-based) |
| **Collection Management** | Collections are logical groupings; shards are explicit; replicas specified per shard | Indices contain shards; replicas are replica shards |
| **Configuration Distribution** | ZooKeeper distributes configs to all nodes | Config stored in cluster state, immutable after index creation |
| **Recovery** | Tlog-based recovery from peers | Transaction log based, full resync if needed |

**Migration implication**: You eliminate ZooKeeper dependency, simplifying operations. However, you lose the "external coordination view"—OpenSearch's embedded consensus means cluster state is less observable from outside.

### Configuration Model

**Solr (solrconfig.xml + schema.xml)**:
```xml
<schema>
  <fieldType name="text_general">
    <analyzer>
      <tokenizer class="solr.StandardTokenizerFactory"/>
      <filter class="solr.LowerCaseFilterFactory"/>
    </analyzer>
  </fieldType>
  <field name="title" type="text_general" indexed="true" stored="true"/>
</schema>
```

**OpenSearch (Mappings + Settings)**:
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "standard": {
          "type": "standard",
          "stopwords": "_english_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard"
      }
    }
  }
}
```

**Key differences**:
- Solr configuration is static (requires restart for some changes); OpenSearch allows dynamic setting updates
- Solr schema is explicit per field; OpenSearch uses dynamic templates for unmapped fields
- OpenSearch settings apply to the index; Solr settings apply to the core

### Collection vs Index Terminology

- **Solr**: A "collection" is a logical entity containing multiple shards, each with replicas
- **OpenSearch**: An "index" is a logical entity containing shards, each with replicas

Functionally equivalent, but tooling and APIs differ. Migration requires remapping `collection=X` parameters to `index=X` in all application code.

---

## Query Migration: From Solr Query Parsers to OpenSearch Query DSL

### Solr Standard Query Parser

**Solr query**: `title:solr AND status:published`

**OpenSearch equivalent**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "solr" } },
        { "term": { "status": "published" } }
      ]
    }
  }
}
```

**Mapping rules**:
- `field:value` → `{"match": {"field": "value"}}` (analyzed)
- `field:"exact phrase"` → `{"match_phrase": {"field": "exact phrase"}}`
- `field:[1 TO 100]` → `{"range": {"field": {"gte": 1, "lte": 100}}}`
- `!field:value` or `NOT field:value` → `{"bool": {"must_not": {"term": {"field": "value"}}}}`
- `field:*` (wildcard) → `{"wildcard": {"field": "*"}}` or restructure as filter

### DisMax Query Parser

**Solr DisMax**: Designed for user-facing search with multiple fields and intelligent boosting.

```
q=solr&defType=dismax&qf=title^2 body^1 tags^0.5&mm=2<75%
```

This means:
- Query terms search across `title` (boosted 2x), `body` (boosted 1x), `tags` (boosted 0.5x)
- Minimum match: require 2 terms, or 75% of terms on larger queries

**OpenSearch equivalent** (using `multi_match`):
```json
{
  "query": {
    "multi_match": {
      "query": "solr",
      "fields": ["title^2", "body^1", "tags^0.5"],
      "type": "best_fields",
      "operator": "and",
      "minimum_should_match": "75%"
    }
  }
}
```

**Mapping rules**:
- `qf` parameter (query fields) → `fields` array in `multi_match`
- `tie_breaker` → `tie_breaker` in `multi_match`
- `mm` (minimum match) → `minimum_should_match`
- `bq` (boost query) → `bool` query with `should` clauses + `boost`
- `bf` (boost function) → `function_score` wrapper

### eDisMax Query Parser

**eDisMax** extends DisMax with:
- Per-field slop and phrase boost: `qf=title~2^3` (title with slop 2, boost 3)
- Filter query alternatives: `fq` become filter context in OpenSearch
- Quoted phrase handling with implicit field application

**OpenSearch approach**: Use `bool` query combining `multi_match` with nested `bool` clauses for complex field-specific logic.

Solr eDisMax:
```
q=solr guide&defType=edismax&qf=title~2^3 body&bq=author:expert^5
```

OpenSearch equivalent:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "solr guide",
            "fields": ["title^3", "body"],
            "type": "phrase",
            "slop": 2
          }
        }
      ],
      "should": [
        {
          "term": {
            "author": {
              "value": "expert",
              "boost": 5
            }
          }
        }
      ]
    }
  }
}
```

### Filter Queries (fq)

**Solr** separates query logic from filtering:
```
q=title:solr&fq=status:published&fq=date:[NOW-30DAYS TO NOW]
```

**OpenSearch** uses `bool` filter context (which is cached and faster):
```json
{
  "query": {
    "bool": {
      "must": { "match": { "title": "solr" } },
      "filter": [
        { "term": { "status": "published" } },
        { "range": { "date": { "gte": "now-30d" } } }
      ]
    }
  }
}
```

**Critical difference**: In OpenSearch, filters in the `filter` context are cached automatically and don't affect relevance scoring. In Solr, `fq` is also efficient but the semantics are slightly different (it's a separate query evaluation phase).

---

## Schema Migration: schema.xml to Index Mappings

### Field Type Mappings

| Solr Field Type | OpenSearch Type | Notes |
|-----------------|-----------------|-------|
| `text_general` | `text` with standard analyzer | Default text analysis |
| `string` | `keyword` | Exact matching, no analysis |
| `int` | `integer` | 32-bit integer |
| `long` | `long` | 64-bit integer |
| `float` | `float` | IEEE 754 single precision |
| `double` | `double` | IEEE 754 double precision |
| `boolean` | `boolean` | True/false values |
| `pdate` | `date` | ISO 8601 or milliseconds since epoch |
| `text_en` | `text` with English analyzer | Language-specific analysis |
| `location` | `geo_point` | Latitude/longitude |
| `nested type` | `nested` | Preserve array structure |

### Analyzer Chain Translation

**Solr**:
```xml
<fieldType name="text_custom">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.StopFilterFactory" words="english.txt"/>
    <filter class="solr.PorterStemFilterFactory"/>
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <!-- No stemming at query time -->
  </analyzer>
</fieldType>
```

**OpenSearch**:
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "text_custom": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "porter_stem"]
        },
        "text_custom_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "my_field": {
        "type": "text",
        "analyzer": "text_custom",
        "search_analyzer": "text_custom_query"
      }
    }
  }
}
```

**Key differences**:
- Solr's `type="index"` and `type="query"` analyzers → OpenSearch's `analyzer` and `search_analyzer`
- Solr's `char_filter` (preprocessor before tokenizer) is less common; OpenSearch uses `char_filter` in analysis settings
- Solr's `copyField` → OpenSearch's `copy_to` (similar semantics, different syntax)

### Dynamic Fields and Templates

**Solr** (wildcard field definitions):
```xml
<dynamicField name="*_s" type="string"/>
<dynamicField name="*_t" type="text_general"/>
<dynamicField name="*_i" type="int"/>
```

**OpenSearch** (dynamic templates):
```json
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings": {
          "match_mapping_type": "string",
          "match": "*_s",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "texts": {
          "match": "*_t",
          "mapping": {
            "type": "text"
          }
        }
      }
    ]
  }
}
```

### CopyField Translation

**Solr**:
```xml
<copyField source="title" dest="search_text"/>
<copyField source="body" dest="search_text"/>
```

**OpenSearch**:
```json
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "copy_to": "search_text"
      },
      "body": {
        "type": "text",
        "copy_to": "search_text"
      },
      "search_text": {
        "type": "text"
      }
    }
  }
}
```

---

## Data Migration Approaches

### Approach 1: Reindex from Source of Truth

**Best for**: When you maintain a database that originally populated Solr.

**Process**:
1. Point reindexing scripts at OpenSearch instead of Solr
2. Perform full reindex in parallel with running Solr
3. Use `refresh_interval=-1` during bulk indexing (disable refresh)
4. After bulk indexing, set `refresh_interval: "1s"` and force refresh

**Advantages**:
- Guarantees data consistency with source of truth
- Allows transformation/cleanup during reindexing
- Can optimize for OpenSearch field types during migration

**Disadvantages**:
- Requires maintaining source-of-truth database/system
- Longer migration window (reindex time can be substantial)

### Approach 2: Logstash

**Best for**: When Solr is the source of truth and you want to transform data in flight.

**Pipeline**:
```
Solr (curl/Solrj) → Logstash → OpenSearch
```

**Logstash configuration example**:
```
input {
  http_poller {
    urls => { "solr" => "http://localhost:8983/solr/mycollection/select?q=*:*&rows=1000&wt=json" }
    request_timeout => 60
    interval => 60
  }
}

filter {
  split { field => "[response][docs]" }
  mutate { rename => { "[response][docs]" => "[@metadata][doc]" } }
  json { source => "[@metadata][doc]" }
}

output {
  opensearch {
    hosts => ["localhost:9200"]
    index => "mycollection"
    document_id => "%{id}"
  }
}
```

**Advantages**:
- Can transform field names, remove fields, enrich data
- Handles schema differences on the fly
- Can add data quality checks/validation

**Disadvantages**:
- Overhead of Logstash processing (typically 5-10K docs/sec throughput)
- For large datasets (100GB+), may take days
- Requires Logstash infrastructure

### Approach 3: Custom ETL

**Best for**: Complex transformations, multi-source aggregation, or very large datasets.

**Considerations**:
- Implement in Scala/Java/Go for performance (500K+ docs/sec with bulk API)
- Use OpenSearch bulk API with optimal batch sizing (500-1000 documents, 5-50MB)
- Implement retry logic with exponential backoff
- Monitor throughput and adjust parallelism

**Pseudo-code**:
```python
from opensearchpy import OpenSearch, helpers

es = OpenSearch([{"host": "localhost", "port": 9200}])

def solr_to_opensearch(solr_client, batch_size=1000):
    offset = 0
    while True:
        docs = solr_client.query(q="*:*", offset=offset, limit=batch_size)
        if not docs.results:
            break

        transformed = transform_docs(docs.results)
        helpers.bulk(es, transformed, index="mycollection", chunk_size=500)
        offset += batch_size

def transform_docs(docs):
    for doc in docs:
        # Map field types, remove unnecessary fields
        yield {
            "_id": doc["id"],
            "_source": {
                "title": doc.get("title", ""),
                "tags": doc.get("tags", []),
                # Solr nested docs become OpenSearch nested type
            }
        }
```

---

## AB Testing and Gradual Traffic Shifting

### Pre-Cutover AB Testing

**Setup**:
1. Route 5% of production queries to OpenSearch in "shadow" mode
2. Log result sets from both systems
3. Use relevance metrics to compare quality

**Key metrics to monitor**:
- **Query latency**: p50, p95, p99 for Solr vs OpenSearch
- **Hit rate**: Do queries return at least some results in both systems?
- **Top-10 overlap**: Do top 10 results overlap sufficiently (80%+ overlap is target)?
- **Relevance**: Use normalized discounted cumulative gain (NDCG) if you have click-through data

### Traffic Shifting Strategy

**Phase 1 (5%)**:
- Route 5% of queries to OpenSearch
- Monitor for any errors, timeouts, or anomalies
- Duration: 24-48 hours minimum

**Phase 2 (10%)**:
- Gradually increase to 10%
- Verify no issues at scale
- Duration: 24-48 hours

**Phase 3 (25%)**:
- Increase to 25%
- Many issues surface here; prepare for hotfixes
- Duration: 1 week

**Phase 4 (50%)**:
- Send half traffic to OpenSearch
- Run in true parallel; compare all results
- Duration: 1 week

**Phase 5 (100%)**:
- Full cutover
- Keep Solr operational for 30 days as fallback
- Gradual cache warming in OpenSearch

### Rollback Procedures

**Automatic rollback triggers**:
```
- Error rate > 0.1% on OpenSearch queries
- p99 latency > 2x Solr baseline
- Result set size differs > 10% from Solr
- More than N anomalies detected in query comparison
```

**Manual rollback**: Have a "flip switch" in your client that redirects all queries to Solr within seconds.

**30-day retention**: Keep Solr indices and data for 30 days post-migration. If critical bugs emerge, you can:
1. Disable OpenSearch reads
2. Redirect traffic to Solr
3. Debug OpenSearch issues
4. Attempt re-cutover

---

## Summary: AWS Migration Checklist

- [ ] Audit Solr configuration, schema, and active queries
- [ ] Design OpenSearch mappings and index settings
- [ ] Implement dual-write logic with async queue
- [ ] Map Solr queries to OpenSearch Query DSL
- [ ] Set up A/B testing infrastructure
- [ ] Reindex historical data to OpenSearch
- [ ] Run shadow read phase (7-14 days)
- [ ] Execute gradual traffic shift (5% → 10% → 25% → 50% → 100%)
- [ ] Monitor key metrics (latency, error rate, relevance)
- [ ] Prepare and test rollback procedures
- [ ] Complete cutover and validate
- [ ] Maintain Solr for 30+ days as safety net
- [ ] Decommission Solr after confidence period
