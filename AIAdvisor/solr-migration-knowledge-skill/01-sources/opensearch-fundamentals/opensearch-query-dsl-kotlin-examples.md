# OpenSearch Query DSL: Kotlin/Java Examples

## Table of Contents
1. [Match Queries](#match-queries)
2. [Bool Query: Combining Conditions](#bool-query-combining-conditions)
3. [Term & Range Queries](#term--range-queries)
4. [Nested Document Queries](#nested-document-queries)
5. [Function Score](#function-score)
6. [Aggregations](#aggregations)
7. [Highlighting](#highlighting)
8. [Pagination with Search After](#pagination-with-search-after)
9. [Source Filtering](#source-filtering)
10. [Practical Examples](#practical-examples)

All examples use opensearch-java builder API with Kotlin.

---

## Match Queries

### Simple Match

Find documents where a field contains query terms.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.match { m ->
                    m.field("title").query("camping tent")
                }
            }
    },
    ProductDocument::class.java
)

val hits = response.hits().hits().mapNotNull { it.source() }
```

**Generated JSON:**
```json
{
  "query": {
    "match": {
      "title": { "query": "camping tent" }
    }
  }
}
```

**Behavior:** Tokenizes "camping tent" into ["camping", "tent"], returns docs matching either term (OR logic by default).

### Match with Operator (AND/OR)

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.match { m ->
                    m.field("title")
                        .query("camping tent")
                        .operator(Operator.And) // requires all terms
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "match": {
      "title": {
        "query": "camping tent",
        "operator": "and"
      }
    }
  }
}
```

**Operator.And** requires both "camping" AND "tent" to be present.

### Match with Fuzzy

Allow misspellings via Levenshtein distance.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.match { m ->
                    m.field("title")
                        .query("campng") // misspelled
                        .fuzziness("AUTO") // auto-adjust fuzziness based on term length
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "match": {
      "title": {
        "query": "campng",
        "fuzziness": "AUTO"
      }
    }
  }
}
```

Matches "camping" despite typo.

### Match Phrase

Exact phrase matching with positional matching.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.matchPhrase { m ->
                    m.field("title").query("camping gear")
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "match_phrase": {
      "title": { "query": "camping gear" }
    }
  }
}
```

Matches "camping gear" but not "camping summer gear" (word order matters).

### Match Phrase with Slop

Allow words between phrase terms.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.matchPhrase { m ->
                    m.field("title")
                        .query("camping gear")
                        .slop(2) // allow up to 2 words between "camping" and "gear"
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "match_phrase": {
      "title": {
        "query": "camping gear",
        "slop": 2
      }
    }
  }
}
```

Matches "camping summer gear", "camping and outdoor gear", etc.

### Multi-Match

Search multiple fields at once.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.multiMatch { m ->
                    m.query("camping tent")
                        .fields("title^3,description,reviews^0.5") // boost syntax
                        .type(TextQueryType.BestFields) // use highest field score
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "multi_match": {
      "query": "camping tent",
      "fields": ["title^3", "description", "reviews^0.5"],
      "type": "best_fields"
    }
  }
}
```

**Types:**
- `best_fields` (default): Returns max score from any field (good for short queries)
- `cross_fields`: Searches all fields as if they're one field (good for names)
- `most_fields`: Uses term frequency from all fields (good for synonyms)
- `phrase`: Match phrase in any field

---

## Bool Query: Combining Conditions

The `bool` query combines multiple queries with logical operators.

### Must (AND)

All conditions must match.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.bool { b ->
                    b.must { m -> m.match { x -> x.field("title").query("tent") } }
                    b.must { m -> m.term { x -> x.field("category").value("shelter") } }
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": { "query": "tent" } } },
        { "term": { "category": { "value": "shelter" } } }
      ]
    }
  }
}
```

Only docs with "tent" in title AND category="shelter" match.

### Should (OR)

At least one condition must match (default behavior with no `must`).

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.bool { b ->
                    b.should { m -> m.match { x -> x.field("title").query("tent") } }
                    b.should { m -> m.match { x -> x.field("title").query("backpack") } }
                    b.minimumShouldMatch("1") // at least 1 should match
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "title": { "query": "tent" } } },
        { "match": { "title": { "query": "backpack" } } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

Returns docs matching "tent" OR "backpack".

### Filter (Non-Scoring Filter)

Conditions that must match but don't affect relevance score.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.bool { b ->
                    b.must { m -> m.match { x -> x.field("title").query("camping") } }
                    b.filter { m -> m.range { x ->
                        x.field("price")
                            .gte(50)
                            .lte(200)
                    } }
                    b.filter { m -> m.term { x -> x.field("in_stock").value(true) } }
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": { "query": "camping" } } }
      ],
      "filter": [
        { "range": { "price": { "gte": 50, "lte": 200 } } },
        { "term": { "in_stock": { "value": true } } }
      ]
    }
  }
}
```

Filters don't score; they're cached and fast. Use for exact-match filters and ranges.

### MustNot (NOT)

Exclude documents matching conditions.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.bool { b ->
                    b.must { m -> m.match { x -> x.field("title").query("tent") } }
                    b.mustNot { m -> m.term { x -> x.field("brand").value("unknown") } }
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": { "query": "tent" } } }
      ],
      "must_not": [
        { "term": { "brand": { "value": "unknown" } } }
      ]
    }
  }
}
```

Returns docs with "tent" in title, excluding those with brand="unknown".

### Complex Bool Query

Combine all clause types.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.bool { b ->
                    // Relevance match (scored)
                    b.must { m -> m.match { x -> x.field("title").query("camping") } }
                    b.should { m -> m.match { x -> x.field("description").query("4-season") } }

                    // Filters (not scored, cached)
                    b.filter { m -> m.range { x ->
                        x.field("price").gte(50).lte(200)
                    } }
                    b.filter { m -> m.term { x -> x.field("in_stock").value(true) } }

                    // Exclusions
                    b.mustNot { m -> m.term { x -> x.field("discontinued").value(true) } }

                    // Boost should clause
                    b.minimumShouldMatch("0") // 0 shoulds ok; "camping" must match
                }
            }
            .size(20)
    },
    ProductDocument::class.java
)
```

