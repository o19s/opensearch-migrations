# Query Syntax Mapping: Solr to OpenSearch

**Source**: https://bigdataboutique.com/blog/solr-to-opensearch-migration-deep-dive

---

## Overview

This document provides a comprehensive query syntax reference for translating Solr queries to OpenSearch Query DSL. The key principle is that Solr query parsers are URL-parameter-based while OpenSearch uses structured JSON Query DSL.

---

## Standard Query Parser Mapping

### Basic Field Queries

**Solr**:
```
title:solr
```

**OpenSearch**:
```json
{
  "query": {
    "match": {
      "title": "solr"
    }
  }
}
```

**Explanation**: Solr's simple field:value uses the Standard query parser by default. In OpenSearch, `match` is the closest equivalent, performing full-text search with analysis applied.

---

### Boolean Operators

**Solr**:
```
title:solr AND status:published AND date:[2020-01-01 TO 2020-12-31]
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "solr" } },
        { "term": { "status": "published" } },
        {
          "range": {
            "date": {
              "gte": "2020-01-01",
              "lte": "2020-12-31"
            }
          }
        }
      ]
    }
  }
}
```

**Mapping**:
- `AND` → `bool.must` (all must match)
- `OR` → `bool.should` (at least one matches, affects scoring)
- `NOT field:value` → `bool.must_not` (must not match)

**Important**: `bool.should` without `must` requires at least one clause to match by default. To change, use `minimum_should_match: 1`.

---

### Phrase Queries

**Solr**:
```
title:"solr for enterprise"
```

**OpenSearch**:
```json
{
  "query": {
    "match_phrase": {
      "title": "solr for enterprise"
    }
  }
}
```

**With Slop** (words can appear within N positions):

**Solr**:
```
title:"solr enterprise"~5
```

**OpenSearch**:
```json
{
  "query": {
    "match_phrase": {
      "title": "solr enterprise",
      "slop": 5
    }
  }
}
```

---

### Wildcard and Prefix Queries

**Solr**:
```
title:sol*
title:*arch
```

**OpenSearch**:
```json
{
  "query": {
    "wildcard": {
      "title": "sol*"
    }
  }
}
```

```json
{
  "query": {
    "wildcard": {
      "title": "*arch"
    }
  }
}
```

**Note**: Wildcards are inefficient in both systems. For prefix searches, use `prefix` query instead:

**OpenSearch (preferred for prefix)**:
```json
{
  "query": {
    "prefix": {
      "title": "sol"
    }
  }
}
```

---

### Range Queries

**Solr**:
```
price:[10 TO 100]
price:{10 TO 100}
date:[2020-01-01T00:00:00Z TO NOW]
```

The square bracket `[` means inclusive; curly brace `{` means exclusive.

**OpenSearch**:
```json
{
  "query": {
    "range": {
      "price": {
        "gte": 10,
        "lte": 100
      }
    }
  }
}
```

```json
{
  "query": {
    "range": {
      "price": {
        "gt": 10,
        "lt": 100
      }
    }
  }
}
```

```json
{
  "query": {
    "range": {
      "date": {
        "gte": "2020-01-01T00:00:00Z",
        "lte": "now"
      }
    }
  }
}
```

**Mapping**:
- `[` (inclusive) → `gte`/`lte`
- `{` (exclusive) → `gt`/`lt`
- `NOW` → `now` (OpenSearch date math)

---

### Negation

**Solr**:
```
title:solr AND NOT status:archived
title:solr AND -status:archived
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": { "match": { "title": "solr" } },
      "must_not": { "term": { "status": "archived" } }
    }
  }
}
```

---

## DisMax Query Parser Mapping

DisMax is Solr's best query parser for user-facing search. It handles multiple fields, intelligent boosting, and phrase queries automatically.

### Basic DisMax Query

**Solr**:
```
q=solr search&defType=dismax&qf=title^2 body^1 tags^0.5
```

**OpenSearch**:
```json
{
  "query": {
    "multi_match": {
      "query": "solr search",
      "fields": ["title^2", "body^1", "tags^0.5"],
      "type": "best_fields"
    }
  }
}
```

**Explanation**:
- `defType=dismax` tells Solr to use DisMax
- `qf` (query fields) lists fields to search with optional boosts
- `^2` syntax boosts field importance
- `multi_match` with `best_fields` type is the closest OpenSearch equivalent

---

### DisMax Parameters Mapping

