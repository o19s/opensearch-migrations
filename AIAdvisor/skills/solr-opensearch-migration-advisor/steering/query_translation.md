# Solr to OpenSearch Query Translation Steering

## Overview
Translate individual Solr queries (standard, dismax, edismax) into OpenSearch Query DSL.

## Key Conversions
- `q`: Map to `query` in OpenSearch.
- `qf` (Query Fields): Map to `multi_match` with `fields` and `type: "best_fields"`.
- `pf` (Phrase Fields): Map to `multi_match` with `type: "phrase"`.
- `mm` (Minimum Should Match): Map to `minimum_should_match` in `bool` or `multi_match`.
- `boost`: Map to `boost` or use `function_score`.
- `fq` (Filter Query): Map to `filter` in a `bool` query.
- `bq` (Boost Query): Map to `should` clause in a `bool` query.
- `bf` (Boost Function): Map to `function_score` with `script_score` or built-in functions.
- `fl` (Field List): Map to `_source` includes/excludes.
- `sort`: Map to `sort` array.
- `rows`/`start`: Map to `size`/`from`.
- `wt` (Writer Type): Not needed — OpenSearch always returns JSON.

## Worked Examples

### 1. Simple field query with boolean AND
Solr:
```
q=title:opensearch AND price:[10 TO 100]
```
OpenSearch:
```json
{"query": {"bool": {"must": [
  {"match": {"title": "opensearch"}},
  {"range": {"price": {"gte": 10, "lte": 100}}}
]}}}
```

### 2. Simple term query (match_all equivalent)
Solr:
```
q=*:*
```
OpenSearch:
```json
{"query": {"match_all": {}}}
```

### 3. Phrase query
Solr:
```
q="open source search"
```
OpenSearch:
```json
{"query": {"match_phrase": {"_all": "open source search"}}}
```
Note: OpenSearch has no `_all` field by default. Map to `copy_to` target or explicit field.

### 4. Wildcard query
Solr:
```
q=title:open*
```
OpenSearch:
```json
{"query": {"wildcard": {"title": {"value": "open*"}}}}
```

### 5. Fuzzy query
Solr:
```
q=title:opensearh~2
```
OpenSearch:
```json
{"query": {"fuzzy": {"title": {"value": "opensearh", "fuzziness": 2}}}}
```

### 6. Boolean query with OR and NOT
Solr:
```
q=title:opensearch OR title:solr NOT status:archived
```
OpenSearch:
```json
{"query": {"bool": {
  "should": [
    {"match": {"title": "opensearch"}},
    {"match": {"title": "solr"}}
  ],
  "must_not": [{"term": {"status": "archived"}}],
  "minimum_should_match": 1
}}}
```

### 7. eDisMax with qf, pf, and mm
Solr:
```
defType=edismax&q=laptop bag&qf=title^3 description^1.5 category&pf=title^5 description^2&mm=2<75%
```
OpenSearch:
```json
{"query": {"bool": {
  "must": [{
    "multi_match": {
      "query": "laptop bag",
      "fields": ["title^3", "description^1.5", "category"],
      "type": "best_fields",
      "minimum_should_match": "75%"
    }
  }],
  "should": [{
    "multi_match": {
      "query": "laptop bag",
      "fields": ["title^5", "description^2"],
      "type": "phrase"
    }
  }]
}}}
```
Note: Solr's tiered `mm` syntax (`2<75%`) means "if 2 or fewer clauses, all required; otherwise 75%". OpenSearch `minimum_should_match` supports the same syntax.

### 8. Filter query (fq)
Solr:
```
q=laptop&fq=category:electronics&fq=price:[100 TO 500]
```
OpenSearch:
```json
{"query": {"bool": {
  "must": [{"match": {"_all": "laptop"}}],
  "filter": [
    {"term": {"category": "electronics"}},
    {"range": {"price": {"gte": 100, "lte": 500}}}
  ]
}}}
```
Note: Solr `fq` is cached separately; OpenSearch `filter` context skips scoring (equivalent caching benefit).

### 9. Boost query (bq)
Solr:
```
defType=edismax&q=shoes&bq=brand:nike^5
```
OpenSearch:
```json
{"query": {"bool": {
  "must": [{"match": {"_all": "shoes"}}],
  "should": [{"term": {"brand": {"value": "nike", "boost": 5}}}]
}}}
```

