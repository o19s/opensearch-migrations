# Solr Query Coverage Matrix

Date: 2026-03-23

This is a working OSC matrix for the Solr-specific query-translation lane.
It is meant to stay lightweight and editable, not to become a full specification.

## Current Read

The most important finding from the first pass is structural:

- the active Solr query path appears to live mainly under
  `TrafficCapture/SolrTransformations/...`
- the newer query-engine architecture exists upstream
- but PR `#2458` currently appears to implement `q` translation in
  `features/query-q.ts` using the `lucene` parser directly rather than
  calling the merged query-engine orchestrator (`translateQ`)

OSC implication:

- there is a potential consistency risk between the "new engine" story and the
  actually active feature implementation path
- this should be clarified before treating parser/orchestrator progress as fully
  reflected in request-level `q` behavior

Follow-up evidence from PR discussion:

- in review comments on [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458),
  `k-rooot` explicitly asked whether the implementation should leverage the
  query-engine framework

OSC implication:

- the convergence question is not only an external OSC concern; it is also visible
  inside upstream review discussion

## Working Matrix

| Feature | Common in real Solr apps? | Migration risk if wrong | Current upstream read | OSC concern / note |
|---|---|---|---|---|
| Standard parser `q` | High | High | Active in [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458) | Most important current feature PR; likely the first real semantics checkpoint |
| `fq` | High | High | Not explicit in the reviewed PR list | Should be near-top priority; central to non-scoring filter semantics |
| `edismax` | High | High | Not explicit in reviewed PR list; parser grammar docs say parser-specific semantics are post-parse work | Biggest strategic gap for many production Solr workloads |
| Boosts | Medium-High | High | Mentioned in [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458) | Need to distinguish syntactic boost support from real relevance parity |
| `sort` | High | Medium | Open in [#2435](https://github.com/opensearch-project/opensearch-migrations/pull/2435) | Important, but usually secondary to `q`/`fq`/`edismax` fidelity |
| `fl` | High | Low-Medium | Merged in [#2411](https://github.com/opensearch-project/opensearch-migrations/pull/2411) | Useful request coverage, but not major migration-risk reduction by itself |
| JSON term facets | Medium-High | Medium | Merged in [#2379](https://github.com/opensearch-project/opensearch-migrations/pull/2379) | Real progress; should be tested with realistic `q` + `fq` combinations |
| Range facets | Medium | Medium | Merged in [#2396](https://github.com/opensearch-project/opensearch-migrations/pull/2396) | Date/time gap still matters |
| Highlighting | Medium | Medium | Open in [#2383](https://github.com/opensearch-project/opensearch-migrations/pull/2383) | Depends on mapping/analyzer parity, not only request translation |
| `rows` / `start` | High | Low-Medium | Already present in active feature path | Common and useful, but not core semantic-risk area |
| `cursorMark` | Low-Medium | Medium | Open draft in [#2417](https://github.com/opensearch-project/opensearch-migrations/pull/2417) | Important for some workloads; dual-target incompatibility warning is a good sign |
| Function queries | Medium | High | Not visible in reviewed PRs | High-risk gap; easy place for false confidence if ignored |
| Join / graph queries | Low-Medium | High | Not visible in reviewed PRs | Likely unsupported/partial for a while; should be labeled very clearly |
| MLT / spellcheck | Low-Medium | Medium | Not visible in reviewed PRs | Secondary priority unless a concrete client workload depends on them |

## Concrete Findings From `#2458`

First-pass observations from the current PR branch:

- `features/query-q.ts` uses `lucene.parse(q)` directly
- the file handles:
  - match-all
  - term queries
  - phrase queries
  - ranges
  - boolean operators
  - boosts
  - `rows` -> `size`
  - `start` -> `from`
- on parse failure it falls back to `query_string`
- the request registry currently wires `query-q.request` directly into the select pipeline

This matters because the merged query-engine/orchestrator path:

- has a parser
- has a transformer stage
- has an orchestrator with warnings and translation modes

But the active `#2458` feature implementation, as currently reviewed, does not obviously route
through that path. That may be temporary, intentional, or simply incomplete, but OSC should ask.

Review-thread evidence:

- `#2458` includes a review comment asking whether the feature should leverage the
  query-engine framework and whether the work should be split into smaller modular PRs
- this makes it more likely that the current direct `lucene` path is an intermediate
  state rather than a settled final architecture

## Immediate Questions To Clarify With Amazon

1. Is `#2458` intentionally independent from the merged query-engine/orchestrator path?
2. If not, what is the planned convergence point?
3. Where do `fq` and `edismax` sit in the concrete roadmap?
4. Which request path is the AI Advisor expected to describe as authoritative?
5. What warning vocabulary should OSC mirror in advisor messaging?
6. Is the current `query-q.ts` implementation a temporary bridge, or should OSC treat it as the
   near-term authoritative behavior for standard-parser `q` support?

## Best Next Steps For OSC

1. Confirm architecture intent:
   - ask whether the direct `lucene`-based `query-q.ts` path is temporary or the real near-term implementation path
2. Keep priority pressure on:
   - `fq`
   - `edismax`
   - integrated request tests
3. Avoid overstating coverage:
   - foundation progress is real
   - but request-level `q` semantics and the new query-engine story may not yet be fully unified

## Suggested Near-Term Test Shapes

- `q=title:java&fq=status:active`
- `q=title:java^2 OR body:java&fq=category:docs`
- `q=foo bar&defType=edismax&qf=title^3 body&mm=2<75%`
- `q=title:java&fq=price:[10 TO 100]&sort=price desc`
- `q=title:java&fq=category:books&json.facet=...`

## Working Bottom Line

The first-pass evidence reinforces the existing OSC view:

- `q` semantics are the most important open area
- `fq` and `edismax` still look underrepresented
- integrated requests should matter more than isolated feature wins
- there may also be an upstream convergence question between the merged query-engine path and the
  currently active request-transform implementation