| Solr DisMax | OpenSearch Equivalent | Behavior |
|-------------|----------------------|----------|
| `qf=field1^2 field2^1` | `fields: ["field1^2", "field2^1"]` in `multi_match` | Field boosting |
| `mm=2<75%` | `minimum_should_match: "75%"` | Minimum match threshold |
| `tie_breaker=0.3` | `tie_breaker: 0.3` | Cross-field relevance tiebreaker |
| `pf=title^10` | Use `should` clause with boost | Phrase matching boost |
| `bf=sqrt(popularity)` | `function_score` query | Numeric field boosting |
| `bq=category:featured^5` | `bool.should` with boost | Boost query |

---

### DisMax Example: Complex Query

**Solr DisMax**:
```
q=solr&defType=dismax&qf=title^3 body^1 tags^0.5&mm=75%&tie_breaker=0.3&pf=title^10&bq=featured:true^5
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "solr",
            "fields": ["title^3", "body^1", "tags^0.5"],
            "type": "best_fields",
            "tie_breaker": 0.3,
            "minimum_should_match": "75%"
          }
        }
      ],
      "should": [
        {
          "match_phrase": {
            "title": "solr",
            "boost": 10
          }
        },
        {
          "term": {
            "featured": {
              "value": true,
              "boost": 5
            }
          }
        }
      ]
    }
  }
}
```

---

## eDisMax Query Parser Mapping

eDisMax (Extended DisMax) adds per-field slop and advanced phrase handling.

### Per-Field Slop

**Solr eDisMax**:
```
q=solr guide&defType=edismax&qf=title~2^3 body~5
```

