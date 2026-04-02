# Migration Execution: Stage Plans, Control Points, and Rollback Boundaries

**Scope:** Execution-stage guidance for Solr-to-OpenSearch migrations after assessment and target design are complete. Covers stage planning, backfill strategy, dual-write and mirrored reads, execution boundaries, cutover preparation, and rollback posture. Does not define workflow runtime code or deployment automation.
**Audience:** Migration leads, search platform engineers, data engineers, application engineers, and operators coordinating staged migration execution
**Last reviewed:** 2026-03-20  |  **Reviewer:** AI draft — rewritten to align with playbook and approval model

---

## Key Judgements

- **Execution should follow a bounded stage plan, not an improvised checklist.** If the team cannot name the current stage, its success criteria, and its stop conditions, the migration is not under control.
- **Backfill is necessary but never sufficient.** A complete document copy does not prove query correctness, freshness, operational stability, or application compatibility.
- **Dual-write is a coordination tool, not a badge of maturity.** If dual-write adds more uncertainty than confidence, it is the wrong choice for that workload.
- **Mirrored reads usually build trust faster than early production exposure.** They let the team learn under real traffic shape while preserving customer safety.
- **Execution stages should create artifacts, not just side effects.** Every major stage should leave behind evidence, a status decision, and an updated risk posture.
- **Rollback boundaries must be designed before the team wants them.** In practice, rollback is hardest when the team is tired, rushed, and staring at partial signals.
- **The costliest execution failures are scope leaks.** Teams start by migrating search, then quietly add autocomplete, merchandising, analytics, and admin search into the same track without re-baselining risk.
- **Do not confuse pipeline motion with migration progress.** High ingest volume is not progress if relevance, freshness, or operational integrity are still unknown.

---

## Execution Preconditions

Do not begin execution work until these are true:

- source assessment exists
- target design exists
- migration scope is bounded
- validation approach is defined
- operators know who can approve and who can roll back

If any of those are missing, stay in design and planning.

---

## The Stage Model

Prefer a small number of explicit stages:

1. target validation
2. sample backfill
3. full backfill
4. application integration validation
5. mirrored reads or shadow traffic
6. dual-write if needed
7. staged production cutover

Not every migration needs all seven. A simple batch-driven search workload may skip dual-write entirely. A freshness-sensitive commerce workload may require it.

Each stage should define:

- objective
- prerequisites
- actions
- success criteria
- stop conditions
- owner
- evidence produced

That structure should match the migration playbook.

---

## Stage 1: Target Validation

### Objective

Prove that target mappings, analyzers, and query abstractions can represent the source workload safely enough to proceed.

### Typical Actions

- create initial index templates and aliases
- load a representative sample
- run smoke queries across the major query classes
- inspect analyzer output and mapping behavior

### Success Criteria

- no critical mapping failures
- no uncontrolled dynamic field creation in protected areas
- major query classes are representable
- field modeling does not force immediate redesign

### Stop Conditions

- target design assumptions fail under sample data
- key source behavior has no acceptable target representation
- application query layer requires deeper redesign than planned

### Evidence Produced

- smoke-test summary
- mapping exception notes
- query translation examples

---

## Stage 2: Sample Backfill

### Objective

Exercise the indexing path on enough real data to discover mapping, transform, and pipeline failures early.

### Typical Actions

- export a bounded sample from Solr
- transform into target ingest format
- index into OpenSearch
- inspect rejects, malformed docs, and timing

### What To Watch

- rejected document reasons
- field-type mismatches
- missing or malformed dates
- analyzer surprises
- unexpected ingest latency

### Decision Heuristics

- If more than a trivial fraction of documents fail for schema reasons, stop and repair the mapping or transforms before increasing volume.
- If rejects cluster around one data family, isolate that family and fix it explicitly instead of weakening the mapping globally.
- If the only way to make the sample pass is to enable loose dynamic mapping, you are creating future production risk.

---

## Stage 3: Full Backfill

### Objective

Populate the target with the complete migration dataset at operationally safe throughput.

### Backfill Patterns

Choose the simplest viable pattern:

- direct export and bulk load for smaller data sets
- staged export to object storage plus bulk import for larger volumes
- replay from a durable event stream if the source system already emits one

### Throughput Guidance

- start conservatively
- increase parallelism only while cluster health remains stable
- measure bulk rejection rates, queueing, and indexing freshness continuously

### Common Mistakes

- pushing bulk throughput before mapping stability is proven
- running full backfill and query tuning at the same time with no environment isolation
- assuming document-count parity means the data is semantically correct

