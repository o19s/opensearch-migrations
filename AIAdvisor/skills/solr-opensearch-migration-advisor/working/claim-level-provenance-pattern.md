# Claim-Level Provenance Pattern
**Purpose:** Lightweight pattern for attaching supporting evidence to the most important advice chunks
**Audience:** OSC design team, contributors, and anyone shaping the skill corpus
**Status:** Discussion draft
**Last updated:** 2026-03-19

---

## Why This Exists

The current repo is good at storing advice, heuristics, and worked examples.
It is not yet good at making the provenance of a specific claim easy to surface.

The goal is not to turn every markdown file into a database. The goal is to make the
strongest and most reusable claims easier to:

- cite
- challenge
- compare
- defend in client-facing work
- distinguish from generic source-summary material

This pattern is intentionally **light and insightful**, not fully normalized.

---

## What To Attach Provenance To

Do this only for the most important reusable chunks:

- key judgements
- decision heuristics
- common mistakes
- war stories

Do **not** try to annotate every sentence in every file.

---

## Minimal Pattern

Each annotated claim should have:

- `id`
- `claim`
- `why_it_matters`
- `provenance`

Recommended provenance fields:

- `type`
- `strength`
- `source_refs`
- `owner`

Suggested values:

- `type`: `expert-opinion`, `playbook-derived`, `worked-example`, `external-reference`, `mixed`
- `strength`: `strong`, `moderate`, `tentative`
- `owner`: person or team who stands behind the claim today

---

## Preferred Markdown Shape

Use this only where the extra structure adds real value.

```md
### CJ-014: Rebuildability outranks index size

Claim:
If the client cannot fully rebuild the index from source, treat the migration as high risk
even when the index is "only" medium-sized.

Why it matters:
Non-rebuildable search estates make every indexing defect and cutover error more dangerous.

Provenance:
- type: expert-opinion
- strength: strong
- owner: Sean / OSC
- source_refs:
  - playbook/pre-migration-assessment.md
  - examples/drupal-solr-opensearch-demo/pre-migration-assessment-starter.md
```

This keeps the claim readable in plain markdown while making support material easy to expose.

---

## Design Principles

- **Claim-level beats document-level.**
  "This advice came from this exact chunk" is more useful than "somewhere in this file."
- **Support the strongest claims first.**
  Not every note deserves provenance overhead.
- **Show the shape of evidence, not fake certainty.**
  A good provenance block can say "expert-opinion, moderate strength" and still be useful.
- **Differentiate source types.**
  A field note, a client pattern, and an AWS doc are not the same kind of support.
- **Preserve human readability.**
  If the markdown becomes annoying to read in a text editor, the pattern has failed.

---

## Claim-Level Provenance Examples

These are intentionally intuitive and a little discussion-provoking. They are not the final schema.

### Example 1: Strong expert heuristic

```md
### CJ-001: Like-for-like migrations are usually the wrong goal

Claim:
If the migration has no visible customer benefit and is framed as a straight engine swap,
push back on the premise before planning delivery.

Why it matters:
Engine swaps without user value often burn budget while preserving weak search behavior.

Provenance:
- type: expert-opinion
- strength: strong
- owner: OSC consulting team
- source_refs:
  - skills/solr-to-opensearch-migration/references/consulting-methodology.md
  - playbook/pre-migration-assessment.md
```

Why this is useful:
- clean expression of a consultant stance
- easy to cite in a client memo
- clear that this is opinionated practice, not a vendor claim

### Example 2: Mixed claim with technical and field support

```md
### CJ-009: Aliases should be mandatory in the target design

Claim:
Never wire applications directly to physical index names in OpenSearch migration projects.

Why it matters:
Aliases make reindex, rollback, blue-green cutover, and future schema evolution survivable.

Provenance:
- type: mixed
- strength: strong
- owner: platform design reviewers
- source_refs:
  - skills/solr-to-opensearch-migration/references/03-target-design.md
  - sources/opensearch-fundamentals/index-management.md
  - examples/northstar-enterprise-demo/design.md
```

