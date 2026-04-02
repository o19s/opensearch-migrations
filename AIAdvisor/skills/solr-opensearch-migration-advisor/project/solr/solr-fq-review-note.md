# Solr `fq` Review Note

Date: 2026-03-23

This note is the next-step deep dive for the Solr-specific lane after the initial upstream review.
It focuses on `fq` because it is one of the most central Solr request surfaces and a fast way to
pressure-test whether the upstream effort is thinking in real request semantics rather than only
feature slices.

## Why `fq` Matters

`fq` is deceptively simple. At a glance it looks like "just another query parameter," but in real
Solr applications it often carries a large share of the workload's operational and semantic meaning.

Typical uses:

- published/active flags
- tenant or visibility filtering
- category/brand/navigation constraints
- date windows
- price or numeric narrowing
- geo constraints
- drill-down and faceting contexts

That means `fq` is often where "business truth" lives, even when `q` drives free-text intent.

## OSC View

The correct top-line mapping is straightforward:

- Solr `fq` usually maps conceptually to OpenSearch `bool.filter`

But that is only the beginning.

The real migration question is not:

- "Can we translate an `fq` string?"

It is:

- "Do we preserve non-scoring filter semantics correctly when `fq` is combined with real request structure?"

## What OSC Should Care About

### 1. Non-scoring behavior

The first key expectation is that `fq` clauses should not affect ranking the way scoring `q`
clauses do.

OSC concern:

- a translation that places `fq` logic into scoring query clauses instead of filter context may
  technically "work" but still be behaviorally wrong

### 2. Multiple `fq` params

Real Solr apps commonly send more than one `fq`.

Examples:

- `fq=status:published`
- `fq=category:tutorial`
- `fq=date:[NOW-30DAYS TO NOW]`

OSC concern:

- upstream should be explicit about how multiple filters are combined
- the normal expectation is conjunctive narrowing unless something more specialized is happening

### 3. Interaction with `q`

The central semantic question is how `q` and `fq` interact together.

Examples worth caring about:

- `q=title:java&fq=status:active`
- `q=solr migration&fq=tenant:acme`
- `q=*:*&fq=price:[10 TO 100]`

OSC concern:

- `q` drives relevance
- `fq` constrains the candidate set
- those roles should remain legible in translation and in runtime warnings

### 4. Interaction with facets

This is where many real migration subtleties appear.

Examples:

- `q=laptop&fq=brand:Dell&json.facet=...`
- `q=*:*&fq=status:active&facet.field=category`

OSC concern:

- it is not enough for facets and `fq` to be translated independently
- we need confidence that the faceting context still reflects the intended filtered document set

### 5. Interaction with sorting and pagination

Examples:

- `q=title:java&fq=status:published&sort=published_date desc`
- `q=*:*&fq=category:books&rows=20&start=40`

OSC concern:

- filter composition must remain stable as sorting and paging are layered on top

### 6. Filter types beyond simple terms

`fq` is not only exact-match filtering.

Important shapes:

- term filters
- numeric/date ranges
- boolean combinations
- grouped filters
- geo filters
- fielded disjunctions

OSC concern:

- if upstream begins with simple `field:value`, that is fine
- but it should be explicit which `fq` shapes are supported, partially supported, or deferred

## Suggested Questions To Ask While Reviewing Upstream Work

- When `fq` is translated, does it clearly land in filter context?
- How are multiple `fq` params composed?
- Are `fq` clauses tested together with a real `q`, or only in isolation?
- Are facets tested with an active filtered set?
- Are warning messages clear when an `fq` form is unsupported or only partially handled?

## Recommended Near-Term Test Shapes

These are the first test shapes OSC should push for.

### Basic non-scoring filter

`q=title:java&fq=status:active`

Goal:

- verify that `q` remains the scoring expression
- verify that `status:active` is a filter constraint

### Multiple filters

`q=title:java&fq=status:published&fq=category:tutorial&fq=date:[NOW-30DAYS TO NOW]`

Goal:

- verify how multiple `fq` params combine
- verify range handling under filter context

### Match-all with filters

`q=*:*&fq=price:[10 TO 100]&fq=inStock:true`

Goal:

- verify that filtering still works correctly without a scoring text query

### Filters plus facets

`q=laptop&fq=brand:Dell&json.facet={...}`

Goal:

- verify that facet results reflect the intended filtered query context

### Filters plus sorting

`q=solr&fq=published:true&sort=published_date desc`

Goal:

- verify that filtering and ranking/sorting do not get conflated

## What To Watch For In Amazon's Response

Good signals:

- they describe `fq` in terms of filter context, not generic translation
- they already have combined-request tests planned
- they can say where `fq` lands relative to `edismax`
- they speak in terms of warnings/partial support where necessary

Weak signals:

- they only discuss `fq` as a string-conversion problem
- they do not distinguish scoring vs filtering semantics
- they talk about facet support and `fq` support separately with no integrated cases
- they imply broad Solr parity without naming scope limits

## Bottom Line

`fq` is the right next step because it is both:

- central enough to matter in most real Solr workloads
- concrete enough to evaluate quickly

If upstream has a solid story for `fq` composition, filter context, and integrated request tests,
that is a strong positive signal.

If not, it is one of the clearest places where OSC should push for priority and clarity before the
project starts sounding more complete than it really is.