The `~2` means allow 2 words between query terms in the title field.

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "should": [
        {
          "match_phrase": {
            "title": "solr guide",
            "slop": 2,
            "boost": 3
          }
        },
        {
          "match_phrase": {
            "body": "solr guide",
            "slop": 5
          }
        }
      ]
    }
  }
}
```

---

### Advanced eDisMax Features

**Solr eDisMax with multiple features**:
```
q=solr&defType=edismax&qf=title body&mm=100%&bq=category:training^10 author:expert^5&boost=sqrt(views)
```

**OpenSearch equivalent**:
```json
{
  "query": {
    "function_score": {
      "query": {
        "bool": {
          "must": [
            {
              "multi_match": {
                "query": "solr",
                "fields": ["title", "body"],
                "minimum_should_match": "100%"
              }
            }
          ],
          "should": [
            {
              "term": {
                "category": {
                  "value": "training",
                  "boost": 10
                }
              }
            },
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
      },
      "functions": [
        {
          "sqrt": { "views": {} }
        }
      ]
    }
  }
}
```

---

## Filter Queries Mapping

Filter queries in Solr are fast, cacheable constraints that don't affect relevance scoring.

### Single Filter Query

**Solr**:
```
q=title:solr&fq=status:published
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": { "match": { "title": "solr" } },
      "filter": { "term": { "status": "published" } }
    }
  }
}
```

### Multiple Filter Queries

**Solr**:
```
q=title:solr&fq=status:published&fq=category:tutorial&fq=date:[NOW-30DAYS TO NOW]
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": { "match": { "title": "solr" } },
      "filter": [
        { "term": { "status": "published" } },
        { "term": { "category": "tutorial" } },
        { "range": { "date": { "gte": "now-30d" } } }
      ]
    }
  }
}
```

**Key advantage**: OpenSearch filters in the `filter` context are automatically cached by segment, improving performance on repeated queries.

---

## Faceting Mapping

### Simple Term Facet

**Solr**:
```
q=*:*&facet=true&facet.field=category&facet.field=status&facet.limit=10
```

**OpenSearch**:
```json
{
  "query": { "match_all": {} },
  "aggs": {
    "category_facet": {
      "terms": {
        "field": "category",
        "size": 10
      }
    },
    "status_facet": {
      "terms": {
        "field": "status",
        "size": 10
      }
    }
  }
}
```

---

### Range Facet

**Solr**:
```
q=*:*&facet=true&facet.range=price&facet.range.start=0&facet.range.end=1000&facet.range.gap=100
```

**OpenSearch**:
```json
{
  "query": { "match_all": {} },
  "aggs": {
    "price_facet": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 100 },
          { "from": 100, "to": 200 },
          { "from": 200, "to": 300 },
          { "from": 300, "to": 400 },
          { "from": 400, "to": 500 },
          { "from": 500 }
        ]
      }
    }
  }
}
```

---

### Date Histogram Facet

**Solr**:
```
q=*:*&facet=true&facet.date=created_at&facet.date.start=2020-01-01T00:00:00Z&facet.date.end=2021-01-01T00:00:00Z&facet.date.gap=%2B1MONTH
```

**OpenSearch**:
```json
{
  "query": { "match_all": {} },
  "aggs": {
    "created_monthly": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "month",
        "min_doc_count": 0
      }
    }
  }
}
```

**Interval mapping**:
- `+1MONTH` → `calendar_interval: "month"`
- `+1DAY` → `calendar_interval: "day"`
- `+1HOUR` → `calendar_interval: "hour"`
- `+30SECONDS` → `fixed_interval: "30s"`

---

## Boosting Mapping

### Boost Query (bq)

**Solr**:
```
q=title:solr&defType=dismax&bq=featured:true^10
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": { "match": { "title": "solr" } },
      "should": {
        "term": {
          "featured": {
            "value": true,
            "boost": 10
          }
        }
      }
    }
  }
}
```

---

### Boost Function (bf)

**Solr**:
```
q=title:solr&bf=sqrt(views)&bf=log(1+sales)
```

**OpenSearch**:
```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": "solr" } },
      "functions": [
        { "sqrt": { "views": {} } },
        { "log1p": { "sales": {} } }
      ],
      "boost_mode": "multiply"
    }
  }
}
```

---

### Relevance Boosting with Script

**Solr** (using boost in query):
```
title:solr^2 body:solr^1
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "title": { "query": "solr", "boost": 2 } } },
        { "match": { "body": { "query": "solr", "boost": 1 } } }
      ]
    }
  }
}
```

---

## Highlighting Mapping

### Basic Highlighting

**Solr**:
```
q=title:solr&hl=true&hl.fl=title,body&hl.fragsize=150&hl.simple.pre=<em>&hl.simple.post=</em>
```

**OpenSearch**:
```json
{
  "query": { "match": { "title": "solr" } },
  "highlight": {
    "fields": {
      "title": {},
      "body": {
        "fragment_size": 150,
        "number_of_fragments": 3
      }
    },
    "pre_tags": ["<em>"],
    "post_tags": ["</em>"]
  }
}
```

---

## Spell Check / Suggester Mapping

Solr has a SpellCheckComponent; OpenSearch uses Suggester API for similar functionality.

### Solr Spell Check

**Solr**:
```
q=solrr&spellcheck=true&spellcheck.build=true&spellcheck.collate=true
```

**OpenSearch Suggester** (requires index-time setup):
```json
{
  "query": { "match_all": {} },
  "suggest": {
    "text": "solrr",
    "suggestions": {
      "term": {
        "field": "title.suggest"
      }
    }
  }
}
```

Index setup for suggestions:
```json
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "suggest": {
            "type": "completion"
          }
        }
      }
    }
  }
}
```

---

## MoreLikeThis Mapping

### Solr MoreLikeThis

**Solr**:
```
q={!mlt qf=title,body mindf=1 mintf=1 minwl=3}solr
```

Or using MLT handler:
```
/select?mlt=true&mlt.fl=title,body&mlt.mindf=1&mlt.mintf=1
```

**OpenSearch more_like_this query**:
```json
{
  "query": {
    "more_like_this": {
      "fields": ["title", "body"],
      "like": "solr",
      "min_doc_freq": 1,
      "min_term_freq": 1,
      "min_word_length": 3
    }
  }
}
```

**For finding similar documents by ID**:

**OpenSearch**:
```json
{
  "query": {
    "more_like_this": {
      "fields": ["title", "body"],
      "like": [
        {
          "_index": "documents",
          "_id": "1"
        }
      ],
      "min_doc_freq": 1,
      "min_term_freq": 1
    }
  }
}
```

---

## Pagination Mapping

### Basic Pagination (Offset-Based)

**Solr**:
```
q=title:solr&start=100&rows=20
```

**OpenSearch**:
```json
{
  "query": { "match": { "title": "solr" } },
  "from": 100,
  "size": 20
}
```

**Note**: OpenSearch limit of deep pagination (from + size > 10000) requires `index.max_result_window` tuning.

---

### Cursor-Based Pagination (search_after)

For large datasets, `search_after` is more efficient than `from`:

**OpenSearch**:
```json
{
  "query": { "match": { "title": "solr" } },
  "sort": [{ "_id": "asc" }],
  "size": 20,
  "search_after": ["last_document_id_from_previous_query"]
}
```

**Advantages**:
- Constant memory usage regardless of offset
- Better for real-time data
- Handles document deletions gracefully

---

### Scroll API (Deprecated but Similar)

**OpenSearch scroll** (use Point-In-Time instead):
```json
{
  "query": { "match": { "title": "solr" } },
  "size": 1000,
  "scroll": "5m"
}
```

**Modern approach (Point-In-Time)**:
```json
{
  "pit": { "id": "<pit_id>", "keep_alive": "5m" },
  "size": 1000,
  "sort": [{ "_shard_doc": "asc" }]
}
```

---

## Complex Query Examples

### Example 1: E-commerce Product Search

**Solr**:
```
q=laptop&defType=dismax&qf=title^3 description^1 tags^0.5&fq=status:active&fq=price:[0 TO 5000]&fq=brand:(Dell OR HP OR Lenovo)&facet=true&facet.field=category&facet.field=brand&facet.limit=10&hl=true&hl.fl=title,description
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "laptop",
            "fields": ["title^3", "description^1", "tags^0.5"],
            "type": "best_fields"
          }
        }
      ],
      "filter": [
        { "term": { "status": "active" } },
        { "range": { "price": { "gte": 0, "lte": 5000 } } },
        {
          "bool": {
            "should": [
              { "term": { "brand": "Dell" } },
              { "term": { "brand": "HP" } },
              { "term": { "brand": "Lenovo" } }
            ],
            "minimum_should_match": 1
          }
        }
      ]
    }
  },
  "aggs": {
    "category": {
      "terms": { "field": "category", "size": 10 }
    },
    "brand": {
      "terms": { "field": "brand", "size": 10 }
    }
  },
  "highlight": {
    "fields": {
      "title": {},
      "description": {}
    }
  },
  "size": 20,
  "from": 0
}
```

---

### Example 2: Blog Search with Date Range

**Solr**:
```
q=elasticsearch&defType=edismax&qf=title~2^3 content~5^1&fq=published:true&fq=published_date:[NOW-6MONTHS TO NOW]&bq=featured:true^5&sort=published_date desc
```

**OpenSearch**:
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "elasticsearch",
            "fields": ["title^3", "content^1"],
            "type": "phrase"
          }
        }
      ],
      "filter": [
        { "term": { "published": true } },
        {
          "range": {
            "published_date": {
              "gte": "now-6M"
            }
          }
        }
      ],
      "should": {
        "term": {
          "featured": {
            "value": true,
            "boost": 5
          }
        }
      }
    }
  },
  "sort": [{ "published_date": "desc" }],
  "size": 20,
  "from": 0
}
```