---

## Term & Range Queries

### Term Query

Exact match on a keyword field (no analysis).

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.term { t ->
                    t.field("brand").value("Coleman") // exact match
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "term": {
      "brand": { "value": "Coleman" }
    }
  }
}
```

**Important:** `term` doesn't analyze input. If you want case-insensitive term search, map field as keyword and store lowercased values, or use `match` instead.

### Terms Query

Match if field value is in a list.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.terms { t ->
                    t.field("category")
                        .value(listOf("Tents", "Backpacks", "Sleeping Bags"))
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "terms": {
      "category": {
        "value": ["Tents", "Backpacks", "Sleeping Bags"]
      }
    }
  }
}
```

Returns docs with category in the list.

### Range Query

Match values within a range.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.range { r ->
                    r.field("price")
                        .gte(50)
                        .lte(200)
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "range": {
      "price": {
        "gte": 50,
        "lte": 200
      }
    }
  }
}
```

**Operators:**
- `gte`: Greater than or equal
- `lte`: Less than or equal
- `gt`: Greater than
- `lt`: Less than
- `format`: For date fields, e.g., `format("yyyy-MM-dd")`
- `boost`: Relevance boost

### Range with Dates

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.range { r ->
                    r.field("created_at")
                        .gte(1704067200000L) // milliseconds since epoch
                        .lte(System.currentTimeMillis())
                }
            }
    },
    ProductDocument::class.java
)
```

Or with date math:

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.range { r ->
                    r.field("created_at")
                        .gte("now-30d")  // last 30 days
                        .lte("now")
                }
            }
    },
    ProductDocument::class.java
)
```

**Date math syntax:**
- `now`: Current moment
- `now-1h`: 1 hour ago
- `now-7d`: 7 days ago
- `now+1M`: 1 month from now
- `2025-01-01||+1d`: Jan 1 2025, plus 1 day

---

## Nested Document Queries

Nested documents allow querying related sub-objects.

### Nested Query

Find parent docs where a nested child matches criteria.

**Document structure:**
```kotlin
@Document(indexName = "products")
data class ProductWithReviews(
    @Id
    val id: String,
    val title: String,
    val reviews: List<Review> = emptyList()
)

data class Review(
    val rating: Int,
    val text: String,
    val reviewer: String
)
```

**Query:** Find products with 5-star reviews.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.nested { n ->
                    n.path("reviews")
                        .query { nq ->
                            nq.term { t ->
                                t.field("reviews.rating").value(5)
                            }
                        }
                }
            }
    },
    ProductWithReviews::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "nested": {
      "path": "reviews",
      "query": {
        "term": { "reviews.rating": { "value": 5 } }
      }
    }
  }
}
```

Returns product docs with at least one 5-star review.

