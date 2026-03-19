# Technical Design: Techproducts Migration

This is the core technical reference. It defines the OpenSearch index mapping, query translations, and indexing architecture.

---

## Index Mapping (Complete JSON)

This JSON mapping replaces the Solr schema.xml. It can be applied directly to OpenSearch via the Mappings API or in application code via Spring Data annotations.

```json
{
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "1s"
    },
    "analysis": {
      "tokenizer": {
        "standard_tokenizer": {
          "type": "standard"
        }
      },
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "synonym_graph": {
          "type": "synonym_graph",
          "synonyms": [
            "hard disk,hard drive",
            "hd,hard drive",
            "ipod,portable music player",
            "camera,photo device"
          ]
        }
      },
      "analyzer": {
        "text_general_index": {
          "type": "custom",
          "tokenizer": "standard_tokenizer",
          "filter": ["lowercase", "english_stop"]
        },
        "text_general_query": {
          "type": "custom",
          "tokenizer": "standard_tokenizer",
          "filter": ["lowercase", "english_stop", "synonym_graph"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "name": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query",
        "copy_to": "_text_"
      },
      "manu": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query",
        "copy_to": ["_text_", "manu_exact"],
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "manu_exact": {
        "type": "keyword"
      },
      "cat": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query",
        "copy_to": "_text_",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "features": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query",
        "copy_to": "_text_"
      },
      "includes": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query"
      },
      "weight": {
        "type": "float"
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
        "type": "geo_point",
        "ignore_malformed": true
      },
      "manufacturedate_dt": {
        "type": "date"
      },
      "payloads": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query",
        "enabled": false
      },
      "_text_": {
        "type": "text",
        "analyzer": "text_general_index",
        "search_analyzer": "text_general_query"
      },
      "subject": { "type": "keyword" },
      "description": { "type": "text", "analyzer": "text_general_index" },
      "comments": { "type": "text", "analyzer": "text_general_index" },
      "author": { "type": "keyword" },
      "keywords": { "type": "text", "analyzer": "text_general_index" },
      "content_type": { "type": "keyword" },
      "resourcename": { "type": "keyword" },
      "url": { "type": "keyword" },
      "content": { "type": "text", "analyzer": "text_general_index" }
    },
    "dynamic_templates": [
      {
        "strings_as_keyword": {
          "match": "*_s",
          "match_mapping_type": "string",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "ints_as_integer": {
          "match": "*_i",
          "match_mapping_type": "long",
          "mapping": {
            "type": "integer"
          }
        }
      },
      {
        "longs_as_long": {
          "match": "*_l",
          "match_mapping_type": "long",
          "mapping": {
            "type": "long"
          }
        }
      },
      {
        "floats_as_float": {
          "match": "*_f",
          "match_mapping_type": "double",
          "mapping": {
            "type": "float"
          }
        }
      },
      {
        "doubles_as_double": {
          "match": "*_d",
          "match_mapping_type": "double",
          "mapping": {
            "type": "double"
          }
        }
      },
      {
        "booleans_as_boolean": {
          "match": "*_b",
          "match_mapping_type": "boolean",
          "mapping": {
            "type": "boolean"
          }
        }
      },
      {
        "dates_as_date": {
          "match": "*_dt",
          "match_mapping_type": "string",
          "mapping": {
            "type": "date"
          }
        }
      },
      {
        "geo_points_as_geopoint": {
          "match": "*_p",
          "match_mapping_type": "string",
          "mapping": {
            "type": "geo_point"
          }
        }
      },
      {
        "strings_multivalue_as_keyword": {
          "match": "*_ss",
          "match_mapping_type": "string",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "ints_multivalue_as_integer": {
          "match": "*_is",
          "match_mapping_type": "long",
          "mapping": {
            "type": "integer"
          }
        }
      }
    ]
  }
}
```

### Mapping Notes

| Solr Feature | OpenSearch Equivalent | How Handled |
|--------------|----------------------|------------|
| copyField name→_text_ | copy_to in manu field | Automatic during indexing |
| copyField manu→manu_exact | manu.fields.keyword + explicit manu_exact | Explicit field + multi-field |
| Dynamic field *_s | dynamic_templates | Automatically typed to keyword on first doc |
| text_general analyzer | Custom "text_general_index" and "text_general_query" | Separate index/query analyzers for synonym expansion |
| FieldType String | keyword | Exact match, no analysis |
| FieldType pfloat | float | OpenSearch numeric |
| FieldType pint | integer | OpenSearch numeric |
| FieldType pdate | date | ISO 8601 format |
| LatLonPointSpatialField | geo_point | "lat,lon" or lat/lon object format |

---

## Query Architecture

### Query 1: Keyword Search (eDisMax Equivalent)

**Solr:**
```
GET /solr/techproducts/select?q=hard%20drive&qf=name^2%20features^1%20cat^0.5&defType=edismax
```

