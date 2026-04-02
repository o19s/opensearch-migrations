# Success Definition Template

Use this artifact to turn migration intent into an approval-ready definition of success.

The goal is to answer, in one place:

- what is in scope
- what counts as success
- what evidence is required
- what tradeoffs are acceptable
- who can approve progress

This should be completed before implementation planning hardens and definitely before any cutover approval discussion.

---

## Document Metadata

- Engagement:
- Prepared by:
- Date:
- Version:
- Status: `draft` / `in review` / `approved`

## 1. Migration Scope

### In Scope

- [user journeys, services, collections, or applications]

### Explicitly Out Of Scope

- [excluded workloads, experiences, or adjacent systems]

### Why This Scope Exists

- [one short paragraph on why this slice is the right first migration target]

## 2. Business Outcomes

State the business outcomes the migration is meant to achieve.

Examples:

- reduce operational fragility
- improve search quality for top revenue journeys
- simplify application maintenance
- remove manual search configuration steps from normal operations

### Success Statements

- [Outcome 1 in stakeholder language]
- [Outcome 2 in stakeholder language]
- [Outcome 3 in stakeholder language]

## 3. Technical Guardrails

These are the non-negotiable technical conditions for success.

- latency guardrails:
- error-rate guardrails:
- freshness guardrails:
- rollback posture:
- environment or access constraints:

## 4. Validation Evidence Required

List the evidence that must exist before approval gates can pass.

- judged relevance report
- functional smoke test results
- traffic comparison or shadow-read findings
- operational dashboard review
- rollback checklist
- [other evidence]

## 5. Approval Thresholds

State what has to be true before the migration can move forward.

### Assessment Gate

- [required conditions]

### Validation Gate

- [required conditions]

### Cutover Gate

- [required conditions]

## 6. Accepted Tradeoffs

Document the tradeoffs that are acceptable so reviewers do not improvise later.

Examples:

- small ranking changes in low-volume queries
- staged rollout instead of same-day full cutover
- temporary operational overhead during dual-write

- [Tradeoff 1]
- [Tradeoff 2]

## 7. Non-Goals

These are things the migration is not trying to solve in this phase.

- [non-goal 1]
- [non-goal 2]
- [non-goal 3]

## 8. Open Risks And Assumptions

- [risk or assumption 1]
- [risk or assumption 2]
- [risk or assumption 3]

## 9. Approvers

| Name | Role | Approval area |
|---|---|---|
|  |  |  |
|  |  |  |

## 10. Approval Record

| Version | Decision | Date | Notes |
|---|---|---|---|
|  |  |  |  |

---

## Review Questions

Before approval, confirm:

- Does this define success clearly enough to reject weak progress?
- Are the user journeys and systems in scope explicit?
- Would an operator know what evidence is required before cutover?
- Are tradeoffs documented instead of left to verbal agreement?
- Are named approvers attached to meaningful gates?
