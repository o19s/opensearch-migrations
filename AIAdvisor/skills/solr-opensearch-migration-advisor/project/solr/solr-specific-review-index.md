# Solr-Specific Review Index

Date: 2026-03-23

This is the top-level index for the Solr-specific review lane in the OSC/Amazon
query-translation discussion.

Use this page when you want the shortest path through the current internal notes.

## Recommended Reading Order

1. [solr-specific-work-plan.md](/opt/work/OSC/agent99/project/solr/solr-specific-work-plan.md)
2. [upstream-query-translation-overview.md](/opt/work/OSC/agent99/project/upstream/upstream-query-translation-overview.md)
3. [upstream-query-translation-assessment.md](/opt/work/OSC/agent99/project/upstream/upstream-query-translation-assessment.md)
4. [solr-query-coverage-matrix.md](/opt/work/OSC/agent99/project/solr/solr-query-coverage-matrix.md)

Then go deeper by topic:

- [solr-fq-review-note.md](/opt/work/OSC/agent99/project/solr/solr-fq-review-note.md)
- [solr-edismax-review-note.md](/opt/work/OSC/agent99/project/solr/solr-edismax-review-note.md)
- [solr-highlighting-analyzer-parity-note.md](/opt/work/OSC/agent99/project/solr/solr-highlighting-analyzer-parity-note.md)
- [solr-integrated-request-test-shapes.md](/opt/work/OSC/agent99/project/solr/solr-integrated-request-test-shapes.md)
- [amazon-query-translation-questions.md](/opt/work/OSC/agent99/project/upstream/amazon-query-translation-questions.md)

## What These Notes Are Trying To Do

This set is not trying to own the entire upstream transform architecture.

It is trying to make sure OSC stays sharp on the Solr-specific questions that are most likely to
create:

- migration drift
- false confidence
- advisor/runtime inconsistency
- overclaiming of support

## Current Solr-Specific Takeaways

### 1. `q` semantics are still the main open risk surface

The parser/transform/orchestrator foundation upstream is good, but request-level `q` behavior is
still the most important place to watch for semantic drift.

### 2. `fq` and `edismax` still deserve top-tier priority

These are central to many real Solr workloads and should remain ahead of lower-frequency feature
slices in OSC's prioritization language.

### 3. Integrated requests matter more than isolated feature wins

Feature-by-feature progress is useful, but migration confidence rises mainly when combined request
shapes behave coherently.

### 4. Highlighting parity is not just request translation

Highlighting quality depends on analyzer parity, field design, and method/term-vector assumptions,
not just `hl.*` syntax mapping.

### 5. There is an architecture-convergence question worth tracking

The current `#2458` `query-q.ts` path appears separate from the newer merged query-engine
orchestrator path, and upstream review comments suggest that convergence is still an open question.

## Best Immediate Use Cases

Use these notes when:

- replying to Amazon about query-translation priorities
- deciding which Solr topics OSC should push hardest
- checking whether a new upstream PR changes the current priority picture
- preparing combined-request test suggestions
- keeping AI Advisor messaging aligned with actual runtime scope

## Practical Short Version

If you only need the current OSC position in a few lines:

- foundation direction is good
- `fq` and `edismax` should remain explicit top-tier priorities
- integrated request testing matters more than isolated param wins
- highlighting parity must be discussed together with analyzer parity
- advisor messaging should mirror runtime warning/partial-support reality
