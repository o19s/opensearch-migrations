# Solr Integrated Request Test Shapes

Date: 2026-03-23

This note captures the request shapes OSC should keep asking for as the upstream Solr
query-translation work evolves.

The point is simple:

- parameter-by-parameter progress is useful
- but production migration risk usually appears in combined requests

So these examples are designed to test integrated behavior, not isolated feature support.

## Why These Matter

A migration effort can look healthy if it has separate support for:

- `q`
- `fq`
- sort
- facets
- highlighting

and still drift materially in production once those features are combined in a single request.

OSC should keep pushing for integrated test cases because that is where:

- ranking drift
- document-set drift
- faceting-context mistakes
- unsupported-feature ambiguity

actually show up.

## Test Shape 1: Basic Search + Filter

**Solr shape**

```text
q=title:java&fq=status:active
```

What it checks:

- `q` remains the scoring/query clause
- `fq` remains non-scoring filter context
- candidate set narrowing is clear and explicit

Why it matters:

- this is the smallest realistic request shape where semantic separation matters

## Test Shape 2: Multi-Filter Narrowing

**Solr shape**

```text
q=*:*&fq=published:true&fq=category:tutorial&fq=date:[NOW-30DAYS TO NOW]
```

What it checks:

- multiple `fq` params
- conjunction of filters
- range filter handling
- match-all query plus real filter behavior

Why it matters:

- many operational and browse flows look more like this than like free-text relevance testing

## Test Shape 3: eDisMax + Filters

**Solr shape**

```text
q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5&fq=status:active&fq=price:[0 TO 5000]
```

What it checks:

- field-weighted relevance logic
- filter narrowing
- separation of scoring and filtering responsibilities

Why it matters:

- this is one of the most representative real-world migration shapes for commerce/search apps

## Test Shape 4: eDisMax + `mm`

**Solr shape**

```text
q=solr migration guide&defType=edismax&qf=title^3 body^1&mm=75%
```

What it checks:

- minimum-match semantics under multi-field search
- candidate-set control driven by parser semantics rather than only query syntax

Why it matters:

- this is a prime example of relevance behavior that can be lost even when the generated DSL looks plausible

## Test Shape 5: eDisMax + Phrase Boost

**Solr shape**

```text
q=solr guide&defType=edismax&qf=title body&pf=title^10
```

What it checks:

- phrase preference logic
- whether exact or near-exact phrase behavior is carried through explicitly

Why it matters:

- many teams care deeply about phrase ordering and exact-title wins

## Test Shape 6: Search + Filters + Sort

**Solr shape**

```text
q=elasticsearch&defType=edismax&qf=title^2 body^1&fq=published:true&sort=published_date desc
```

What it checks:

- relevance query
- filter narrowing
- ordering behavior layered on top

Why it matters:

- this is where teams often notice "results look valid, but the wrong things are first"

## Test Shape 7: Search + Filters + Facets

**Solr shape**

```text
q=laptop&fq=brand:Dell&json.facet={categories:{type:terms,field:category}}
```

What it checks:

- filtered query context
- facet aggregation context
- whether facet counts reflect the intended narrowed set

Why it matters:

- facets often expose subtle set-composition errors faster than the main result list does

## Test Shape 8: Search + Filters + Highlighting

**Solr shape**

```text
q=solr migration&fq=published:true&hl=true&hl.fl=title,body
```

What it checks:

- translated query behavior
- filtered result set
- highlighting response structure

Why it matters:

- highlighting is visible to users, but its correctness depends on both query behavior and index design

## Test Shape 9: Search + Filters + Facets + Highlighting + Sort

**Solr shape**

```text
q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5&fq=status:active&fq=brand:(Dell OR HP OR Lenovo)&facet.field=category&hl=true&hl.fl=title,description&sort=price asc
```

What it checks:

- full request composition under realistic workload pressure
- interactions among relevance, filter set, aggregations, response enrichment, and ordering

Why it matters:

- this is the kind of shape that reveals whether feature-by-feature support actually composes

## What OSC Should Ask For

For each integrated request shape, OSC should ask:

- what is the expected translated request?
- what warnings, if any, are expected?
- what parts are considered fully supported vs partial?
- what is the validation strategy: result-set parity, ranking sanity, facet sanity, or response-shape only?

## Bottom Line

If Amazon can show convincing integrated request tests for shapes like these, confidence in the
translation roadmap rises materially.

If the coverage stays mostly feature-slice based, OSC should keep treating the roadmap as promising
but still early in terms of migration-confidence.