### Nested with Multiple Conditions

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.nested { n ->
                    n.path("reviews")
                        .query { nq ->
                            nq.bool { b ->
                                b.must { m -> m.range { r ->
                                    r.field("reviews.rating").gte(4)
                                } }
                                b.must { m -> m.match { x ->
                                    x.field("reviews.text").query("excellent")
                                } }
                            }
                        }
                }
            }
    },
    ProductWithReviews::class.java
)
```

Returns products with reviews rated 4+ that mention "excellent".

### Nested with Aggregations

Count reviews per rating for matching products.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.match { m -> m.field("title").query("tent") }
            }
            .aggregations("reviews_by_rating") { agg ->
                agg.nested { n ->
                    n.path("reviews")
                }
                .aggregations("rating_distribution") { inner ->
                    inner.terms { t ->
                        t.field("reviews.rating").size(5)
                    }
                }
            }
    },
    ProductWithReviews::class.java
)
```

---

## Function Score

Apply custom scoring logic to boost/penalize results.

### Field Value Factor Boost

Boost score by a field value (e.g., popularity).

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.functionScore { fs ->
                    fs.query { subQ -> subQ.match { m ->
                        m.field("title").query("tent")
                    } }
                    fs.functions { f ->
                        f.fieldValueFactor { fvf ->
                            fvf.field("popularity")
                                .factor(1.2)
                                .modifier(Modifier.Log1p) // log(1 + popularity)
                        }
                    }
                    fs.scoreMode(FunctionScoreMode.Multiply)
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": { "query": "tent" } } },
      "functions": [
        {
          "field_value_factor": {
            "field": "popularity",
            "factor": 1.2,
            "modifier": "log1p"
          }
        }
      ],
      "score_mode": "multiply"
    }
  }
}
```

Multiplies relevance score by `log(1 + popularity)`.

### Decay Function (Geospatial)

Decrease score as location moves away from a point.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.functionScore { fs ->
                    fs.query { subQ -> subQ.matchAll { } }
                    fs.functions { f ->
                        f.gauss { g ->
                            g.field("location") // lat,lon field
                                .placement(
                                    "40.7128,-74.0060", // origin point (NYC)
                                    JsonData.fromRawJson("""{"lat":40.7128,"lon":-74.0060}""")
                                )
                                .scale("10km")  // distance where score halves
                                .offset("1km")  // distance before decay starts
                                .decay(0.5)     // score multiplier at scale distance
                        }
                    }
                    fs.scoreMode(FunctionScoreMode.Multiply)
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "function_score": {
      "query": { "match_all": {} },
      "functions": [
        {
          "gauss": {
            "location": {
              "origin": "40.7128,-74.0060",
              "scale": "10km",
              "offset": "1km",
              "decay": 0.5
            }
          }
        }
      ],
      "score_mode": "multiply"
    }
  }
}
```

Docs closer to origin get higher scores; decay within 10km radius.

### Conditional Boost (Random)

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.functionScore { fs ->
                    fs.query { subQ -> subQ.match { m ->
                        m.field("title").query("tent")
                    } }
                    fs.functions { f ->
                        f.randomScore { r ->
                            r.seed(System.currentTimeMillis())
                        }
                    }
                    fs.scoreMode(FunctionScoreMode.Multiply)
                }
            }
    },
    ProductDocument::class.java
)
```

Randomizes score for each query; useful for A/B testing or result rotation.

### Script Scoring

Apply a custom Painless script to compute score.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.functionScore { fs ->
                    fs.query { subQ -> subQ.match { m ->
                        m.field("title").query("camping")
                    } }
                    fs.functions { f ->
                        f.scriptScore { ss ->
                            ss.script { s ->
                                s.inline { i ->
                                    i.source("Math.log(2 + doc['popularity'].value)")
                                }
                            }
                        }
                    }
                }
            }
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "query": {
    "function_score": {
      "query": { "match": { "title": { "query": "camping" } } },
      "functions": [
        {
          "script_score": {
            "script": {
              "source": "Math.log(2 + doc['popularity'].value)"
            }
          }
        }
      ]
    }
  }
}
```

Powerful but slower than built-in functions. Use Painless for complex scoring.

---

## Aggregations

Aggregations compute statistics and group results.

### Terms Aggregation (Faceting)

Count occurrences of each unique field value.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.matchAll { } }
            .size(0) // don't return docs, only aggregations
            .aggregations("categories", { agg ->
                agg.terms { t ->
                    t.field("category")
                        .size(100) // return top 100 categories
                }
            })
    },
    ProductDocument::class.java
)

