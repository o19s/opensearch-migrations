# Strategic Readout Template

Use this template to present the results of the pre-migration assessment.

## Readout Style Guidance

The readout should help the client make decisions, not just receive findings.

When presenting options or gaps:
- offer a recommended default when the evidence is incomplete
- distinguish `Known`, `Estimated`, and `Unknown`
- point the client to the shortest useful explainer
- state what clarification question would unlock the next decision
- make it easy for the client to refine or challenge the recommendation

Useful references:
- [pre-migration-assessment-framework.md](../../01-sources/opensearch-migration/pre-migration-assessment-framework.md)
- [architecture-option-cards.md](architecture-option-cards.md)
- [risk-and-readiness-rubric.md](risk-and-readiness-rubric.md)

## 1. Executive Summary

- migration driver
- current readiness level
- top risks
- recommended migration posture
- immediate decisions required

## 2. Scope

- in-scope search experiences
- in-scope systems and content domains
- out-of-scope areas
- major dependencies

## 3. Current-State Assessment

### Business and Product

- primary business drivers
- success criteria
- tolerated regressions
- critical user journeys

### Search and Relevance

- query pattern summary
- ranking logic summary
- tuning asset summary
- major parity risks

### Content and Data

- content source summary
- document volume and freshness
- transformation and enrichment flow
- ownership and quality concerns

### Operations and Security

- SLA/SLO expectations
- monitoring and DR posture
- security model summary
- compliance constraints

## 4. Key Findings

List the highest-value findings first.

Suggested subsections:
- unsupported assumptions
- hidden dependencies
- redesign requirements
- missing evidence
- organizational risks

For each major finding, include when relevant:
- best current interpretation
- confidence level
- what evidence would confirm or change the conclusion

## 5. Architecture Options

For each decision area include:
- decision area
- options considered
- when each fits
- key tradeoffs
- OSC recommendation
- recommended default if the client is not ready to decide yet
- what question the client should ask next if they want to refine the answer

Suggested decision areas:
- migration posture: parity-first vs redesign-first
- cutover model: dual-write vs batch
- data model: denormalize vs nested
- transform location: application vs ingest pipeline
- platform model: provisioned vs serverless
- authorization strategy: app-side vs engine-side enforcement

## 6. Recommendation

State:
- recommended target posture
- rationale
- major tradeoffs accepted
- explicit non-goals

If confidence is partial:
- say which recommendations are provisional
- say what evidence would upgrade them from estimated to confirmed

## 7. Risk Register

Use a table with:
- risk
- evidence
- impact
- likelihood
- severity
- mitigation
- owner
- status

## 8. Readiness Score and Gates

Include:
- category scores
- gating failures
- gate recommendation statement

## 9. Strategic Migration Plan

Keep this non-tactical and phase-based.

Suggested phases:

### Phase A: Discovery Completion

- objective
- entrance criteria
- exit criteria
- owners
- outputs

### Phase B: Target-State Design

- objective
- entrance criteria
- exit criteria
- owners
- outputs

### Phase C: Measurement and Validation Design

- objective
- entrance criteria
- exit criteria
- owners
- outputs

### Phase D: Implementation Planning

- objective
- entrance criteria
- exit criteria
- owners
- outputs

### Phase E: Execution Readiness

- objective
- entrance criteria
- exit criteria
- owners
- outputs

## 10. Decision Log

Use a table with:
- decision
- owner
- status
- rationale
- date
- downstream impact

## 11. Assumptions and Unknowns

Separate:
- planning assumptions accepted for now
- unresolved unknowns requiring evidence
- blockers that prevent implementation planning

## 12. Immediate Next Steps

List only the next strategic actions, for example:
- obtain missing evidence
- resolve decision ownership
- validate unsupported feature usage
- establish relevance baseline
- confirm target platform constraints

For each next step, optionally include:
- best owner guess
- what “done” looks like
- what clarifying question should be answered first