### Evidence Produced

- document-count comparisons
- ingest reject log summary
- freshness and replay timing summary

---

## Stage 4: Application Integration Validation

### Objective

Prove that the application can speak to the new search layer safely before exposing users.

### Typical Actions

- validate query translation layer
- validate autocomplete, browse, filter, and pagination behaviors
- test timeout, retry, and fallback posture
- confirm observability hooks are live

### Key Risks

- Solr-specific query builder assumptions
- deep pagination behavior changes
- facet and grouping semantics drifting subtly
- hidden dependencies on score explanations or handler-specific params

### Decision Heuristics

- If the app still leaks Solr syntax deeply into business code, pause execution and refactor before cutover planning.
- If you cannot test the real application path end to end, treat all later stages as provisional.

---

## Stage 5: Mirrored Reads Or Shadow Traffic

### Objective

Observe target behavior under representative live traffic without exposing customers to target-side failures.

### Typical Actions

- mirror or replay a bounded share of read traffic
- compare latency, errors, freshness, and sampled results
- review top regressions with a human relevance owner

### Why This Stage Matters

Mirrored reads are often the highest-leverage trust-building stage because they expose operational and relevance issues that static test sets miss.

### Stop Conditions

- sustained target instability
- unexplained critical relevance regressions
- replay lag or freshness drift beyond threshold

### Evidence Produced

- mirrored-read findings summary
- sampled result diffs
- operational dashboard snapshots

---

## Stage 6: Dual-Write

### When To Use It

Use dual-write only when data freshness or source-system architecture demands it.

Good reasons:

- near-real-time updates matter materially
- you need a stable target while the source remains live
- the source of truth emits manageable write events already

Bad reasons:

- "it feels safer"
- the team has no replay strategy but hopes dual-write will hide the gap
- the application layer is not stable enough to own write correctness yet

### Dual-Write Rules

- keep one system of record conceptually clear
- log and surface write divergence
- do not silently ignore target write failures
- bound the period of dual-write so it does not become permanent architecture

### Rollback Reality

Dual-write can make rollback easier for read traffic, but it can make ownership and data reconciliation harder. Plan both sides.

---

## Stage 7: Staged Production Cutover

### Objective

Move live customer read traffic to OpenSearch in bounded increments with explicit human approval.

### Default Pattern

- 5%
- 25%
- 50%
- 100%

Hold between steps long enough to inspect telemetry and sampled user-visible behavior.

### Before Starting

- validation report approved
- cutover checklist ready
- rollback owner active
- command channel open
- current dashboards healthy

### Never Treat As Autonomous

- first production traffic exposure
- final move to 100%
- rollback from a live cutover

These are always human-owned decisions, even if the AI summarizes the evidence.

---

## Rollback Boundaries

Rollback planning should answer:

- what traffic or workload can be moved back
- how long rollback remains feasible
- who can authorize it
- what data reconciliation is required afterward

### Good Rollback Posture

- clear trigger thresholds
- named owner
- tested traffic-routing reversal
- preserved source readiness during the watch window

### Bad Rollback Posture

- "we can always switch back" with no operational owner
- no agreement on what counts as failure
- source degraded too early to serve as a stable fallback

---

## Artifact Expectations By Stage

Each stage should leave behind at least one durable artifact.

| Stage | Minimum artifact |
|---|---|
| Target validation | smoke-test summary |
| Sample backfill | reject analysis and sample ingest notes |
| Full backfill | count/freshness summary |
| Application validation | integration findings and known gaps |
| Mirrored reads | traffic comparison findings |
| Dual-write | divergence monitoring summary |
| Cutover | approved checklist and command log |

If a stage produced no artifact, later reviewers will be forced to rely on memory and optimism.

---

## Common Failure Modes

- Advancing stages because the team is busy, not because the exit criteria were met
- Treating count parity as proof of migration readiness
- Leaving stop conditions undefined to preserve schedule flexibility
- Using dual-write to postpone architectural decisions
- Beginning cutover planning before mirrored reads or equivalent validation exists
- Letting the source environment drift during the rollback window
- Mixing execution scope changes into the same approval path without a revised playbook

---

## Open Questions

- Which migration scenarios in this repo deserve explicit execution-pattern variants: batch, near-real-time, and event-stream-driven?
- Should future worked examples include a sample prose playbook plus a matching executable workflow file for comparison?
- What is the minimum useful evidence pack for teams that cannot run full mirrored-read infrastructure?