// Extract results
val categoriesAgg = response.aggregations()["categories"]
if (categoriesAgg != null) {
    val terms = categoriesAgg.sterms()
    terms.buckets().each { bucket ->
        println("${bucket.key()}: ${bucket.docCount()}")
    }
}
```

**Generated JSON:**
```json
{
  "query": { "match_all": {} },
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {
        "field": "category",
        "size": 100
      }
    }
  }
}
```

### Range Aggregation

Count documents in value ranges.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.matchAll { } }
            .size(0)
            .aggregations("price_ranges", { agg ->
                agg.range { r ->
                    r.field("price")
                    r.ranges { rng ->
                        rng.range { x -> x.to(50.0) }        // 0-50
                        rng.range { x -> x.from(50.0).to(100.0) } // 50-100
                        rng.range { x -> x.from(100.0).to(200.0) } // 100-200
                        rng.range { x -> x.from(200.0) }      // 200+
                    }
                }
            })
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 50 },
          { "from": 50, "to": 100 },
          { "from": 100, "to": 200 },
          { "from": 200 }
        ]
      }
    }
  }
}
```

### Date Histogram Aggregation

Count documents per time period.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.matchAll { } }
            .size(0)
            .aggregations("sales_per_month", { agg ->
                agg.dateHistogram { dh ->
                    dh.field("created_at")
                        .calendarInterval(CalendarInterval.Month)
                        .minDocCount(1)
                }
            })
    },
    ProductDocument::class.java
)

// Extract results
val histogram = response.aggregations()["sales_per_month"].dateHistogram()
histogram.buckets().each { bucket ->
    println("${bucket.key()}: ${bucket.docCount()}")
}
```

**Generated JSON:**
```json
{
  "aggs": {
    "sales_per_month": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "month",
        "min_doc_count": 1
      }
    }
  }
}
```

### Sub-Aggregations (Nested Aggregations)

Aggregate within aggregations.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.matchAll { } }
            .size(0)
            .aggregations("by_category", { agg ->
                agg.terms { t -> t.field("category").size(50) }
                    .aggregations("avg_price", { subAgg ->
                        subAgg.avg { a -> a.field("price") }
                    })
                    .aggregations("price_range", { subAgg ->
                        subAgg.range { r ->
                            r.field("price")
                            r.ranges { rng ->
                                rng.range { x -> x.to(50.0) }
                                rng.range { x -> x.from(50.0).to(200.0) }
                                rng.range { x -> x.from(200.0) }
                            }
                        }
                    })
            })
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "aggs": {
    "by_category": {
      "terms": { "field": "category", "size": 50 },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } },
        "price_range": {
          "range": { "field": "price", "ranges": [...] }
        }
      }
    }
  }
}
```

Returns average price and price distribution per category.

### Stats Aggregation

Calculate multiple stats at once.

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.term { t -> t.field("category").value("Tents") } }
            .size(0)
            .aggregations("price_stats", { agg ->
                agg.stats { s -> s.field("price") }
            })
    },
    ProductDocument::class.java
)

val stats = response.aggregations()["price_stats"].statsAggregate()
println("Count: ${stats.count()}")
println("Min: ${stats.min()}")
println("Max: ${stats.max()}")
println("Avg: ${stats.avg()}")
println("Sum: ${stats.sum()}")
```

**Generated JSON:**
```json
{
  "aggs": {
    "price_stats": {
      "stats": { "field": "price" }
    }
  }
}
```

Returns count, min, max, avg, sum in a single aggregation.

---

## Highlighting

Return snippets with matching terms highlighted.

### Basic Highlighting

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.match { m -> m.field("description").query("waterproof durable") }
            }
            .highlight { h ->
                h.fields("description", { f -> f.fragmentSize(150) })
                h.preTags("<mark>")
                h.postTags("</mark>")
            }
            .size(10)
    },
    ProductDocument::class.java
)

response.hits().hits().forEach { hit ->
    val doc = hit.source()!!
    val highlights = hit.highlight()
    highlights?.forEach { (field, fragments) ->
        println("$field: ${fragments.joinToString("...")}")
    }
}
```

**Generated JSON:**
```json
{
  "query": { "match": { "description": { "query": "waterproof durable" } } },
  "highlight": {
    "fields": { "description": { "fragment_size": 150 } },
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"]
  }
}
```

