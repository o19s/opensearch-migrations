╔═════════════════════════════════════════════════════════════════════════╗
║  ⚡ EXPRESS MODE — GENERATED WITH ASSUMPTIONS ⚡                    ║
║                                                                      ║
║  This spec was generated in express ("YOLO") mode. The advisor made  ║
║  its best expert guesses where information was missing. Every        ║
║  assumption is marked [ASSUMED:...] for your review.                ║
║                                                                      ║
║  DO NOT execute this migration without reviewing assumptions.        ║
╚═════════════════════════════════════════════════════════════════════════╝

### a. Field Mappings
```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "name": {
        "type": "text",
        "analyzer": "standard"
      },
      "features": {
        "type": "text",
        "analyzer": "standard"
      },
      "cat": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "price": {
        "type": "float"
      },
      "popularity": {
        "type": "integer"
      },
      "inStock": {
        "type": "boolean"
      },
      "store": {
        "type": "geo_point"
      },
      "_text_": {
        "type": "text",
        "analyzer": "standard"
      }
    }
  }
}
```
[ASSUMED: `text_general` maps to `text` with `standard` analyzer.]

### b. Behavioral Incompatibilities
1. **HIGH**: BM25 (OpenSearch default) scores differently than TF-IDF (Solr legacy). This will change relevance rankings.
2. [ASSUMED: No custom scoring functions or plugins are used.]

### c. Query Translations
- **eDisMax keyword search** → **multi_match with field boosts**
  ```json
  {
    "query": {
      "multi_match": {
        "query": "search term",
        "fields": ["name^2", "features", "cat"]
      }
    }
  }
  ```
- **fq (filter query)** → **bool.filter clause**
  ```json
  {
    "query": {
      "bool": {
        "filter": [
          { "term": { "inStock": true } }
        ]
      }
    }
  }
  ```
- **facet.field** → **terms aggregation (requires.keyword sub-field)**
  ```json
  {
    "aggs": {
      "categories": {
        "terms": {
          "field": "cat.keyword"
        }
      }
    }
  }
  ```

### d. Client Migration
Replace SolrJ with opensearch-java:
```xml
<!-- Maven -->
<dependency>
  <groupId>software.amazon.opensearch</groupId>
  <artifactId>opensearch-java</artifactId>
  <version>1.0.0</version>
</dependency>
```
[ASSUMED: Latest stable version of opensearch-java is used.]

### e. Infrastructure Sizing
- **Node Count**: 3 data nodes, 1 dedicated master node
- **Instance Type**: `r5.large.search` for data nodes, `t3.medium` for master node
- **Shard/Replica Config**: 3 primary shards, 2 replicas each
[ASSUMED: Similar performance characteristics between Solr and OpenSearch.]

### f. Phased Timeline
- **Week 1**: Schema translation and OpenSearch cluster setup
- **Week 2**: Client code refactoring (SolrJ → opensearch-java)
- **Week 3**: Dual-write validation and performance testing
- **Week 4**: Cutover and decommissioning of Solr
[ASSUMED: 4-week timeline is feasible based on provided load and index size.]

### g. Assumptions Summary
1. [ASSUMED: `text_general` maps to `text` with `standard` analyzer.] - MEDIUM risk
2. [ASSUMED: No custom scoring functions or plugins are used.] - LOW risk
3. [ASSUMED: Latest stable version of opensearch-java is used.] - LOW risk
4. [ASSUMED: Similar performance characteristics between Solr and OpenSearch.] - MEDIUM risk
5. [ASSUMED: 4-week timeline is feasible.] - MEDIUM risk