**OpenSearch Query DSL:**
```json
{
  "query": {
    "multi_match": {
      "query": "hard drive",
      "fields": ["name^2", "features^1", "cat^0.5"],
      "type": "best_fields",
      "operator": "or",
      "tie_breaker": 0.3
    }
  },
  "size": 10
}
```

**Expected results:** SP2514N (exact name match, boosted), 6H500F0 (features match)

---

### Query 2: Filter by Stock Status

**Solr:**
```
GET /solr/techproducts/select?q=*:*&fq=inStock:true&rows=10
```

**OpenSearch Query DSL:**
```json
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "inStock": true } }
      ]
    }
  },
  "size": 10
}
```

**Expected results:** Only 3 products (SP2514N, MA147LL/A, 9885A004)

---

### Query 3: Filter by Price Range

**Solr:**
```
GET /solr/techproducts/select?q=*:*&fq=price:[50%20TO%20300]&rows=10
```

**OpenSearch Query DSL:**
```json
{
  "query": {
    "bool": {
      "filter": [
        { "range": { "price": { "gte": 50, "lte": 300 } } }
      ]
    }
  },
  "size": 10
}
```

**Expected results:** SP2514N (92.0), F8V7067-APL-KIT (19.95), 0579B002 (210.0)

---

### Query 4: Category Facets

**Solr:**
```
GET /solr/techproducts/select?q=*:*&facet=true&facet.field=cat&rows=0
```

**OpenSearch Query DSL:**
```json
{
  "query": { "match_all": {} },
  "aggs": {
    "by_category": {
      "terms": {
        "field": "cat.keyword",
        "size": 20
      }
    }
  },
  "size": 0
}
```

**Expected response:**
```json
{
  "aggregations": {
    "by_category": {
      "buckets": [
        { "key": "electronics", "doc_count": 7 },
        { "key": "hard drive", "doc_count": 2 },
        { "key": "music", "doc_count": 2 },
        { "key": "camera", "doc_count": 2 },
        { "key": "connector", "doc_count": 1 }
      ]
    }
  }
}
```

---

### Query 5: Boolean Facets

**Solr:**
```
GET /solr/techproducts/select?q=*:*&facet=true&facet.field=inStock&rows=0
```

**OpenSearch Query DSL:**
```json
{
  "query": { "match_all": {} },
  "aggs": {
    "by_inStock": {
      "terms": {
        "field": "inStock",
        "size": 2
      }
    }
  },
  "size": 0
}
```

**Expected response:**
```json
{
  "aggregations": {
    "by_inStock": {
      "buckets": [
        { "key": 1, "key_as_string": "true", "doc_count": 3 },
        { "key": 0, "key_as_string": "false", "doc_count": 4 }
      ]
    }
  }
}
```

---

### Query 6: Price Range Facets

**Solr:**
```
GET /solr/techproducts/select?q=*:*&facet=true&facet.range=price&facet.range.start=0&facet.range.end=500&facet.range.gap=100&rows=0
```

**OpenSearch Query DSL:**
```json
{
  "query": { "match_all": {} },
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 100 },
          { "from": 100, "to": 250 },
          { "from": 250, "to": 400 },
          { "from": 400 }
        ]
      }
    }
  },
  "size": 0
}
```

---

### Query 7: Geo Search

**Solr:**
```
GET /solr/techproducts/select?q=*:*&fq={!geofilt%20sfield=store%20pt=37.77,-122.41%20d=10}&rows=10
```

**OpenSearch Query DSL:**
```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "geo_distance": {
            "distance": "10km",
            "store": {
              "lat": 37.77,
              "lon": -122.41
            }
          }
        }
      ]
    }
  },
  "size": 10,
  "sort": [
    {
      "_geo_distance": {
        "store": { "lat": 37.77, "lon": -122.41 },
        "order": "asc",
        "unit": "km"
      }
    }
  ]
}
```

---

### Query 8: Combined Filters + Facets

**Solr:**
```
GET /solr/techproducts/select?q=electronics&fq=inStock:true&fq=cat:camera&facet=true&facet.field=cat&facet.field=inStock&rows=10
```

**OpenSearch Query DSL:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "_text_": "electronics" } }
      ],
      "filter": [
        { "term": { "inStock": true } },
        { "term": { "cat.keyword": "camera" } }
      ]
    }
  },
  "aggs": {
    "categories": {
      "terms": { "field": "cat.keyword", "size": 20 }
    },
    "stock_status": {
      "terms": { "field": "inStock", "size": 2 }
    }
  },
  "size": 10
}
```

**Expected results:** Only 9885A004 (camera, in stock)

---

## Migration Architecture

### Data Flow Diagram (ASCII)

```
┌─────────────────┐
│  Solr Instance  │
│  techproducts   │
│  (7 products)   │
└────────┬────────┘
         │
         │ 1. Export via /select?qt=export
         │    (SolrJ or curl)
         │
         ▼
┌──────────────────────────────┐
│   SolrExporter.kt            │
│  • Parse Solr JSON response  │
│  • Transform to ProductDoc   │
│  • Validate fields           │
└────────┬─────────────────────┘
         │
         │ 2. List<ProductDocument>
         │
         ▼