### Highlight with Number of Fragments

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q ->
                q.match { m -> m.field("description").query("tent") }
            }
            .highlight { h ->
                h.fields("description", { f ->
                    f.fragmentSize(200)
                    f.numberOfFragments(3) // return up to 3 snippets
                })
            }
    },
    ProductDocument::class.java
)
```

Returns up to 3 fragments (snippets) from description field, each up to 200 characters.

---

## Pagination with Search After

For deep pagination, `search_after` is more efficient than `from`/`size`.

### Setup: Sort + Search After

```kotlin
var searchAfter: Array<Any>? = null
val pageSize = 20

// First page
var response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.matchAll { } }
            .sort { s -> s.field { f -> f.field("id").order(SortOrder.Asc) } }
            .size(pageSize)
    },
    ProductDocument::class.java
)

var hits = response.hits().hits()
hits.forEach { hit -> println(hit.source()) }

// Get sort values from last doc
if (hits.isNotEmpty()) {
    searchAfter = hits.last().sort()?.toTypedArray() ?: arrayOf(hits.last().id())
}

// Subsequent pages
while (hits.isNotEmpty()) {
    response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q -> q.matchAll { } }
                .sort { s -> s.field { f -> f.field("id").order(SortOrder.Asc) } }
                .size(pageSize)
                .searchAfter(searchAfter?.toList() ?: emptyList())
        },
        ProductDocument::class.java
    )

    hits = response.hits().hits()
    hits.forEach { hit -> println(hit.source()) }

    if (hits.isNotEmpty()) {
        searchAfter = hits.last().sort()?.toTypedArray() ?: arrayOf(hits.last().id())
    }
}
```

**Generated JSON (subsequent pages):**
```json
{
  "query": { "match_all": {} },
  "sort": [{ "id": "asc" }],
  "size": 20,
  "search_after": ["product-123"]
}
```

**Why `search_after` is better:**
- `from` + `size`: Must skip N documents (expensive for large offsets)
- `search_after`: Continues from last position using sort values (O(1) vs O(N))

---

## Source Filtering

Control which fields are returned in results.

### Include Only Specific Fields

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.match { m -> m.field("title").query("tent") } }
            .source { s ->
                s.includes("id", "title", "price", "brand") // only these fields
            }
            .size(10)
    },
    ProductDocument::class.java
)

response.hits().hits().forEach { hit ->
    // Only id, title, price, brand are present; other fields are null
    println("${hit.source()!!.id}: ${hit.source()!!.title}")
}
```

**Generated JSON:**
```json
{
  "query": { "match": { "title": { "query": "tent" } } },
  "_source": ["id", "title", "price", "brand"]
}
```

### Exclude Specific Fields

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.match { m -> m.field("title").query("tent") } }
            .source { s ->
                s.excludes("description", "reviews") // exclude large fields
            }
            .size(10)
    },
    ProductDocument::class.java
)
```

**Generated JSON:**
```json
{
  "_source": {
    "excludes": ["description", "reviews"]
  }
}
```

### Disable Source

For minimal response size (only ID returned):

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.match { m -> m.field("title").query("tent") } }
            .source(false) // don't return source at all
            .size(10)
    },
    Void::class.java // No document class needed
)

response.hits().hits().forEach { hit ->
    println("ID: ${hit.id()}") // Only ID available
}
```

---

## Practical Examples

### E-Commerce Product Search

Find camping gear with facets and sorting.