---

## Performance Considerations

1. **Filter vs Query**: Use `filter` context for boolean constraints; they're cached
2. **Query complexity**: Deeply nested `bool` queries have exponential complexity; simplify where possible
3. **Wildcards**: Leading wildcards (`*field`) are inefficient; use `prefix` or `match_phrase_prefix` instead
4. **Aggregations**: Place costly aggregations inside filtered subqueries when possible
5. **Sorting**: Sorting on `text` fields requires additional memory; use `keyword` fields instead
6. **Pagination depth**: Use `search_after` instead of `from` for deep pagination

---

## Summary: Quick Reference Table

| Solr Feature | OpenSearch Equivalent | Notes |
|--------------|----------------------|-------|
| Standard parser | `match`, `bool` | Basic field queries |
| DisMax | `multi_match` with `best_fields` | Multi-field search |
| eDisMax | `bool` + `multi_match` + slop | Advanced phrase logic |
| fq | `bool.filter` | Fast, cached filtering |
| facet.field | `terms` aggregation | Category faceting |
| facet.range | `range` aggregation | Range faceting |
| facet.date | `date_histogram` aggregation | Time-series faceting |
| hl | `highlight` | Result highlighting |
| spellcheck | `suggest` with completion | Suggestions/corrections |
| mlt | `more_like_this` | Similar documents |
| start/rows | `from`/`size` | Pagination |
| scroll | Point-In-Time or scroll | Long-running iterations |
| bf | `function_score` | Numeric boosting |
| bq | `bool.should` + boost | Conditional boosting |

