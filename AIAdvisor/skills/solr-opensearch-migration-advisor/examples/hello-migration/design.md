# Technical Design: `hello` Migration

[ASSUMED: All field names are placeholders derived from common content-search patterns.
Replace with your actual schema.xml field names before executing.]

## Assumed Solr Schema

This design assumes the following `schema.xml` field definitions. Verify each against
your actual schema — field names and types are the most important things to get right.

```xml
<!-- [ASSUMED: Inferred from common content-search Solr collections] -->
<field name="id"            type="string"       indexed="true"  stored="true"  required="true"/>
<field name="title"         type="text_general" indexed="true"  stored="true"/>
<field name="body"          type="text_general" indexed="true"  stored="true"/>
<field name="category"      type="string"       indexed="true"  stored="true"/>
<field name="author"        type="string"       indexed="true"  stored="true"/>
<field name="publishedDate" type="pdate"        indexed="true"  stored="true"/>
<field name="tags"          type="string"       indexed="true"  stored="true" multiValued="true"/>
<field name="score"         type="pfloat"       indexed="true"  stored="true"/>
<field name="_text_"        type="text_general" indexed="true"  stored="false" multiValued="true"/>

<copyField source="title"  dest="_text_"/>
<copyField source="body"   dest="_text_"/>
<copyField source="author" dest="_text_"/>

<dynamicField name="*_s"  type="string"  indexed="true" stored="true"/>
<dynamicField name="*_dt" type="pdate"   indexed="true" stored="true"/>
```

---

## Index Mapping (OpenSearch)

Save this as `src/main/resources/opensearch/hello-mapping.json`.
Create the index with:
```bash
curl -X PUT "https://<endpoint>/hello" \
  -H "Content-Type: application/json" \
  --aws-sigv4 "aws:amz:us-east-1:es" \
  -d @hello-mapping.json
```

```json
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "refresh_interval": "1s",
    "analysis": {
      "analyzer": {
        "hello_text": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "english_stemmer"]
        },
        "hello_text_search": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "english_stemmer"]
        }
      },
      "filter": {
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        }
      }
    }
  },
  "mappings": {
    "dynamic": "strict",
    "dynamic_templates": [
      {
        "strings_as_keyword": {
          "match": "*_s",
          "mapping": { "type": "keyword" }
        }
      },
      {
        "dates_as_date": {
          "match": "*_dt",
          "mapping": { "type": "date", "format": "strict_date_optional_time" }
        }
      }
    ],
    "properties": {
      "id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "hello_text",
        "search_analyzer": "hello_text_search",
        "copy_to": "_text_",
        "fields": {
          "keyword": { "type": "keyword", "ignore_above": 256 }
        }
      },
      "body": {
        "type": "text",
        "analyzer": "hello_text",
        "search_analyzer": "hello_text_search",
        "copy_to": "_text_"
      },
      "category": {
        "type": "keyword"
      },
      "author": {
        "type": "keyword",
        "copy_to": "_text_"
      },
      "publishedDate": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "tags": {
        "type": "keyword"
      },
      "score": {
        "type": "float"
      },
      "_text_": {
        "type": "text",
        "analyzer": "hello_text"
      }
    }
  }
}
```

### Mapping Notes

| Decision | Rationale |
|----------|-----------|
| `"dynamic": "strict"` | Prevents dynamic mapping landmines; new fields must be explicit |
| `title` has `.keyword` sub-field | Enables exact-match sort and aggregation on title if needed |
| `hello_text` analyzer | Standard + lowercase + stop + english stemmer = Solr `text_general` equivalent [ASSUMED] |
| Separate index/search analyzers | Mirrors Solr `<analyzer type="index">` / `<analyzer type="query">` split |
| `copy_to: "_text_"` | Direct equivalent of Solr `<copyField>` directives |
| `author` as `keyword` | [ASSUMED: used for filtering/faceting, not full-text] — change to `text` if searched |

---

## Query Translations

### Q1: Basic Keyword Search (eDisMax → multi_match)