### 10. Faceting — field facet to terms aggregation
Solr:
```
q=*:*&facet=true&facet.field=category&facet.mincount=1&facet.limit=10
```
OpenSearch:
```json
{
  "query": {"match_all": {}},
  "aggs": {
    "category_facet": {
      "terms": {"field": "category", "min_doc_count": 1, "size": 10}
    }
  },
  "size": 0
}
```

### 11. Faceting — range facet to range aggregation
Solr:
```
q=*:*&facet=true&facet.range=price&facet.range.start=0&facet.range.end=1000&facet.range.gap=100
```
OpenSearch:
```json
{
  "query": {"match_all": {}},
  "aggs": {
    "price_ranges": {
      "histogram": {"field": "price", "interval": 100}
    }
  },
  "size": 0
}
```

### 12. Faceting — pivot facet to nested aggregation
Solr:
```
q=*:*&facet=true&facet.pivot=category,brand
```
OpenSearch:
```json
{
  "query": {"match_all": {}},
  "aggs": {
    "category_pivot": {
      "terms": {"field": "category"},
      "aggs": {
        "brand_pivot": {
          "terms": {"field": "brand"}
        }
      }
    }
  },
  "size": 0
}
```

### 13. Highlighting
Solr:
```
q=opensearch&hl=true&hl.fl=title,description&hl.fragsize=150&hl.snippets=3
```
OpenSearch:
```json
{
  "query": {"match": {"_all": "opensearch"}},
  "highlight": {
    "fields": {
      "title": {"fragment_size": 150, "number_of_fragments": 3},
      "description": {"fragment_size": 150, "number_of_fragments": 3}
    }
  }
}
```
Note: OpenSearch supports `plain`, `unified`, and `fvh` highlighters. Solr's default maps best to `unified`.

### 14. Function query — boost by recency
Solr:
```
defType=edismax&q=news&bf=recip(ms(NOW,publish_date),3.16e-11,1,1)
```
OpenSearch:
```json
{"query": {"function_score": {
  "query": {"match": {"_all": "news"}},
  "functions": [{
    "exp": {
      "publish_date": {
        "origin": "now",
        "scale": "30d",
        "decay": 0.5
      }
    }
  }],
  "boost_mode": "multiply"
}}}
```
Note: Solr's `recip()` for date decay maps to OpenSearch's `exp`/`gauss`/`linear` decay functions. Exact tuning parameters need recalibration.

### 15. Spatial / geo query
Solr:
```
q=*:*&fq={!geofilt sfield=location pt=40.7128,-74.0060 d=10}
```
OpenSearch:
```json
{"query": {"bool": {
  "must": [{"match_all": {}}],
  "filter": [{
    "geo_distance": {
      "distance": "10km",
      "location": {"lat": 40.7128, "lon": -74.0060}
    }
  }]
}}}
```
Note: Solr `d` is in kilometers by default. Solr `location` (LatLonPointSpatialField) maps to OpenSearch `geo_point`.

### 16. JSON Facet API
Solr:
```json
{
  "query": "*:*",
  "facet": {
    "avg_price": "avg(price)",
    "categories": {
      "type": "terms",
      "field": "category",
      "limit": 5,
      "facet": {
        "avg_price": "avg(price)"
      }
    }
  }
}
```
OpenSearch:
```json
{
  "query": {"match_all": {}},
  "aggs": {
    "avg_price": {"avg": {"field": "price"}},
    "categories": {
      "terms": {"field": "category", "size": 5},
      "aggs": {
        "avg_price": {"avg": {"field": "price"}}
      }
    }
  },
  "size": 0
}
```

### 17. DisMax (simple)
Solr:
```
defType=dismax&q=running shoes&qf=title^2 description&mm=100%
```
OpenSearch:
```json
{"query": {"multi_match": {
  "query": "running shoes",
  "fields": ["title^2", "description"],
  "type": "best_fields",
  "minimum_should_match": "100%"
}}}
```
Note: DisMax is a simplified eDisMax — same translation pattern, fewer parameters.
