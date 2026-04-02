# Upstream Query Translation Assessment

Date: 2026-03-23

This is a more detailed OSC-facing assessment of the recent upstream Solr query-translation PRs
in `opensearch-project/opensearch-migrations`, based on the Slack summary plus current GitHub PR
state as of 2026-03-23.

Scope note:

- this assessment is about the active Solr query-translation path, which currently appears to live
  primarily under `TrafficCapture/SolrTransformations/...`
- upstream also has a separate `transformation/standardJavascriptTransforms/src` area with generic
  metadata/settings/index-shape transforms; that work matters, but it should not be counted as
  Solr query-semantic coverage

## Current State Correction

The Slack snapshot is already slightly stale:

- [#2478](https://github.com/opensearch-project/opensearch-migrations/pull/2478) merged on 2026-03-23

That matters because the engine is now no longer just parser + transformer pieces. Upstream now
has a merged orchestrator layer that wires parser-to-transform execution and returns warnings on
parse/transform failure instead of throwing.

## What The Upstream Work Adds

### Architecture/foundation

- [#2399](https://github.com/opensearch-project/opensearch-migrations/pull/2399)
  Query-engine skeleton and interfaces. This is architecture, not end-user coverage.
- [#2434](https://github.com/opensearch-project/opensearch-migrations/pull/2434)
  PEG-based Solr parser with AST generation, default field handling, `q.op=AND`, and parse errors
  returned safely.
- [#2461](https://github.com/opensearch-project/opensearch-migrations/pull/2461)
  Transformer stage with registry-based AST-to-OpenSearch dispatch.
- [#2478](https://github.com/opensearch-project/opensearch-migrations/pull/2478)
  Orchestrator that wires parser -> transformer and returns fallback `query_string` plus warnings
  on parse/transform failure.

OSC view:

- this is good engineering direction
- it gives a clean seam for AI Advisor consistency
- it also means the advisor can talk in terms of "translated", "partial", "passthrough", and
  "warning" states instead of pretending translation is binary

### Parameter / feature coverage

- [#2411](https://github.com/opensearch-project/opensearch-migrations/pull/2411)
  `fl` translation
- [#2435](https://github.com/opensearch-project/opensearch-migrations/pull/2435)
  `sort` translation
- [#2379](https://github.com/opensearch-project/opensearch-migrations/pull/2379)
  JSON term facets
- [#2396](https://github.com/opensearch-project/opensearch-migrations/pull/2396)
  range facets, but not date/time ranges yet
- [#2383](https://github.com/opensearch-project/opensearch-migrations/pull/2383)
  highlighting request/response transforms
- [#2417](https://github.com/opensearch-project/opensearch-migrations/pull/2417)
  `cursorMark` -> `search_after`, with explicit dual-target limitations

OSC view:

- this is useful breadth
- but breadth is not the same as production confidence
- the highest-risk migration problems still sit in the meaning of `q`, `fq`, `edismax`,
  boosting, analysis, and combined query behavior
- generic transform utilities elsewhere in the repo may improve migration plumbing, but they do
  not materially change this query-priority assessment unless they affect request semantics directly

### Core semantic translation

- [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458)
  standard query parser translation for terms, ranges, phrases, booleans, and boosts

OSC view:

- this is the most important currently open feature PR in the list
- if the engine can only translate surface params but not preserve query intent and ranking
  structure, the migration story will still feel shallow

### Validation infrastructure

- [#2287](https://github.com/opensearch-project/opensearch-migrations/pull/2287)
  transformation shim, multi-target validation, and E2E framework

OSC view:

- strategically one of the most important merged items
- it creates the possibility of evidence-backed validation instead of subjective confidence
- OSC should encourage upstream to use this to validate integrated requests, not just isolated params

## What Seems Correctly Prioritized

The following parts of the upstream priority stack look correct:

1. Build the parser / transformer / orchestrator foundation first.
2. Keep an E2E validation harness in place early.
3. Add common request-parameter translations incrementally.
4. Return warnings/fallbacks rather than crashing when coverage is incomplete.

That is the right general shape.

## What Looks Under-Prioritized From OSC's Perspective

### 1. `edismax` and request-level relevance behavior

This is the biggest gap in the listed PR set.

Many real Solr applications rely on `edismax` behavior, `qf`, `pf`, boosts, minimum-should-match,
and fielded relevance tuning. Standard parser support matters, but for many real migrations it is
not enough by itself.

OSC concern:

- if `edismax` is not near the top of the roadmap, the translation effort may look broader than it
  really is for production Solr workloads

### 2. `fq` behavior and query/filter composition

The Slack list does not call out `fq`, even though it is one of the most central Solr request
surfaces.

OSC concern:

- correctness of filters, cache-like semantics, and composition with `q` matters more than some
  more visible but less central features

### 3. Integrated requests instead of parameter-by-parameter success

The current PR list mostly reads like feature slices:

- `fl`
- `sort`
- highlighting
- cursor
- facets

That is fine for implementation, but users do not send isolated feature slices. They send one
request containing many of them.

OSC concern:

- success should increasingly be measured on real combined requests
- ranking changes and document-set drift can appear only when these features interact

### 4. Explicit compatibility language

The merged orchestrator already returns warnings and fallback `query_string` results.
That is a good start. OSC should push for making that an explicit product contract.

OSC concern:

- AI Advisor and transform runtime must use the same language for:
  - translated
  - partially translated
  - passed through
  - unsupported
  - behaviorally risky

## Suggested Priority View For OSC

Best-guess OSC ordering:

### Top tier

- standard query parser fidelity: [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458)
- `fq` support and integrated filter semantics
- `edismax` support and its relevance-affecting params
- combined-request E2E validation using the existing shim framework

### Middle tier

- `sort`: [#2435](https://github.com/opensearch-project/opensearch-migrations/pull/2435)
- facets in realistic requests: [#2379](https://github.com/opensearch-project/opensearch-migrations/pull/2379), [#2396](https://github.com/opensearch-project/opensearch-migrations/pull/2396)
- highlighting: [#2383](https://github.com/opensearch-project/opensearch-migrations/pull/2383)

### Lower tier

- cursor pagination: [#2417](https://github.com/opensearch-project/opensearch-migrations/pull/2417)

This is not because cursor pagination is unimportant. It is because fewer migrations are blocked
on it than on query/filter relevance behavior.

## Specific Concerns OSC Should Flag

### Concern 1: standard parser coverage may be mistaken for "query translation solved"

The presence of parser/orchestrator infrastructure plus standard parser translation could make the
effort look more complete than it is.

Recommended OSC wording:

- "Great foundation, but we should avoid implying broad Solr query parity until `fq`, `edismax`,
  and combined-request validation are covered."

### Concern 2: highlighting translation can still drift because of mappings/analyzers

Even if request/response shape translation is correct, highlighting quality depends on:

- analyzer differences
- field mapping choices
- term vector / highlighting mode compatibility

Recommended OSC wording:

- "Highlighting support is valuable, but we should treat it as dependent on index-design parity,
  not only request translation."

### Concern 3: cursor translation already signals dual-target incompatibility

The cursor PR explicitly notes that Solr and OpenSearch cursor tokens are not compatible and uses
fallback behavior in dual-target mode.

Recommended OSC wording:

- "This is the right kind of honesty. We should preserve and surface these incompatibility warnings
  rather than trying to smooth them over."

### Concern 4: facets need realistic scope statements

The merged facet work covers:

- JSON term facets
- numeric/custom range facets

It does not yet cover everything.

Recommended OSC wording:

- "Facet progress is real, but we should keep scope precise, especially around date/time and more
  advanced facet semantics."

## Potential Action Items For OSC

### Recommended immediate OSC actions

1. Send Amazon a short priority response:
   - foundation direction looks right
   - core query/filter fidelity should stay ahead of lower-frequency features
   - `edismax` and `fq` should be explicit priorities if not already on deck

2. Align AI Advisor messaging with upstream transform-engine status:
   - do not overclaim support
   - use the same caveat language as upstream warnings/fallbacks

3. Add or maintain an internal coverage matrix:
   - translated
   - partial
   - unsupported
   - behaviorally risky

4. Ask for integrated test cases, not just feature-slice PRs:
   - `q + fq + sort + fl + rows/start`
   - `q + fq + facets`
   - `q + highlighting`

### Optional OSC asks to Amazon

- publish or share a feature-priority matrix that separates:
  - usage frequency
  - migration criticality
  - user-visible breakage risk
  - current implementation status

- explicitly identify where `edismax`, `fq`, function queries, join/graph queries, and MLT sit in
  the roadmap

- document the warning/fallback contract coming out of the orchestrator

## Suggested Reply Shape Back To Amazon

If OSC wants a compact response, this is the basic position:

The current direction looks broadly correct. The parser/transform/orchestrator foundation and the
E2E validation harness are the right investments, and the team is making useful progress on common
parameters like `fl`, `sort`, facets, highlighting, and cursor handling. From OSC's point of view,
the next priority should continue to bias toward query and filter fidelity over surface breadth.

In particular, we would rank standard query semantics, boosting, `fq`, and especially `edismax`
behavior above lower-frequency features. We also want the AI Advisor and the transform engine to
stay tightly aligned in how they describe partial support, warnings, and behavioral risk. The best
way to keep this complementary and consistent is to evaluate integrated requests, not only
parameter-by-parameter translations.