```
Solr:  q=knowledge+management&qt=dismax&qf=title^3 body^1&mm=2<75%&pf=title^5&ps=2
```

```json
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "knowledge management",
            "fields": ["title^3", "body^1"],
            "type": "best_fields",
            "minimum_should_match": "75%"
          }
        },
        {
          "match_phrase": {
            "title": {
              "query": "knowledge management",
              "boost": 5,
              "slop": 2
            }
          }
        }
      ],
      "minimum_should_match": 1
    }
  }
}
```

**Relevance note:** The `mm=2<75%` rule (below 2 terms: all required; ≥2 terms: 75% required)
is approximated as `"minimum_should_match": "75%"` in OpenSearch. For single-term queries this
is identical; for multi-term it's slightly different. [ASSUMED: acceptable delta]

---

### Q2: Category Filter (fq → bool.filter)

```
Solr:  q=*:*&fq=category:technology&rows=20
```

```json
{
  "query": {
    "bool": {
      "must": { "match_all": {} },
      "filter": [
        { "term": { "category": "technology" } }
      ]
    }
  },
  "size": 20
}
```

**Note:** `bool.filter` context means no scoring contribution from the filter — same as
Solr's `fq` behavior. The filter is also cache-eligible, matching Solr's filter cache.

---

### Q3: Keyword + Category Filter

```
Solr:  q=machine+learning&qf=title^3 body^1&fq=category:technology
```

```json
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "machine learning",
            "fields": ["title^3", "body^1"],
            "type": "best_fields",
            "minimum_should_match": "75%"
          }
        }
      ],
      "filter": [
        { "term": { "category": "technology" } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

---

### Q4: Date Range Filter

```
Solr:  fq=publishedDate:[2025-01-01T00:00:00Z TO 2025-12-31T23:59:59Z]
```

```json
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "publishedDate": {
              "gte": "2025-01-01T00:00:00Z",
              "lte": "2025-12-31T23:59:59Z"
            }
          }
        }
      ]
    }
  }
}
```

---

### Q5: Category Facets

```
Solr:  facet=true&facet.field=category&facet.limit=20&facet.mincount=1
```

```json
{
  "query": { "match_all": {} },
  "aggs": {
    "by_category": {
      "terms": {
        "field": "category",
        "size": 20,
        "min_doc_count": 1
      }
    }
  },
  "size": 0
}
```

**Response shape difference:** Solr returns `facet_counts.facet_fields.category` as a flat
array `["tech", 42, "science", 31, ...]`. OpenSearch returns
`aggregations.by_category.buckets: [{key: "tech", doc_count: 42}, ...]`. The client must
be updated to read the new shape.

---

### Q6: Combined Search + Facet (typical production query)

```
Solr:  q=climate+change&qf=title^3 body^1&mm=75%
       &facet=true&facet.field=category
       &fq=publishedDate:[2024-01-01T00:00:00Z TO *]
       &rows=20&start=0
```

```json
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "climate change",
            "fields": ["title^3", "body^1"],
            "type": "best_fields",
            "minimum_should_match": "75%"
          }
        }
      ],
      "filter": [
        {
          "range": {
            "publishedDate": { "gte": "2024-01-01T00:00:00Z" }
          }
        }
      ],
      "minimum_should_match": 1
    }
  },
  "aggs": {
    "by_category": {
      "terms": { "field": "category", "size": 20 }
    }
  },
  "from": 0,
  "size": 20
}
```

---

### Q7: Sort by Date (replacing Solr sort parameter)

```
Solr:  sort=publishedDate desc
```

```json
{
  "sort": [
    { "publishedDate": { "order": "desc" } },
    { "_score": { "order": "desc" } }
  ]
}
```

**Note:** Always include a tiebreaker (`_score` or `_id`) after any date sort to ensure
stable pagination with `search_after`.

---

### Q8: Deep Pagination (search_after, replaces start/rows > 10K)

```
Solr:  start=10000&rows=20&sort=publishedDate desc,id asc
```

```json
{
  "size": 20,
  "sort": [
    { "publishedDate": { "order": "desc" } },
    { "id": { "order": "asc" } }
  ],
  "search_after": ["2024-06-15T10:30:00Z", "doc-00009999"]
}
```

**Migration action:** Identify all pagination call sites that use `start > 0` and add
a guard: return HTTP 400 if `from + size > 10000` with message directing to `search_after`.

---

## Indexing Architecture

```
                ┌─────────────────────┐
                │   Application       │
                │  (Spring Boot 3.x)  │
                └────────┬────────────┘
                         │
          ┌──────────────▼──────────────────┐
          │      DualWriteIndexService       │
          │  (Phase 3: migration.dual-write) │
          └───────┬─────────────────┬────────┘
                  │                 │
         ┌────────▼───┐     ┌───────▼────────┐
         │  SolrClient │     │ HelloIndexSvc  │
         │  (retiring) │     │  (opensearch)  │
         └────────────┘     └────────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │  AWS OpenSearch Service │
                        │  hello index (2 shards) │
                        └───────────────────────┘
