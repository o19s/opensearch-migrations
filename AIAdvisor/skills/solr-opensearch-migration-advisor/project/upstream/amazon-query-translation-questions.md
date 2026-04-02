# Targeted Questions For Amazon Query-Translation Discussion

Date: 2026-03-23

These are the highest-value follow-up questions OSC can send back to Amazon after the first pass
through the recent Solr query-translation PRs.

They are intentionally narrow and designed to clarify priority, semantics, and architecture
convergence without turning the thread into a broad design review.

## Recommended Questions

### 1. Which query path should OSC treat as authoritative in the near term?

We now see:

- merged parser / transformer / orchestrator work in the new query-engine path
- active request-level `q` work in `#2458`
- `#2458` currently appears to use `lucene.parse(q)` directly in `query-q.ts`

Question:

- should OSC treat the current `query-q.ts` path as the near-term authoritative implementation for
  standard-parser `q` support, or is it expected to converge onto the merged `translateQ`
  orchestrator path soon?

Why OSC cares:

- the AI Advisor should describe the same behavior boundary that the runtime actually has

### 2. Where do `fq` semantics sit in the roadmap?

Question:

- do you already have a concrete plan or PR sequence for `fq`, especially multiple `fq` params,
  non-scoring filter behavior, and interaction with `q`, facets, and sorting?

Why OSC cares:

- `fq` is one of the most central Solr request surfaces
- it is easy to undercount because it is less flashy than parser work

### 3. Where does `edismax` sit in the roadmap?

Question:

- where do you currently expect `edismax` support to land, including `qf`, `pf`, boosts, and `mm`,
  and do you see that as top-tier follow-on work after standard-parser `q`?

Why OSC cares:

- for many production Solr apps, `edismax` is a larger migration-risk topic than some of the
  already-open feature slices

### 4. What warning / fallback contract should OSC mirror?

Question:

- what warning vocabulary do you want downstream consumers like the AI Advisor to mirror when
  translation is partial, unsupported, or passed through?

Examples:

- translated
- partially translated
- passed through
- unsupported
- behaviorally risky

Why OSC cares:

- consistency between advisor messaging and transform-runtime behavior is one of the main goals

### 5. What integrated request tests are planned?

Question:

- beyond feature-specific tests, what combined-request cases are planned or already covered for
  things like:
  - `q + fq + sort + fl + rows/start`
  - `q + fq + facets`
  - `q + highlighting`
  - `edismax + qf + pf + mm`

Why OSC cares:

- isolated param coverage can still miss ranking drift and document-set drift in real workloads

## Short Version To Send

If OSC wants a compact version, this is the simplest useful set:

1. Should we treat the current `query-q.ts` implementation in `#2458` as the near-term
   authoritative `q` behavior, or is it expected to converge onto the merged query-engine
   orchestrator path soon?
2. Where do `fq` semantics sit in the roadmap, especially multiple filters and non-scoring filter behavior?
3. Where does `edismax` sit in the roadmap, including `qf`, `pf`, boosts, and `mm`?
4. What warning/fallback vocabulary should OSC mirror in the AI Advisor so our messaging stays
   complementary and consistent with the transform runtime?
5. What integrated request tests are planned beyond feature-by-feature coverage?

## OSC Framing

The tone that fits these questions is:

- the foundation direction looks good
- OSC is mainly trying to understand where the highest Solr migration-risk semantics land next
- OSC wants to stay aligned with the runtime, not second-guess the architecture from the outside
