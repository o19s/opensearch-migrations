# Validation and Cutover: Relevance, Evidence, and Go/No-Go Control
**Scope:** Offline relevance evaluation, cutover-readiness evidence, shadow validation, acceptance thresholds, and rollback posture for Solr to OpenSearch migrations. Covers how to prove the new engine is safe enough to expose to users. Does not cover infrastructure provisioning or query translation mechanics.
**Audience:** O19s consultants, search relevance engineers, QA leads, and migration owners responsible for sign-off
**Last reviewed:** 2026-03-20  |  **Reviewer:** AI draft — needs expert review

---

## Key Judgements

- **If you cannot explain why the new ranking is better, you are not ready to cut over.** "Looks fine" is not evidence. Every cutover decision needs an explicit baseline, a judgment method, and a reasoned interpretation of the deltas.
- **Relevance parity is not score parity.** Solr and OpenSearch will not produce identical raw scores, and trying to force that outcome wastes time. What matters is whether the result ordering satisfies the user's information need at the positions that matter.
- **The gold query set is a control surface, not a demo artifact.** It is how you stop subjective arguments from dominating the migration. If the team cannot rerun the same judged queries on demand, the discussion will drift into anecdotes.
- **Human judgments are expensive, noisy, and still necessary.** Query logs tell you what people searched for; they do not tell you what the right answer was. Use analytics to choose the queries and humans to score the intent fulfillment.
- **Shadow traffic is the final confidence-building step, not the first measurement step.** If your offline judgments are weak, shadowing real traffic will only generate more confusion at production scale.
- **One experiment at a time is not academic purity; it is survival.** If you change analyzers, boosts, synonyms, and field mappings in one shot, any score movement is uninterpretable and cannot be defended to stakeholders.
- **A failed cutover is often a measurement failure discovered too late.** Teams usually have some telemetry for latency and errors. They far more often lack a defensible answer to "are the results actually good enough?"
- **The acceptance lead must be able to say no.** If nobody is empowered to block cutover when quality evidence is weak, the migration will be decided by schedule pressure instead of search quality.

---

## What "Validated" Means

A migration is validated only when all of the following exist:

1. A versioned query set built from real traffic and known business-critical searches
2. A written judgment rubric with examples
3. A baseline measurement from the current Solr system
4. A repeatable way to run the same evaluation against OpenSearch
5. A documented explanation of major deltas, especially the worst regressions
6. A cutover recommendation with named approvers and rollback conditions

If any of those are missing, the team is still in discovery or tuning, not validation.

---

## Measurement Stack

Use three layers. Do not skip directly to the top layer.

### Layer 1: Offline Judged Evaluation

This is the primary decision layer before cutover.

- Tooling: Quepid, RRE, or an equivalent judged evaluation harness
- Inputs: gold query set, ratings, fixed query templates, fixed corpus snapshot
- Output: nDCG / P@k / query-level regression report

### Layer 2: Functional Validation

This proves the target engine is behaviorally safe enough to test further.

- No hard query errors
- No obviously broken filters/facets/sorts
- Document counts roughly reconcile
- Highlighting, aggregations, and pagination behave as expected

### Layer 3: Shadow / Limited Live Validation

This is the final confidence layer before user-facing cutover.

- Shadow traffic comparison
- Sampled query/result diff review
- Latency, error, and timeout comparison
- Replay lag / indexing freshness checks where applicable

---

## Building the Gold Query Set

### Query Selection Rules

Start with production analytics whenever possible.

Include:

- top-volume head queries
- key revenue or mission-critical queries
- representative queries from each major information-need category
- important navigational queries
- known troublesome long-tail queries
- zero-result or reformulation-heavy queries if they represent a real product pain point

Do not overweight:

- obscure one-off queries with no business value
- internal test queries
- vanity stakeholder examples unless they represent real user needs

### Recommended Starting Size

- Small migration: 50-100 queries
- Standard migration: 100-200 queries
- Large or high-stakes migration: 200-500 judged queries, but only if the team can maintain them

More is not always better. An unmaintained 400-query set is worse than a disciplined 100-query set.

---

## Judgment Methodology

### Default Rating Scale

Use a 4-point graded scale unless there is a strong reason not to:

- `3 = Perfect`
- `2 = Good`
- `1 = Fair`
- `0 = Bad`

Define the scale in product language, not search-engine language. A judge should know what "Good" means without understanding analyzers or BM25.

### Calibration Round

Before full judging:

1. Have 2-3 judges rate the same 20-30 query/result sets
2. Compare disagreements
3. Clarify the rubric
4. Rerun if disagreement remains high

If judges fundamentally disagree on what relevance means, stop and resolve that before tuning. Otherwise every score improvement will be disputed.

### Judge Selection

Prefer:

- product owners
- support or service staff who know real user needs
- merchandisers/content owners for commerce or editorial search
- subject matter experts for domain-heavy search

Avoid relying only on engineers unless the product is deeply technical and they are true users of the system.

---

## Metrics and How To Use Them

### Primary Default

Use `nDCG@10` as the default primary metric for most migrations.

Why:

- it respects rank position
- it handles graded judgments
- it is widely understandable once explained

### Secondary Checks

Use one or two of the following:

- `P@5` for stakeholder-friendly reporting
- `MRR` for known-item or navigational search
- `Recall@k` where missing relevant documents is especially costly

