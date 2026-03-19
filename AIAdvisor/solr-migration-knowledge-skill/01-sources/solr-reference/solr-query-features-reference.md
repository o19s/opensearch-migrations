# Solr Query Features: Comprehensive Reference

## Table of Contents
1. [Request Handlers](#request-handlers)
2. [Query Parsers Overview](#query-parsers-overview)
3. [DisMax Parser](#dismax-parser)
4. [eDisMax Parser](#edismax-parser)
5. [Lucene/Standard Parser](#lucenesandard-parser)
6. [Common Query Parameters](#common-query-parameters)
7. [Faceting](#faceting)
8. [Grouping & Collapsing](#grouping--collapsing)
9. [Joins & Nested Documents](#joins--nested-documents)
10. [Spatial & Geospatial Queries](#spatial--geospatial-queries)
11. [Advanced Features](#advanced-features)
12. [Atomic Updates & Optimistic Concurrency](#atomic-updates--optimistic-concurrency)

---

## Request Handlers

Request handlers are Solr components that process incoming HTTP requests. They're defined in `solrconfig.xml` and mapped to URL paths.

### /select (Standard Query Handler)

The most common handler for search queries. Executes in query mode.

**Definition:**
```xml
<requestHandler name="/select" class="solr.SearchHandler">
  <lst name="defaults">
    <str name="echoParams">explicit</str>
    <int name="rows">10</int>
  </lst>
</requestHandler>
```

**Usage:** `GET /solr/mycore/select?q=foo&fq=category:bar`

**Features:**
- Accepts all standard query parameters (q, fq, sort, facet, etc.)
- Executes configured query parsers
- Applies update processors? No; this is read-only
- Response format: JSON (default), XML, or custom

### /query (Newer Standard Handler)

In modern Solr (7.0+), `/query` is preferred over `/select`. It's identical in functionality but better aligns with naming conventions.

### /update (Update Handler)

Processes document additions, updates, and deletions. Operates in update mode.

**Definition:**
```xml
<requestHandler name="/update" class="solr.UpdateRequestHandler">
  <lst name="defaults">
    <str name="update.chain">default</str>
  </lst>
</requestHandler>
```

**Accepted formats:**
- JSON: `POST /update -d '{"add":{"doc":{"id":"1","title":"foo"}}}'`
- XML: `POST /update -d '<add><doc><field name="id">1</field></doc></add>'`
- CSV: `POST /update/csv -d 'id,title\n1,foo'`

**Key parameters:**
- `commit=true`: Hard commit after updates
- `softCommit=true`: Soft commit (visible to searches, not durable)
- `commitWithin=5000`: Hard commit within 5 seconds if another request triggers it first
- `overwrite=false`: Add documents without checking for duplicates (faster, but allows duplicates)

### Custom Request Handlers

You can define custom handlers for domain-specific logic:

```xml
<requestHandler name="/suggestions" class="com.example.SuggestionHandler">
  <lst name="defaults">
    <str name="suggest.field">product_name</str>
  </lst>
</requestHandler>
```

Custom handlers can:
- Invoke custom query parsers
- Apply custom response formatting
- Chain multiple components
- Implement business logic (e.g., personalization, A/B testing)

---

## Query Parsers Overview

A query parser interprets the user-provided query string (`q` parameter) and converts it into a Lucene `Query` object.

### Parser Selection

Specify parser via `defType` parameter:
```
GET /select?q=foo&defType=edismax
GET /select?q=title:foo&defType=lucene
GET /select?q=foo+bar&defType=dismax
```

### Response to Parser Errors

If a query is malformed:
- **Strict mode (default)**: Returns error 400 with message
- **Lenient mode**: Ignores invalid parts, returns partial results

Enable lenient mode: `?q=foo bar&defType=edismax&sow=true`

---

## DisMax Parser

**DisMax** (Disjunction Max) is designed for user-facing search. It's lenient with syntax and searches multiple fields.

### Core Concept

DisMax doesn't support AND/OR operators or phrase syntax. Instead:
- Treats input as a bag of keywords
- Scores documents if they match _any_ keyword
- Supports "disjunction max" scoring: score is the max of individual field scores, not sum

### Key Parameters

#### qf (Query Fields)
Specifies which fields to search and their boost weights.

```
q=laptop&qf=title^2 description category
```

Searches title with 2x boost, description and category with 1x boost. Solr adds a match to whichever field has highest score.

**Boost syntax:**
- `^2`: Double the relevance of that field
- `^0.5`: Halve the relevance
- Fractional boosts are common for less-important fields

#### mm (Minimum Match)

How many query terms must match for a document to be returned.

```
q=laptop for work&mm=2
```

Document must match at least 2 of [laptop, for, work]. Useful for recall/precision tuning.

**Syntax:**
- `mm=2`: Exactly 2 terms
- `mm=75%`: At least 75% of terms (rounds intelligently)
- `mm=1<-25%`: 1 term for 1-word queries, -25% (reduce by 25%) for longer queries

#### pf (Phrase Boost)

Boosts documents where query terms appear as a phrase.

```
q=machine learning&qf=title description&pf=title^3
```

- Title is searched for "machine" and "learning" individually
- If title contains phrase "machine learning", apply additional 3x boost
- Encourages phrase matches without requiring them

#### pf2 & pf3 (Bigram & Trigram Boost)

Boosts documents where terms appear close together.

```
q=distributed database system&pf2=title^2&pf3=description^1.5
```

- `pf2`: Boost if terms appear within a 2-word span (bigram)
- `pf3`: Boost if terms appear within a 3-word span (trigram)
- Useful for favoring proximity without strict phrase requirement

#### ps (Phrase Slop)

Controls how far apart words in a phrase can be.

```
q=machine learning&qf=title&pf=title&ps=2
```

Phrase "machine learning" matches "machine deep learning" (slop=1) and "machine neural deep learning" (slop=2), but not farther apart.

#### tie (Tie Breaker)

When multiple fields match with equal score, `tie` determines how much to add from other fields' scores.

```
q=laptop&qf=title^2 description&tie=0.1
```

- `tie=0` (default): Score is max(title_score, description_score)
- `tie=0.5`: Score is max + 0.5 * sum of other scores
- `tie=1`: Score is sum of all scores (becomes SHOULD, not MUST)

Use tie > 0 when you want all field matches to contribute slightly.

#### bq (Boost Query)

Apply a multiplier to documents matching an arbitrary query.

```
q=laptop&bq=in_stock:true^2&bq=category:gaming^1.5
```

Matching `in_stock:true` multiplies score by 2; matching `category:gaming` multiplies by 1.5. Non-matching documents unaffected.

#### bf (Boost Function)

Apply a function to boost scores.

```
q=laptop&bf=log(1+popularity)^0.5
```

For each matching document, multiply score by `log(1+popularity)^0.5`. Useful for popularity biasing.

**Common functions:**
- `log(field)`: Logarithmic scaling
- `sqrt(field)`: Square root scaling
- `1/(1+field)`: Inverse scaling
- `if(field>10,2,1)`: Conditional boost
- `field1 * field2`: Multiplication

#### is (Default Query)

If user provides no query, use this default.

```
GET /select?is=*:*
```

Useful for faceting and result sets when query is optional.

### DisMax Example

```
GET /select?
  q=camping+gear&
  defType=dismax&
  qf=title^3+description+reviews&
  mm=1&
  pf=title^2&
  tie=0.1&
  bq=in_stock:true^2&
  bf=log(popularity)&
  rows=20
```

---

## eDisMax Parser

**eDisMax** (Extended DisMax) is an enhanced version of DisMax with more features and better syntax support.

### Features Over DisMax

eDisMax supports:
- Wildcard queries: `camp*`
- Range queries: `price:[10 TO 100]`
- Boolean operators (optional): `camping AND gear` or `camping OR tent`
- Negative terms: `-tent` (exclude tent)
- Phrase queries: `"camping gear"`
- Field-specific queries: `title:tent`

### Additional Parameters

#### uf (User Fields)

Which fields users are allowed to search directly (e.g., `title:foo`). Security control.

```
GET /select?q=title:camping&uf=title+description+-id
```

- `uf=title description`: Allow searching these fields
- `uf=*`: Allow all fields (default, risky if you have secret fields)
- `uf=* -secret_field`: Allow all except secret_field
- `uf=title description -price`: Whitelist some, blacklist one

#### lowercaseOperators

By default, eDisMax requires uppercase boolean operators: `camping AND gear`. Set `lowercaseOperators=true` to allow lowercase: `camping and gear`.

```
GET /select?q=camping+and+gear&lowercaseOperators=true
```

#### sow (Split on Whitespace)

Controls how whitespace splits query terms.

```
GET /select?q=camping+gear&sow=true
```

- `sow=true`: Each whitespace-separated token is a separate term (safer; prevents phrase collisions)
- `sow=false` (default): Tries to recognize phrases and operators

#### autoRelaxMM

Automatically relax `mm` if it's too strict.

```
GET /select?q=camping+equipment+gear&mm=100%&autoRelaxMM=true
```

If 100% match fails (all three terms required), try 66%, then 33%, then return any match. Balances precision with recall.

#### boost & boost2

Similar to `bf` but more explicit in eDisMax.

```
GET /select?q=camping&boost=log(popularity)&boost2=if(in_stock:true,2,1)
```

Apply boost functions in order.

### eDisMax Example

```
GET /select?
  q=camping+gear+-rain&
  defType=edismax&
  qf=title^3+description&
  uf=title+description+-id&
  mm=2&
  pf=title^2&
  tie=0.2&
  bq=in_stock:true^2&
  autoRelaxMM=true&
  lowercaseOperators=true&
  rows=20
```

---

## Lucene/Standard Parser

The Lucene (or "Standard") parser implements Lucene query syntax directly. It's strict and powerful.

### Basic Syntax

#### Term Query
```
q=camping
```
Matches documents with term "camping" in default field.

#### Boolean Operators
```
q=camping AND gear
q=camping OR tent
q=camping NOT (rain OR cold)
```

AND is default (implicit): `camping gear` = `camping AND gear`

#### Field-Specific Search
```
q=title:camping
q=author:"John Doe"
```

#### Phrase Query
```
q="camping gear"
```
Matches documents with exact phrase.

#### Wildcard
```
q=camp*
q=te?t
```

`*` = multiple characters, `?` = single character. (Note: `*` at start is slow; most Solr deployments disable it.)

#### Range Query
```
q=price:[10 TO 100]
q=date:[2020-01-01 TO 2023-12-31]
```

`[...]` = inclusive, `{...}` = exclusive

#### Fuzzy Search
```
q=campng~
q=campng~1
```

`~` enables fuzzy matching; `~N` sets edit distance.

#### Proximity
```
q="camping gear"~2
```

Terms "camping" and "gear" within 2 words.

#### Boost
```
q=camping^2 tent^0.5
```

Boost individual terms.

#### Grouping
```
q=(camping OR hiking) AND gear
```

### Parameters

#### defaultOperator

Default operator between terms if not specified.

```
q=camping gear&defaultOperator=AND   (matches both terms; default)
q=camping gear&defaultOperator=OR    (matches either term)
```

#### df (Default Field)

Which field to search if no field is specified.

```
q=camping&df=title  (searches title field)
q=camping&df=content
```

#### lenient

Ignore syntax errors and return partial results instead of error.

```
q=camping [broken syntax&lenient=true
```

---

## Common Query Parameters

These parameters work across all query parsers.

### q (Query)

The actual search query.

```
q=camping
q=title:camping AND price:[10 TO 100]
q=*:*   (match all)
```

### fq (Filter Query)

Filters results without affecting relevance scores. Multiple fq parameters are combined with AND.

```
q=camping&fq=category:gear&fq=in_stock:true
```

Returns documents matching "camping" AND in category gear AND in stock. Score is based on "camping" only.

**Performance note:** Filters are cached; use them for high-selectivity, repeatable queries (e.g., status, category). Don't use for low-selectivity or per-user filters.

### fl (Field List)

Which fields to return in results.

```
q=camping&fl=id,title,price
q=camping&fl=*    (all fields)
q=camping&fl=id,title,score   (include relevance score)
```

### sort

Order results by one or more fields.

```
q=camping&sort=price asc
q=camping&sort=popularity desc,price asc
q=camping&sort=score desc   (default; sort by relevance)
```

### start & rows

Pagination.

```
q=camping&start=0&rows=10     (first 10 results)
q=camping&start=10&rows=10    (second page)
```

**Warning:** Deep pagination (start > 100000) is expensive; consider cursor-based pagination (search_after) for large offsets.

### facet

Enable faceting; group results by field values.

```
q=camping&facet=true&facet.field=category&facet.field=color
```

Returns facet counts for each field.

### hl (Highlighting)

Return highlighted snippets of matching text.

```
q=camping+gear&hl=true&hl.fl=title,description
```

Returns `<em>` tags around matching terms.

### spellcheck

Return spelling suggestions.

```
q=campign&spellcheck=true
```

If "campign" is misspelled, suggests "camping".

### mlt (More Like This)

Find similar documents.

```
q=id:123&mlt=true&mlt.fl=title,description&mlt.mindf=1
```

Uses document 123 as template; finds docs with similar terms in title/description.

### stats

Calculate statistics (min, max, avg, sum) on numeric fields.

```
q=camping&stats=true&stats.field=price&stats.field=rating
```

Returns min/max/avg for price and rating across results.

### group

Group results by field value; return one representative doc per group.

```
q=camping&group=true&group.field=brand&group.limit=2
```

See [Grouping & Collapsing](#grouping--collapsing) section for details.

### wt (Writer Type)

Response format.

```
q=camping&wt=json   (JSON; default)
q=camping&wt=xml
q=camping&wt=csv
```

---

## Faceting

Faceting groups results by field values and returns counts. Useful for navigation, filtering, and analytics.

### Field Facet

Count occurrences of each unique value in a field.

```
GET /select?q=camping&facet=true&facet.field=category&facet.field=brand
```

**Response:**
```json
{
  "response": { "numFound": 100, "docs": [...] },
  "facet_counts": {
    "facet_fields": {
      "category": [
        "Tents", 45,
        "Backpacks", 30,
        "Gear", 25
      ],
      "brand": [
        "Coleman", 35,
        "REI", 28,
        ...
      ]
    }
  }
}
```

### Range Facet

Count documents in ranges of a numeric field.

```
GET /select?q=camping&facet=true&facet.range=price&facet.range.start=0&facet.range.end=1000&facet.range.gap=100
```

Returns counts for price ranges [0-100), [100-200), ..., [900-1000).

### Date Facet

Count documents by time period.

```
GET /select?q=camping&facet=true&facet.range=publish_date&facet.range.start=2020-01-01T00:00:00Z&facet.range.end=2025-01-01T00:00:00Z&facet.range.gap=+1MONTH
```

Returns counts per month. `+1MONTH`, `+1YEAR`, `+1DAY` are common gaps.

### Pivot Facet

Hierarchical faceting: group by field A, then within each group, group by field B.

```
GET /select?q=camping&facet=true&facet.pivot=category,brand
```

**Response:**
```json
{
  "facet_counts": {
    "facet_pivot": {
      "category,brand": [
        {
          "field": "category",
          "value": "Tents",
          "count": 45,
          "pivot": [
            { "field": "brand", "value": "Coleman", "count": 25 },
            { "field": "brand", "value": "REI", "count": 20 }
          ]
        },
        ...
      ]
    }
  }
}
```

### facet.method (Field Facet Performance)

Two algorithms for field faceting:

#### enum (Enumeration)
- Iterates over each unique field value
- Fast when field has few unique values (< 1000)
- Slow when field has many unique values

#### fc (Field Cache)
- Uses Lucene FieldCache or DocValues
- Fast when field has many unique values
- Default in modern Solr

```
GET /select?facet=true&facet.field=brand&facet.method=fc
```

**Rule of thumb:**
- `<1000 unique values` or `frequent faceting`: use `enum`
- `>10000 unique values` or `rare faceting`: use `fc` (default)

### facet.mincount

Exclude facet values with counts below threshold.

```
GET /select?facet=true&facet.field=category&facet.mincount=5
```

Returns only categories with 5+ documents. Reduces facet clutter.

---

## Grouping & Collapsing

### Grouping (group=true)

Returns a subset of results, grouped by a field, with representative docs from each group.

```
GET /select?q=laptop&group=true&group.field=brand&group.limit=3&rows=10
```

Returns up to 10 groups (brands), each with up to 3 docs. Useful for showing diverse results.

#### group.field

Field to group by. Only one per query (vs. facet, which can be multi-valued).

```
group.field=brand
group.field=category
```

#### group.func

Group by function result instead of field value.

```
group.func=sqrt(price)
```

Groups docs by rounded square root of price.

#### group.query

Group by results of arbitrary query.

```
group.query=price:[0 TO 100]&group.query=price:[100 TO 500]
```

Returns docs in first price range, then in second. Useful for custom groupings.

#### group.limit

How many docs to return per group.

```
group.limit=3   (return 3 docs per group)
```

#### group.offset

Offset within each group.

```
group.limit=3&group.offset=1   (skip first doc, return next 3 per group)
```

#### group.format

How to structure grouped results.

```
group.format=grouped   (nested structure; default)
group.format=simple    (flat list with grouping metadata)
```

### Collapsing (CollapsingQParserPlugin)

A lightweight alternative to grouping. Removes duplicate docs (per field value) during search.

```
q=laptop&defType=edismax&fq={!collapse field=brand}&rows=10
```

Returns at most 10 distinct brands, one doc per brand (the highest-scoring doc). Less flexible than grouping, but faster.

#### Collapse with Expansion

Expand collapsed docs to show alternates.

```
q=laptop&fq={!collapse field=brand expand.rows=3}&rows=10
```

Returns 10 groups (brands), but provides up to 3 docs per brand in a separate `expanded` section for display.

---

## Joins & Nested Documents

### Solr Join (join Query Parser)

Join documents from two collections based on a shared field.

```
GET /solr/products/select?
  q={!join from=product_id to=id fromIndex=inventory}in_stock:true&
  rows=20
```

Returns products where `product_id` matches documents in the inventory collection with `in_stock:true`.

**Use case:** Distributed schemas across multiple collections; link via shared ID.

**Limitations:**
- Slower than nested documents (requires two queries)
- Only works for equality joins
- fromIndex must be searchable by the current node

### Nested Documents (Block Join)

Store parent and child documents as a single block in the index. Children inherit parent's routing (shard assignment).

**Indexing nested docs:**
```json
{
  "id": "product-1",
  "title": "Tent",
  "reviews": [
    { "id": "review-1", "rating": 5, "text": "Great!" },
    { "id": "review-2", "rating": 4, "text": "Good" }
  ]
}
```

If using managed schema, declare reviews as nested:
```xml
<field name="reviews" type="object" stored="true" />
```

**toParent Query (child to parent):**

Find products with high-rated reviews.

```
GET /select?q={!parent which="type:product"}rating:5
```

Returns product docs where at least one review has rating=5.

**toChild Query (parent to child):**

Find reviews for expensive products.

```
GET /select?q={!child parentFilter="price:[500 TO *]"}rating:4
```

Returns review docs whose parent product has price >= 500 and review has rating=4.

**Aggregating nested docs:**

```
GET /select?
  q=type:product&
  fl=id,title&
  child.fl=review_id,rating,text&
  rows=10
```

Returns products with nested review data in the response.

---

## Spatial & Geospatial Queries

### Field Types

#### LatLonPointSpatialField

Modern (preferred) spatial field using geohashing. Efficient for proximity and range queries.

```xml
<field name="location" type="location" indexed="true" stored="true" />
<fieldType name="location" class="solr.LatLonPointSpatialField" />
```

Store as: `"location": "40.7128,-74.0060"` (latitude,longitude)

#### RPT (Recursive Prefix Tree)

More flexible spatial field supporting complex shapes, polygons, etc.

```xml
<fieldType name="location_rpt" class="solr.SpatialRecursivePrefixTreeFieldType"
  spatialContextFactory="org.locationtech.spatial4j.context.SpatialContextFactory"
  distErrPct="0.025" />
```

### Spatial Queries

#### Proximity (radius) Query

Find points within N km/miles of a location.

```
GET /select?
  q=*:*&
  fq={!geofilt sfield=location pt=40.7128,-74.0060 d=10 units=kilometers}
```

Returns documents within 10km of Times Square (40.7128,-74.0060).

#### Bounding Box

Find points within a lat/lon rectangle.

```
GET /select?
  q=*:*&
  fq={!bbox sfield=location minX=-74.2 maxX=-73.8 minY=40.6 maxY=40.8}
```

#### Distance Sorting

Sort results by distance from a point.

```
GET /select?
  q=restaurant&
  sort=geodist() asc&
  sfield=location&
  pt=40.7128,-74.0060
```

The `geodist()` function calculates distance from `pt`; sort by ascending distance.

#### Distance in Score

Boost score by proximity.

```
GET /select?
  q=restaurant&
  bf=exp(div(geodist(sfield=location,pt=40.7128\\,-74.0060),50))^2&
  rows=20
```

Uses exponential decay: docs closer to the pt get higher scores.

---

## Advanced Features

### Streaming Expressions & Export Handler

For very large result sets (millions of docs), cursor-based pagination or streaming is more efficient than traditional pagination.

#### Export Handler

Exports all matching documents as CSV without pagination overhead.

```
GET /select?
  q=category:camping&
  wt=csv&
  fl=id,title,price&
  rows=1000000
```

Solr streams results directly, avoiding memory buildup.

#### Streaming Expressions

Declarative language for complex, multi-stage data processing.

```
GET /stream?expr=
  search(
    collection1,
    q="category:camping",
    fl="id,title,price",
    sort="price asc",
    rows=10000
  )
```

Common streaming operations: `sort`, `facet`, `group`, `join`, `merge`.

### Real-Time Get (RTG)

Retrieve a document by ID without query overhead. Reads from both the searcher and the transaction log.

```
GET /select?q=id:product-123&realtime=true
```

or

```
GET /{collection}/get?id=product-123
```

Returns the doc even if it's only in the tlog (not yet committed to index). Useful for verifying writes or debugging.

### Atomic Updates

Update specific fields of a document without reindexing the entire doc.

#### Update Modifiers

- `set`: Set field to new value(s)
- `add`: Add to numeric field or append to multiValued field
- `remove`: Remove value(s) from multiValued field
- `inc`: Increment numeric field

```json
POST /update
{
  "add": {
    "doc": {
      "id": "product-123",
      "inventory": { "inc": -5 },
      "last_updated": { "set": "2025-03-17T10:30:00Z" },
      "tags": { "add": ["clearance", "limited-stock"] }
    }
  }
}
```

Decrements inventory by 5, sets last_updated, adds two tags. Other fields unchanged.

#### Requirements for Atomic Updates

- All fields must be `stored=true`
- `_version_` field must be present (for optimistic locking)
- Single-threaded per document (Solr locks on doc ID)

### Optimistic Concurrency (_version_ Field)

The `_version_` field tracks document update count. Use it to prevent lost updates.

**Without optimistic concurrency (risky):**
1. Client A reads doc (no version)
2. Client B reads same doc
3. Client A updates and writes (version is now 1)
4. Client B updates and writes, overwriting A's changes (version is now 2)

**With optimistic concurrency:**
```json
POST /update
{
  "add": {
    "doc": {
      "id": "product-123",
      "title": "New Title",
      "_version_": 5
    },
    "overwrite": false
  }
}
```

If current `_version_` is not 5, update fails (409 Conflict). Client B retries, reads the new version, and re-applies changes.

---

## Migration Mapping: Solr ↔ OpenSearch

| Feature | Solr | OpenSearch |
|---------|------|-----------|
| Field boost | qf param in DisMax | boost in mapping or query DSL |
| Phrase boost | pf, pf2, pf3 params | match_phrase with boost |
| Minimum match | mm param | minimum_should_match |
| Filtering | fq param | bool filter clause |
| Faceting | facet=true, facet.field | aggregations (terms, range, date_histogram) |
| Grouping | group.field, group.limit | collapse with expand or top_hits agg |
| Highlighting | hl=true, hl.fl | highlight block |
| Spatial | geofilt, bbox | geo_distance filter, geo_distance_sort |
| Atomic updates | update modifiers (set, add) | partial update via _update API |
| Nested docs | toParent, toChild | nested query, nested aggregations |

---

## Summary for Migration

**Solr's query strength:**
- DisMax/eDisMax are mature, production-tested for user-facing search
- Phrase boosting (`pf`, `pf2`, `pf3`) is more explicit than OpenSearch
- Grouping and faceting are tightly integrated
- Spatial queries are feature-complete

**Migration considerations:**
- DisMax → eDisMax by enabling user field specification and relaxing syntax
- eDisMax → OpenSearch Query DSL requires translating params to bool/filter structure
- Faceting → Aggregations; syntax is different but expressiveness is similar
- Atomic updates exist in both, but Solr's modifiers are more granular
- Streaming expressions have no direct OpenSearch equivalent; consider bulk processing instead
