# Solr `edismax` Review Note

Date: 2026-03-23

This note is the Solr-specific companion to the `fq` review note. It focuses on `edismax`
because this is often where the most important user-facing Solr relevance behavior actually lives.

## Why `edismax` Matters

For many production Solr applications, `edismax` is not a niche parser choice. It is the core
search behavior for user-facing search boxes.

It commonly carries:

- field weighting through `qf`
- phrase boosting through `pf`
- minimum-match behavior through `mm`
- additional boost logic through `bq` and `boost`
- query intent spread across multiple text fields

That means `edismax` is one of the clearest places where a migration effort can look good at the
surface level while still drifting meaningfully in relevance behavior.

## OSC View

The easy headline is:

- Solr `edismax` often maps conceptually toward OpenSearch `multi_match` plus surrounding bool /
  phrase / boost logic

But that is only a starting point.

The real migration question is not:

- "Can we turn `defType=edismax` into some OpenSearch JSON?"

It is:

- "Do we preserve the relevance-shaping intent of the Solr request well enough that search
  behavior remains explainable and reviewable?"

## What OSC Should Care About

### 1. Field weighting through `qf`

`qf` is usually the first big signal that the query is not just a plain full-text search.

Examples:

- `qf=title^3 body^1 tags^0.5`
- `qf=name^2 features^1 cat^0.5`

OSC concern:

- field boosts are often business logic, not tuning trivia
- even if a migration maps them syntactically, the resulting ranking behavior still needs scrutiny

### 2. Phrase boosting through `pf`

`pf` often captures the "exact phrase should win harder" rule.

OSC concern:

- if `pf` is absent or weakly approximated, results may still be "relevant enough" in a generic
  sense while failing the real ranking expectations of the application team

### 3. Minimum-match behavior through `mm`

`mm` is one of the clearest examples of a parameter that changes behavior materially while being
easy to under-explain.

OSC concern:

- this is not just syntax
- it changes which documents stay in the candidate set
- poor handling here can create both precision and recall surprises

### 4. Extra boosting through `bq` and `boost`

These are often where product or editorial intent gets layered in.

Examples:

- `bq=featured:true^5`
- `boost=sqrt(views)`

OSC concern:

- these may be the most "business-specific" parts of the request
- ignoring them or flattening them into generic text queries can produce the kind of migration that
  is technically running but strategically unacceptable

### 5. Interaction with `fq`

`edismax` rarely stands alone.

Typical real request:

- `q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5&fq=status:active&fq=price:[0 TO 5000]`

OSC concern:

- relevance shaping and filter narrowing have to coexist correctly
- this is one of the most important integrated request shapes for realistic migration validation

### 6. Per-field slop and more advanced semantics

Our own reference material already calls out eDisMax patterns like:

- `qf=title~2^3 body~5`

OSC concern:

- even if upstream begins with a simpler `multi_match` mapping, it should be explicit about what
  advanced eDisMax semantics are deferred
- partial support is acceptable if labeled clearly

## Suggested Questions To Ask While Reviewing Upstream Work

- Is `edismax` treated as a top-tier roadmap item or as a later enhancement?
- Which of `qf`, `pf`, `mm`, `bq`, and `boost` are planned first?
- What is considered acceptable partial support?
- How will warnings be expressed when only a subset of `edismax` behavior is preserved?
- Are there end-to-end request examples being tested, not just parameter snippets?

## Recommended Near-Term Test Shapes

These are the first `edismax` request shapes OSC should push for.

### Basic field-weighted query

`q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5`

Goal:

- verify that field weighting is preserved in a plausible OpenSearch shape

### Field weighting plus filters

`q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5&fq=status:active&fq=price:[0 TO 5000]`

Goal:

- verify that relevance shaping and narrowing constraints remain clearly separated

### `mm` behavior

`q=solr migration guide&defType=edismax&qf=title^3 body^1&mm=75%`

Goal:

- verify that minimum-match semantics are not lost or silently simplified

### Phrase boost behavior

`q=solr guide&defType=edismax&qf=title body&pf=title^10`

Goal:

- verify that exact or near-phrase preference is represented explicitly

### Boost-query / boost-function behavior

`q=solr&defType=edismax&qf=title body&bq=featured:true^5&boost=sqrt(views)`

Goal:

- verify whether business-oriented boosts are supported, partially supported, or explicitly deferred

## What To Watch For In Amazon's Response

Good signals:

- they talk about `edismax` as a major relevance topic, not just an extra parser mode
- they can say where `qf`, `pf`, `mm`, `bq`, and `boost` land in the roadmap
- they describe partial support and warning behavior explicitly
- they are thinking in realistic integrated requests

Weak signals:

- they reduce `edismax` to "use `multi_match`" with no deeper discussion
- they do not distinguish field weighting, phrase boosting, and min-match semantics
- they imply broad coverage without naming what is still deferred
- they discuss `edismax` without `fq`, sort, or facet interaction

## Bottom Line

`edismax` is the clearest place where query translation becomes relevance translation.

If upstream has a concrete, staged story for:

- `qf`
- `pf`
- `mm`
- `bq`
- `boost`
- and integrated request tests

that is a very strong sign.

If not, OSC should keep treating `edismax` as one of the top strategic gaps in the current query
translation roadmap.