```

### Bulk Reindex Strategy

Run before dual-write begins (Phase 3, Step 1):

```kotlin
fun reindexAll() {
    val log = LoggerFactory.getLogger(javaClass)
    // Disable refresh for bulk speed
    client.indices().putSettings { s ->
        s.index("hello")
         .settings { t -> t.refreshInterval(Time.of { tt -> tt.time("-1") }) }
    }

    var cursor = "*"
    var total = 0

    do {
        val solrResponse = solrClient.query("hello",
            SolrQuery("*:*").also {
                it.set("cursorMark", cursor)
                it.setSort("id", SolrQuery.ORDER.asc)
                it.setRows(500)  // [ASSUMED: batch size]
            }
        )

        val docs = solrResponse.results.map { it.toHelloDocument() }
        if (docs.isNotEmpty()) {
            helloIndexService.bulkIndex(docs)
            total += docs.size
            log.info("Reindexed $total documents...")
        }

        cursor = solrResponse.nextCursorMark
    } while (cursor != solrResponse.results.cursorMark)

    // Re-enable refresh
    client.indices().putSettings { s ->
        s.index("hello")
         .settings { t -> t.refreshInterval(Time.of { tt -> tt.time("1s") }) }
    }

    // Force final refresh
    client.indices().refresh { r -> r.index("hello") }
    log.info("Reindex complete: $total total documents")
}
```

**Why cursor-based pagination:** Solr's `start/rows` with deep offsets is slow (heap sort).
`cursorMark` uses a seek-based approach, consistent and fast for large collections.

---

## Relevance Baseline Plan

Before any query tuning, establish a Solr baseline using Quepid:

1. **Build judgment set** — select 20 representative queries from the Solr query log
   [ASSUMED: query logs are available; if not, derive from product use cases]
2. **Rate top-10 Solr results** for each query (1 = not relevant, 3 = relevant, 5 = highly relevant)
3. **Capture baseline nDCG@10** — this is the target to match or beat
4. **Run identical queries on OpenSearch** — compare nDCG@10 side-by-side
5. **Accept or tune** — if OpenSearch nDCG ≥ Solr nDCG for ≥ 90% of queries, proceed to cutover

**Expected delta:** BM25 vs TF-IDF produces 30-40% ranking difference in top-10 for
typical collections. This does not mean 30-40% of queries will fail the parity gate —
many differences will be acceptable or improvements. Measure first.

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| P50 search latency | ≤ 30ms | At OpenSearch client (excludes app overhead) |
| P99 search latency | ≤ 150ms | Under normal load (not bulk reindex) |
| Bulk reindex rate | ≥ 500 docs/sec | With refresh_interval=-1 during reindex |
| Index refresh latency | 1s (default) | Acceptable NRT; adjust if near-real-time critical |
| Cluster disk usage | ≤ 70% | Alert at 80%; hard block at 90% (AWS watermark) |

[ASSUMED: targets based on r6g.large.search sizing; revisit if index size > 5GB]
