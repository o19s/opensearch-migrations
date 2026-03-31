# Solr to OpenSearch Query Translation

## Purpose

Translate Solr query requests into idiomatic OpenSearch Query DSL. Preserve relevance intent,
non-scoring filter semantics, and business logic -- not just syntax.

---

## Standard Parser

### Field queries

```
Solr:  title:opensearch
OS:    {"query": {"match": {"title": "opensearch"}}}
```

### Boolean operators

| Solr operator | OpenSearch `bool` clause |
|---------------|------------------------|
| `AND` / `+`  | `must`                 |
| `OR`          | `should` (with `minimum_should_match: 1` when no `must`) |
| `NOT` / `-`  | `must_not`             |

```
Solr:  title:solr AND status:published AND -archived:true
OS:    {"query": {"bool": {
         "must": [{"match": {"title": "solr"}}, {"term": {"status": "published"}}],
         "must_not": [{"term": {"archived": true}}]
       }}}
```

### Phrase queries

```
Solr:  title:"solr enterprise"
OS:    {"query": {"match_phrase": {"title": "solr enterprise"}}}

Solr:  title:"solr enterprise"~5
OS:    {"query": {"match_phrase": {"title": {"query": "solr enterprise", "slop": 5}}}}
```

### Wildcards and prefix

```
Solr:  title:sol*
OS:    {"query": {"prefix": {"title": "sol"}}}         -- prefer prefix for trailing *
OS:    {"query": {"wildcard": {"title": "s?lr*"}}}      -- use wildcard only when needed
```

Leading wildcards (`*arch`) are expensive in both systems. Flag them in migration reports.

### Range queries

| Solr bracket | OpenSearch operator |
|-------------|-------------------|
| `[` inclusive | `gte` / `lte`   |
| `{` exclusive | `gt` / `lt`     |
| `NOW`        | `now`             |

```
Solr:  price:[10 TO 100]
OS:    {"query": {"range": {"price": {"gte": 10, "lte": 100}}}}

Solr:  date:[NOW-30DAYS TO NOW]
OS:    {"query": {"range": {"date": {"gte": "now-30d", "lte": "now"}}}}
```

### Fuzzy search

```
Solr:  campng~2
OS:    {"query": {"fuzzy": {"title": {"value": "campng", "fuzziness": 2}}}}
```

---

## eDisMax (and DisMax)

eDisMax is the core user-facing query parser in most production Solr apps. Translation must
preserve the relevance-shaping intent, not just produce valid JSON.

### qf (query fields) -> multi_match

```
Solr:  q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5
OS:    {"query": {"multi_match": {
         "query": "laptop",
         "fields": ["title^3", "description^1", "tags^0.5"],
         "type": "best_fields"
       }}}
```

Field boosts are often business logic. Always preserve them and flag for relevance review.

### pf (phrase fields) -> match_phrase in bool.should

```
Solr:  q=solr guide&defType=edismax&qf=title body&pf=title^10
OS:    {"query": {"bool": {
         "must": [{"multi_match": {"query": "solr guide", "fields": ["title", "body"]}}],
         "should": [{"match_phrase": {"title": {"query": "solr guide", "boost": 10}}}]
       }}}
```

pf rewards phrase proximity without requiring it. The `should` clause preserves this behavior.

### mm (minimum should match)

```
Solr:  q=solr migration guide&defType=edismax&qf=title body&mm=75%
OS:    {"query": {"multi_match": {
         "query": "solr migration guide",
         "fields": ["title", "body"],
         "minimum_should_match": "75%"
       }}}
```

mm changes the candidate set. Poor handling causes precision and recall surprises. Always
preserve the exact mm value.

### bq (boost query) -> bool.should with boost

```
Solr:  q=laptop&defType=edismax&qf=title body&bq=featured:true^5
OS:    {"query": {"bool": {
         "must": [{"multi_match": {"query": "laptop", "fields": ["title", "body"]}}],
         "should": [{"term": {"featured": {"value": true, "boost": 5}}}]
       }}}
```

### boost / bf (boost functions) -> function_score