Why this is useful:
- mixes expert judgment with technical source support
- points to both canonical guidance and a concrete example

### Example 3: War-story-backed caution

```md
### CM-004: Shadow traffic is not optional when stakeholder trust is low

Claim:
If stakeholders are already nervous about result changes, require a shadow period before full cutover.

Why it matters:
Trust collapses faster than metrics improve. A safe technical plan can still fail politically.

Provenance:
- type: worked-example
- strength: moderate
- owner: engagement lead
- source_refs:
  - skills/solr-to-opensearch-migration/references/05-validation-cutover.md
  - skills/solr-to-opensearch-migration/references/roles-and-escalation-patterns.md
  - examples/drupal-solr-opensearch-demo/pre-migration-assessment-starter.md
```

Why this is useful:
- preserves the political/organizational dimension of a migration claim
- makes room for evidence that is experiential rather than purely technical

### Example 4: Tentative pattern that invites discussion

```md
### DH-011: Split multilingual content only when the product experience justifies it

Claim:
Do not default to one index per language. Start by proving the user experience requires it.

Why it matters:
Teams often pay long-term operational complexity for a multilingual design they never needed.

Provenance:
- type: expert-opinion
- strength: tentative
- owner: search architecture working group
- source_refs:
  - skills/solr-to-opensearch-migration/references/03-target-design.md
  - examples/drupal-solr-opensearch-demo/migration-report.md
```

Why this is useful:
- shows that provenance can support nuanced, discussable advice
- keeps "tentative but important" claims visible without overstating certainty

### Example 5: Explicitly separating external support from OSC stance

```md
### CJ-017: Relevance evidence should gate migration decisions

Claim:
Do not promise "better search" unless the team has agreed on a measurable baseline and comparison method.

Why it matters:
Without explicit evidence, "better" becomes a political argument instead of an engineering claim.

Provenance:
- type: mixed
- strength: strong
- owner: OSC relevance practice
- source_refs:
  - playbook/relevance-methodology.md
  - skills/solr-to-opensearch-migration/references/consulting-methodology.md
  - sources/opensearch-best-practices/search-relevance-tuning.md
```

Why this is useful:
- distinguishes OSC methodology from external best-practice support
- likely to matter in proposals, assessments, and cutover gates

---

## Where To Pilot This First

Do not roll this out across the whole repo immediately.

Best pilot candidates:

- `skills/solr-to-opensearch-migration/references/consulting-methodology.md`
- `skills/solr-to-opensearch-migration/references/03-target-design.md`
- `skills/solr-to-opensearch-migration/references/05-validation-cutover.md`
- `playbook/pre-migration-assessment.md`
- `playbook/relevance-methodology.md`

These files contain the kinds of high-value, challengeable claims that benefit most from provenance.

---

## Questions For The OSC Design Team

These are the best open questions to answer before implementing this broadly:

1. Do we want provenance to support **human trust**, **agent retrieval**, or both?
2. Should provenance identify the **person who stands behind a claim**, or only the source files?
3. Do we want to distinguish **OSC stance** from **external-source support** explicitly?
4. Should a "war story" be allowed as evidence on its own, or should it usually be paired with a more general reference?
5. Are `type`, `strength`, and `source_refs` enough for a first pass, or do we also want `date`, `reviewer`, or `confidence notes`?
6. Do we want these blocks visible inline in the main docs, or collapsed into a sidecar pattern later if they grow too noisy?

---

## Recommendation

Pilot this in 2 to 3 high-value docs first.

If the team likes the readability and the resulting answers are more defensible, then:

1. standardize the mini-pattern
2. annotate only the strongest claims
3. teach the skill/router to prefer annotated claims when answering high-stakes questions

If the team hates the visual overhead, move the same fields into a sidecar format later.
