# Technical Design: Northstar Enterprise Demo

This document defines the target OpenSearch design for the Northstar enterprise sample.

---

## Target Index Strategy

For the demo, use one primary index with aliases:

- write alias: `atlas-search-write`
- read alias: `atlas-search-read`
- concrete index: `atlas-search-v1`

This keeps the demo simple while still following a production-sane versioned-index pattern.

---

## Index Mapping

```json
{
  "settings": {
    "index": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "refresh_interval": "1s"
    },
    "analysis": {
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "northstar_synonyms": {
          "type": "synonym_graph",
          "synonyms": [
            "seal kit,gasket kit",
            "manual,guide",
            "bulletin,service alert",
            "part,component"
          ]
        }
      },
      "analyzer": {
        "northstar_text_index": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop"]
        },
        "northstar_text_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop", "northstar_synonyms"]
        }
      }
    }
  },
  "mappings": {
    "dynamic": "true",
    "properties": {
      "id": { "type": "keyword" },
      "doc_type": { "type": "keyword" },
      "title": {
        "type": "text",
        "analyzer": "northstar_text_index",
        "search_analyzer": "northstar_text_query",
        "copy_to": "score_text"
      },
      "summary": {
        "type": "text",
        "analyzer": "northstar_text_index",
        "search_analyzer": "northstar_text_query",
        "copy_to": "score_text"
      },
      "body": {
        "type": "text",
        "analyzer": "northstar_text_index",
        "search_analyzer": "northstar_text_query",
        "copy_to": "score_text"
      },
      "score_text": {
        "type": "text",
        "analyzer": "northstar_text_index",
        "search_analyzer": "northstar_text_query"
      },
      "part_number": {
        "type": "keyword"
      },
      "model_number": {
        "type": "keyword"
      },
      "product_line": {
        "type": "keyword"
      },
      "region": {
        "type": "keyword"
      },
      "language": {
        "type": "keyword"
      },
      "visibility_level": {
        "type": "keyword"
      },
      "dealer_tier": {
        "type": "keyword"
      },
      "business_unit": {
        "type": "keyword"
      },
      "published_at": {
        "type": "date"
      },
      "updated_at": {
        "type": "date"
      }
    },
    "dynamic_templates": [
      {
        "attr_as_keyword": {
          "match": "attr_*",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "txt_as_text": {
          "match": "txt_*",
          "mapping": {
            "type": "text",
            "analyzer": "northstar_text_index",
            "search_analyzer": "northstar_text_query"
          }
        }
      },
      {
        "num_as_double": {
          "match": "num_*",
          "mapping": {
            "type": "double"
          }
        }
      }
    ]
  }
}
```

---

## Mapping Notes

| Solr Pattern | OpenSearch Equivalent | Handling |
|---|---|---|
| `copyField` to catch-all text | `copy_to` to `score_text` | explicit |
| `title/summary/body` text fields | `text` with custom analyzers | explicit |
| identifier lookup fields | `keyword` | exact matching and filters |
| facet fields | `keyword` | terms aggs |
| freshness dates | `date` | `function_score` |
| dynamic `attr_*`, `txt_*`, `num_*` | dynamic templates | controlled field family handling |

---

## Query Architecture

### 1. Enterprise Keyword Search

Use `multi_match` across:

- `title^8`
- `part_number^12`
- `model_number^10`
- `summary^4`
- `body^1`
- `txt_keywords^5`

### 2. Entitlements And Region Filters

Apply `visibility_level`, `dealer_tier`, `region`, and `business_unit` in `bool.filter`.
Do not score on these fields.

### 3. Freshness For Bulletins

Use `function_score` with a recency decay on `published_at`, plus a content-type boost when
the query pattern is bulletin-like.

### 4. Facets

Use aggregations for:

- `doc_type`
- `product_line`
- `region`
- `visibility_level`

### 5. Document-Type Narrowing

Use `term` filters on `doc_type`, not separate query endpoints per type.

---

## Example Query Translation

### Solr

```text
/select?q=overheating+fault+E41
&defType=edismax
&qf=title^7 error_codes^12 symptoms^8 body^2
&bq=doc_type:bulletin^5
&bf=recip(ms(NOW,published_at),3.16e-11,1,1)^3
&fq=region:EMEA
```

### OpenSearch

```json
{
  "query": {
    "function_score": {
      "query": {
        "bool": {
          "must": [
            {
              "multi_match": {
                "query": "overheating fault E41",
                "fields": ["title^7", "txt_keywords^8", "summary^4", "body^2"],
                "type": "best_fields"
              }
            }
          ],
          "filter": [
            { "term": { "region": "EMEA" } }
          ],
          "should": [
            { "term": { "doc_type": { "value": "bulletin", "boost": 5 } } }
          ]
        }
      },
      "functions": [
        {
          "gauss": {
            "published_at": {
              "origin": "now",
              "scale": "30d",
              "decay": 0.5
            }
          },
          "weight": 3
        }
      ],
      "boost_mode": "multiply"
    }
  },
  "aggs": {
    "by_doc_type": { "terms": { "field": "doc_type" } },
    "by_product_line": { "terms": { "field": "product_line" } }
  }
}
```

---

## Indexing Workflow

1. Export source documents from Solr or load the prepared sample corpus.
2. Normalize document types and field names into a single application model.
3. Create `atlas-search-v1`.
4. Attach read/write aliases.
5. Bulk index sample documents with refresh disabled during load.
6. Refresh, run validation queries, and capture baseline demo results.

---

## Validation Strategy

Use a simple demo validation set:

- 10 search queries
- 3 entitlement scenarios
- 4 facet checks
- 2 freshness-sensitive bulletin searches

For the demo, the goal is not exhaustive statistical relevance testing. The goal is to show:

- credible ranking behavior
- correct filters
- correct facet counts
- a migration plan that can scale into a fuller validation cycle later

---

## Known Redesign Areas

- any existing Solr collapse/grouping behavior
- exact synonym parity between source and target analyzers
- whether one index remains the right target model after broader source audit