```
Solr:  q=laptop&defType=edismax&qf=title body&boost=sqrt(views)
OS:    {"query": {"function_score": {
         "query": {"multi_match": {"query": "laptop", "fields": ["title", "body"]}},
         "functions": [{"script_score": {"script": {"source": "Math.sqrt(doc['views'].value)"}}}],
         "boost_mode": "multiply"
       }}}
```

Common Solr function mappings:
- `sqrt(field)` -> `Math.sqrt(doc['field'].value)`
- `log(field)` -> `Math.log(doc['field'].value)`
- `log(1+field)` -> use `Math.log1p(doc['field'].value)`

### tie_breaker

```
Solr:  tie=0.3
OS:    "tie_breaker": 0.3   (inside multi_match)
```

### Per-field slop (eDisMax-specific)

```
Solr:  q=solr guide&defType=edismax&qf=title~2^3 body~5
OS:    {"query": {"bool": {"should": [
         {"match_phrase": {"title": {"query": "solr guide", "slop": 2, "boost": 3}}},
         {"match_phrase": {"body": {"query": "solr guide", "slop": 5}}}
       ]}}}
```

### Full eDisMax composite example

```
Solr:  q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5
       &mm=75%&pf=title^10&bq=featured:true^5&boost=sqrt(views)
       &fq=status:active&fq=price:[0 TO 5000]

OS:    {"query": {"function_score": {
         "query": {"bool": {
           "must": [{"multi_match": {
             "query": "laptop",
             "fields": ["title^3", "description^1", "tags^0.5"],
             "type": "best_fields",
             "minimum_should_match": "75%"
           }}],
           "should": [
             {"match_phrase": {"title": {"query": "laptop", "boost": 10}}},
             {"term": {"featured": {"value": true, "boost": 5}}}
           ],
           "filter": [
             {"term": {"status": "active"}},
             {"range": {"price": {"gte": 0, "lte": 5000}}}
           ]
         }},
         "functions": [{"script_score": {"script": {"source": "Math.sqrt(doc['views'].value)"}}}],
         "boost_mode": "multiply"
       }}}
```

---

## Filter Queries (fq) -> bool.filter

fq clauses must land in `bool.filter`, never in scoring context. This preserves non-scoring
semantics and enables OpenSearch filter caching.

### Single filter

```
Solr:  q=title:solr&fq=status:published
OS:    {"query": {"bool": {
         "must": [{"match": {"title": "solr"}}],
         "filter": [{"term": {"status": "published"}}]
       }}}
```

### Multiple filters (conjunctive by default)

```
Solr:  q=laptop&fq=status:active&fq=category:electronics&fq=price:[0 TO 500]
OS:    {"query": {"bool": {
         "must": [{"match_all": {}}],
         "filter": [
           {"term": {"status": "active"}},
           {"term": {"category": "electronics"}},
           {"range": {"price": {"gte": 0, "lte": 500}}}
         ]
       }}}
```

### OR within a single fq

```
Solr:  fq=brand:(Dell OR HP OR Lenovo)
OS:    "filter": [{"bool": {"should": [
         {"term": {"brand": "Dell"}},
         {"term": {"brand": "HP"}},
         {"term": {"brand": "Lenovo"}}
       ], "minimum_should_match": 1}}]
```

### Match-all with filters only

```
Solr:  q=*:*&fq=price:[10 TO 100]&fq=inStock:true
OS:    {"query": {"bool": {
         "filter": [
           {"range": {"price": {"gte": 10, "lte": 100}}},
           {"term": {"inStock": true}}
         ]
       }}}
```

---

## Faceting -> Aggregations

### Field facet -> terms aggregation

```
Solr:  facet=true&facet.field=category&facet.field=brand&facet.limit=10&facet.mincount=5
OS:    "aggs": {
         "category": {"terms": {"field": "category", "size": 10, "min_doc_count": 5}},
         "brand": {"terms": {"field": "brand", "size": 10, "min_doc_count": 5}}
       }
```

### Range facet -> range aggregation

```
Solr:  facet.range=price&facet.range.start=0&facet.range.end=1000&facet.range.gap=100
OS:    "aggs": {"price_ranges": {"histogram": {"field": "price", "interval": 100}}}
```

Use `histogram` when gaps are uniform. Use `range` with explicit `ranges` array when custom.

### Date facet -> date_histogram