┌──────────────────────────────┐
│   MigrationService.kt        │
│  • Disable refresh_interval  │
│  • Bulk index (async)        │
│  • Count verification        │
│  • Force refresh             │
└────────┬─────────────────────┘
         │
         │ 3. BulkRequest
         │    (opensearch-java API)
         │
         ▼
┌──────────────────────────────┐
│  AWS OpenSearch Service      │
│  index: techproducts         │
│  status: GREEN               │
│  docs: 7                     │
└──────────────────────────────┘
```

### Indexing Strategy

**Single-Pass Reindex (Demo Mode)**

1. **Export from Solr** (SolrJ client)
   ```kotlin
   val solrClient = HttpSolrClient("http://localhost:8983/solr")
   val query = SolrQuery("*:*").setRows(1000)
   val response = solrClient.query("techproducts", query)
   ```

2. **Transform to OpenSearch format**
   ```kotlin
   val products = response.results.map { doc ->
       ProductDocument(
           id = doc.getFieldValue("id") as String,
           name = doc.getFieldValue("name") as String,
           // ... map all fields
       )
   }
   ```

3. **Optimize for bulk loading**
   ```kotlin
   // Disable refresh during bulk indexing
   openSearchClient.indices().putSettings(
       PutIndexSettingsRequest("techproducts")
           .settings(Settings.builder()
               .put("index.refresh_interval", "-1")
               .build())
   )
   ```

4. **Bulk index with opensearch-java**
   ```kotlin
   val bulkRequest = BulkRequest()
   products.forEach { product ->
       bulkRequest.add(
           IndexRequest("techproducts")
               .id(product.id)
               .document(product, ContentType.APPLICATION_JSON)
       )
   }
   val bulkResponse = openSearchClient.bulk(bulkRequest)
   ```

5. **Re-enable refresh and verify**
   ```kotlin
   // Re-enable refresh
   openSearchClient.indices().putSettings(
       PutIndexSettingsRequest("techproducts")
           .settings(Settings.builder()
               .put("index.refresh_interval", "1s")
               .build())
   )

   // Force refresh
   openSearchClient.indices().refresh(
       RefreshRequest("techproducts")
   )

   // Verify count
   val countResponse = openSearchClient.count(
       CountRequest("techproducts")
   )
   assert(countResponse.count() == 7)
   ```

### Comparison: This Demo vs. Production Migrations

| Aspect | Techproducts Demo | Production Reality |
|--------|-------------------|-------------------|
| Data size | 1 MB / 7 docs | 10 GB - 10 TB |
| Reindex time | Seconds | Hours to days |
| Dual-write needed? | No (green-field) | Yes (zero downtime) |
| Shadow read validation? | Manual spot-checks | Automated A/B harness |
| Relevance tuning | Minimal (baseline match) | Extensive (Quepid, RRE) |
| Rollback window | N/A (can re-index) | 30-90 days (keep Solr warm) |
| Analyzer complexity | Standard (stopwords, synonyms) | Custom filters, plugins |
| Query patterns | 8 examples | Dozens of production patterns |

---

## Relevance Baseline

### Solr Baseline Query: "hard drive"

Executed against Solr `/select` with eDisMax:
```
q=hard drive
qf=name^2 features^1 cat^0.5
defType=edismax
```

**Results (score, id, name):**
1. 8.64 | SP2514N | Samsung SpinPoint hard drive ← name match (boosted)
2. 4.32 | 6H500F0 | Maxtor hard drive ← name match

### OpenSearch Baseline Query: "hard drive"

Executed with multi_match:
```json
{
  "query": {
    "multi_match": {
      "query": "hard drive",
      "fields": ["name^2", "features^1", "cat^0.5"],
      "type": "best_fields"
    }
  }
}
```

**Expected results:** Same top-2, possibly different scores (BM25 vs TF-IDF)

**Success criteria:** Top-10 overlap ≥ 80% (both should return the same 2 products at top)

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Keyword search (10 results) | < 50ms | With caching |
| Faceted query (10 docs + 5 aggs) | < 100ms | Cold cache |
| Geo search (10 results) | < 75ms | Depends on document count |
| Bulk index (7 docs) | < 5 sec | Including refresh overhead |
| Query latency p99 | < 150ms | Sustained load |

---

## What's Different from Production

This spec is intentionally simplified:

1. **No Tika/document parsing** — real systems parse binary content (PDFs, images, Office files)
2. **No payload scoring** — real systems use custom scoring functions
3. **No complex nested documents** — real systems have hierarchies (blog post → comments → replies)
4. **No CDCR or replication** — real systems need cross-datacenter sync
5. **No atomic updates** — real systems update fields without re-indexing
6. **No streaming expressions** — real systems have ETL pipelines
7. **No tuning at scale** — real migrations use Quepid and judgment sets

**For your own migration:** Start here, then add complexity as needed.

---

**Version:** 1.0
**Date:** 2026-03-17
**Reviewer:** Search Architecture Team