```kotlin
data class SearchRequest(
    val query: String,
    val minPrice: Double? = null,
    val maxPrice: Double? = null,
    val categories: List<String> = emptyList(),
    val inStockOnly: Boolean = true,
    val sortBy: String = "relevance", // relevance, price_asc, price_desc, newest
    val pageSize: Int = 20,
    val pageNumber: Int = 1
)

fun searchCampingGear(request: SearchRequest): SearchResponse {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q ->
                    q.bool { b ->
                        // Full-text search on title + description
                        b.must { m -> m.multiMatch { mm ->
                            mm.query(request.query)
                                .fields("title^3,description")
                                .type(TextQueryType.BestFields)
                        } }

                        // Filter by price range
                        if (request.minPrice != null || request.maxPrice != null) {
                            b.filter { m -> m.range { r ->
                                r.field("price")
                                if (request.minPrice != null) r.gte(request.minPrice)
                                if (request.maxPrice != null) r.lte(request.maxPrice)
                            } }
                        }

                        // Filter by categories
                        if (request.categories.isNotEmpty()) {
                            b.filter { m -> m.terms { t ->
                                t.field("category").value(request.categories)
                            } }
                        }

                        // Filter to in-stock items
                        if (request.inStockOnly) {
                            b.filter { m -> m.term { t ->
                                t.field("in_stock").value(true)
                            } }
                        }
                    }
                }

                // Sorting
                when (request.sortBy) {
                    "price_asc" -> req.sort { s ->
                        s.field { f -> f.field("price").order(SortOrder.Asc) }
                    }
                    "price_desc" -> req.sort { s ->
                        s.field { f -> f.field("price").order(SortOrder.Desc) }
                    }
                    "newest" -> req.sort { s ->
                        s.field { f -> f.field("created_at").order(SortOrder.Desc) }
                    }
                    else -> req.sort { s -> // relevance (default)
                        s.score { f -> f.order(SortOrder.Desc) }
                    }
                }

                // Pagination
                req.size(request.pageSize)
                req.from((request.pageNumber - 1) * request.pageSize)

                // Facets
                req.aggregations("categories", { agg ->
                    agg.terms { t -> t.field("category").size(50) }
                })
                req.aggregations("price_ranges", { agg ->
                    agg.range { r ->
                        r.field("price")
                        r.ranges { rng ->
                            rng.range { x -> x.to(50.0) }
                            rng.range { x -> x.from(50.0).to(100.0) }
                            rng.range { x -> x.from(100.0).to(200.0) }
                            rng.range { x -> x.from(200.0) }
                        }
                    }
                })
                req.aggregations("brands", { agg ->
                    agg.terms { t -> t.field("brand").size(100) }
                })
        },
        ProductDocument::class.java
    )

    return SearchResponse(
        hits = response.hits().hits().mapNotNull { it.source() },
        totalHits = response.hits().total()?.value() ?: 0L,
        facets = extractFacets(response)
    )
}

data class SearchResponse(
    val hits: List<ProductDocument>,
    val totalHits: Long,
    val facets: Map<String, List<Facet>>
)

data class Facet(
    val name: String,
    val count: Long
)
```

### Geo-proximity Search (Nearest Stores)

Find stores within radius, sorted by distance.

```kotlin
fun findNearbyStores(latitude: Double, longitude: Double, radiusKm: Int = 10): List<Store> {
    val response = openSearchClient.search(
        { req ->
            req.index("stores")
                .query { q ->
                    q.bool { b ->
                        b.filter { m -> m.geoDistance { g ->
                            g.field("location")
                                .location { l -> l.lat(latitude).lon(longitude) }
                                .distance("${radiusKm}km")
                        } }
                    }
                }
                .sort { s ->
                    s.geoDistance { g ->
                        g.field("location")
                            .location { l -> l.lat(latitude).lon(longitude) }
                            .order(SortOrder.Asc)
                            .unit(DistanceUnit.Kilometers)
                    }
                }
                .size(20)
        },
        Store::class.java
    )

    return response.hits().hits().mapNotNull { it.source() }
}

data class Store(
    @Id val id: String,
    val name: String,
    val location: String, // "latitude,longitude"
    val address: String
)
```

### Auto-suggest (Prefix Matching)

Implement type-ahead with ngrams.

```kotlin
fun getSuggestions(prefix: String, limit: Int = 10): List<String> {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q ->
                    q.match { m ->
                        m.field("title_ngram") // Field indexed with EdgeNGram analyzer
                            .query(prefix)
                            .operator(Operator.And)
                    }
                }
                .size(0) // Don't need docs, just aggregations
                .aggregations("suggestions", { agg ->
                    agg.terms { t ->
                        t.field("title")
                            .size(limit)
                    }
                })
        },
        ProductDocument::class.java
    )

    val terms = response.aggregations()["suggestions"].sterms()
    return terms.buckets().map { it.key() }
}
```

---

## Summary

**OpenSearch Query DSL strengths:**
- Comprehensive bool query for complex logic
- Aggregations are powerful for analytics
- Function scoring allows flexible relevance tuning
- Nested queries handle hierarchical data elegantly

**Kotlin-specific tips:**
- Use builder API for type safety
- Handle null safely in aggregate responses
- Pagination via `search_after` for large offsets
- Filter context (vs query context) for non-scored filtering

**Performance considerations:**
- Use filter context for repeatable conditions (cached)
- Aggregations: Set `size: 0` to skip returning docs
- Highlighting adds overhead; use sparingly
- Deep pagination with `from`/`size` is slow; use `search_after`