Do not overload the project with too many metrics early. A migration team that cannot explain one metric clearly should not be carrying five.

---

## Quepid and RRE Posture

### Quepid

Use Quepid when the team needs:

- collaborative judgment work
- rapid exploration
- visible query-by-query comparison
- stakeholder walk-throughs of why results changed

### RRE

Use RRE when the team needs:

- repeatable CI/CD regression checks
- structured pass/fail thresholds
- automated protection against accidental relevance regressions

### Recommended Default

- Quepid for early baseline and tuning loops
- RRE for later-stage regression gating once query templates stabilize

Trying to start with only CI-style measurement is usually too rigid. Trying to finish with only a manual UI tool is usually too fragile.

---

## Baseline -> Tune -> Revalidate Loop

Use this operating rhythm:

1. Measure current Solr baseline
2. Log the query set version, query template version, and corpus version
3. Run the same evaluation on OpenSearch
4. Identify best gains and worst regressions
5. Form one hypothesis
6. Implement one change
7. Re-run the full suite
8. Record the delta and decision
9. Repeat until the worst regressions are understood and the aggregate score is acceptable

Keep a simple decision log:

- change attempted
- reason for the change
- metric delta
- queries helped
- queries harmed
- final decision

Without this, iteration history disappears and the team will repeat bad ideas.

---

## Cutover Readiness Evidence

Before recommending cutover, assemble an evidence pack with these sections:

### 1. Relevance Summary

- baseline metric on Solr
- current metric on OpenSearch
- trend over recent tuning iterations
- explanation of the top wins
- explanation of the top unresolved regressions

### 2. Functional Summary

- no critical query failures
- filters/facets/sorts validated
- pagination validated
- highlighting or field retrieval validated
- application integration smoke-tested

### 3. Data Integrity Summary

- document count comparison
- known exclusions or transformation differences
- freshness / lag posture
- duplicate / missing document checks

### 4. Operational Summary

- latency comparison
- timeout and error-rate comparison
- relevant dashboards/logs checked
- rollback path confirmed

### 5. Recommendation

- `go`
- `go with conditions`
- `no-go`

Tie the recommendation to named approvers, not the abstract team.

---

## Go/No-Go Heuristics

Use these as defaults, then tighten or relax based on domain risk.

### Default Go Signals

- No Sev-1 functional defects in critical query paths
- Aggregate judged relevance is stable or improved versus baseline
- Worst regressions are known, limited, and accepted by product/search owners
- Latency and error rates are within agreed tolerances
- Rollback path is rehearsed and credible

### Default No-Go Signals

- Critical business queries regress with no accepted mitigation
- Team cannot explain major ranking shifts
- Judgment set is incomplete or disputed
- Query failures or broken facets are still surfacing in normal usage
- Rollback path exists only on paper

### "Go With Conditions"

This is acceptable when:

- improvements are real overall
- remaining risks are narrow and named
- approvers understand the tradeoff
- a rollback decision threshold is written down

Do not say "go with conditions" when what you mean is "we ran out of time."

---

## Shadow Traffic and Limited Rollout

Shadow traffic is most useful when:

- query volume is high enough to produce signal quickly
- application behavior can tolerate mirrored reads
- the team already has an offline baseline

During shadowing, watch for:

- result shape differences
- broken filters or sort semantics
- unexpected zero-result spikes
- latency regressions
- query parser edge cases that were underrepresented in offline evaluation

For live exposure, use staged rollout if possible:

- 5%
- 25%
- 50%
- 100%

Do not advance tiers just because the calendar says so. Advance only when the prior tier has remained boring.

---

## Cutover Day Checklist

1. Confirm approvers are available and reachable
2. Freeze unnecessary search changes
3. Re-run smoke tests on critical flows
4. Confirm dashboards and logs are open and assigned
5. Confirm rollback owner and exact rollback trigger
6. Shift traffic according to the agreed plan
7. Watch critical queries and operational metrics in the first hour
8. Log every anomaly and decision in real time
9. Decide whether to continue, pause, or roll back based on prewritten conditions

If cutover-day decision-making depends on improvisation, the team is not ready.

---

## Decision Heuristics

- If the judged query set is still changing materially, freeze the dataset before making go/no-go claims.
- If offline evaluation still shows unexplained critical regressions, do not use shadow traffic as a substitute for fixing them.
- If shadow traffic reveals broken filters, sort semantics, or zero-result spikes, stop rollout progression and return to validation.
- If the best available recommendation is "go with conditions," write the exact conditions and rollback triggers before exposing more traffic.
- If stakeholders are debating anecdotes instead of evidence, return to the gold set, scorecards, and versioned findings rather than improvising policy in meetings.

---

## Common Mistakes

- Treating document-count parity as proof of search quality
- Letting stakeholders add favorite queries to the gold set mid-stream without versioning
- Judging on different corpora between Solr and OpenSearch
- Bundling too many tuning changes into a single experiment
- Claiming parity when the team has only checked demos, not representative traffic
- Confusing "different" with "worse" without measured evidence
- Running shadow traffic before the offline judgment loop is credible

---

## Open Questions / Evolving Guidance

- What minimum judged-query volume is enough for a defensible sign-off in low-traffic products?
- When should click-model or interleaving methods supplement human judgments during migration?
- What default tolerance band should be recommended for "parity" in different domains?
- How should vector or hybrid retrieval be evaluated when there is no true Solr equivalent baseline?