```
Solr:  facet.range=created_at&facet.range.gap=+1MONTH
OS:    "aggs": {"created_monthly": {"date_histogram": {
         "field": "created_at", "calendar_interval": "month"
       }}}
```

Interval mapping: `+1MONTH` -> `month`, `+1DAY` -> `day`, `+1HOUR` -> `hour`,
`+30SECONDS` -> `fixed_interval: "30s"`.

### Pivot facet -> nested aggregation

```
Solr:  facet.pivot=category,brand
OS:    "aggs": {"category": {"terms": {"field": "category"}, "aggs": {
         "brand": {"terms": {"field": "brand"}}
       }}}
```

---

## Highlighting

```
Solr:  hl=true&hl.fl=title,body&hl.fragsize=150
       &hl.simple.pre=<em>&hl.simple.post=</em>

OS:    "highlight": {
         "fields": {
           "title": {},
           "body": {"fragment_size": 150, "number_of_fragments": 3}
         },
         "pre_tags": ["<em>"],
         "post_tags": ["</em>"]
       }
```

---

## Spellcheck / Suggest

Solr's SpellCheckComponent maps to the OpenSearch Suggest API. Requires index-time setup.

```
Solr:  q=campign&spellcheck=true&spellcheck.collate=true

OS:    {"suggest": {"text": "campign", "spell": {"term": {"field": "title"}}}}
```

For autocomplete, use a `completion` field type in the mapping:

```json
"title": {"type": "text", "fields": {"suggest": {"type": "completion"}}}
```

Then query with: `{"suggest": {"title-suggest": {"prefix": "cam", "completion": {"field": "title.suggest"}}}}`

---

## Sort, Pagination, Field List

### Sort

```
Solr:  sort=price asc,score desc
OS:    "sort": [{"price": "asc"}, "_score"]
```

Sort on `text` fields requires a `.keyword` sub-field in OpenSearch.

### Pagination

```
Solr:  start=20&rows=10
OS:    "from": 20, "size": 10
```

Deep pagination (from + size > 10,000) requires `search_after` with a sort tiebreaker:

```json
{"sort": [{"price": "asc"}, {"_id": "asc"}], "size": 10, "search_after": [29.99, "doc_500"]}
```

### Field list (fl) -> _source filtering

```
Solr:  fl=id,title,price,score
OS:    "_source": ["id", "title", "price"]
```

`score` is not in `_source`. Request it separately or it is returned by default in `_score`.

---

## Grouping / Collapsing

### Solr group.field -> collapse field

```
Solr:  q=laptop&group=true&group.field=brand&group.limit=1
OS:    {"query": {"match": {"title": "laptop"}},
        "collapse": {"field": "brand"},
        "aggs": {"brand_hits": {"top_hits": {"size": 1}}}
       }
```

`collapse` returns one doc per unique field value. For multiple docs per group, combine with
`top_hits` aggregation.

### Solr group.query -> filters + top_hits

For arbitrary grouping queries, use named filters aggregation:

```json
"aggs": {
  "price_groups": {
    "filters": {
      "filters": {
        "cheap": {"range": {"price": {"lte": 100}}},
        "mid": {"range": {"price": {"gt": 100, "lte": 500}}},
        "premium": {"range": {"price": {"gt": 500}}}
      }
    },
    "aggs": {"top": {"top_hits": {"size": 3}}}
  }
}
```

---

## Migration Warnings

Flag these patterns explicitly when encountered during translation:

1. **Leading wildcards** (`*suffix`) -- expensive, suggest ngram tokenizer or reverse wildcard
2. **Complex mm expressions** (`2<75%`) -- verify OpenSearch supports the exact syntax variant
3. **bf with conditional logic** (`if(field>10,2,1)`) -- requires Painless script in function_score
4. **Geo fq** -- requires geo_point field type and geo_distance/geo_bounding_box queries
5. **pf2/pf3 (bigram/trigram phrase boost)** -- no direct equivalent; approximate with shingle analyzer + match_phrase
6. **autoRelaxMM** -- no direct equivalent; document as a behavioral gap
7. **group.func** -- no direct equivalent; requires custom scripting
8. **Multiple group.field** -- OpenSearch collapse supports only one field

When only partial translation is possible, emit a warning with the untranslated parameter
and a concrete suggestion for manual review.
