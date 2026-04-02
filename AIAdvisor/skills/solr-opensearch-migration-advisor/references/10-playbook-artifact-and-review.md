# Migration Playbook Artifact and Review
**Scope:** Defines the migration playbook as the primary reviewable artifact for AI-assisted migration work. Covers what the playbook must contain, how assessment, design, validation, and operations outputs feed it, what should be reviewed before execution, and how to use it at approval gates. Does not define the runtime schema or submission API for any specific workflow engine.
**Audience:** O19s consultants, migration leads, product owners, platform operators, reviewers, and any team using an AI companion to prepare or approve migration work
**Last reviewed:** 2026-03-20  |  **Reviewer:** AI draft — new RFC-supporting reference

---

## Key Judgements

- **The playbook is the control artifact, not a convenience export.** If the migration is driven through an AI conversation, the playbook is how that conversation becomes reviewable, repeatable, and governable.
- **A good playbook is specific enough to execute and narrow enough to approve.** Reviewers should be able to tell exactly what stage will run, in which environment, with what prerequisites, and under what rollback conditions.
- **Assessment without a playbook becomes narrative drift.** Discovery notes and design discussions are useful, but teams need one artifact that turns findings into bounded action.
- **Validation evidence belongs next to the plan, not in a separate tribal-memory thread.** If judged relevance, traffic results, or operational thresholds are required for a decision, the playbook should point to them explicitly.
- **Approval scope should follow playbook scope.** Approvers should approve a versioned plan, not a vague intent to "keep moving."
- **Playbooks should prefer staged execution over heroic one-shot cutovers.** If the artifact does not make stage boundaries visible, reviewers will underestimate migration risk.
- **A playbook is also a communication tool.** It should be legible to non-authors: operators, reviewers, and stakeholders who need to understand what will happen next.

---

## What The Playbook Is For

The migration playbook is the durable artifact that ties together:

- source audit findings
- target design decisions
- migration stage definitions
- validation requirements
- approval gates
- rollback posture
- ownership and escalation

Use it as the reference point for:

- readiness reviews
- stage approvals
- cutover approvals
- rollback decisions
- post-stage retrospectives

If the AI can explain a migration plan but cannot leave behind a bounded artifact, the process is not mature enough for enterprise migration work.

---

## Minimum Required Sections

Every migration playbook should include at least these sections.

### 1. Metadata

- playbook identifier
- version or revision
- owner
- target environment
- source environment
- current status (`draft`, `in review`, `approved`, `executing`, `completed`, `rolled back`, `superseded`)

### 2. Migration Goal

- what workload is being migrated
- which collections, indexes, or applications are in scope
- what "done" means for this stage

### 3. Scope Boundaries

- what is included
- what is intentionally excluded
- assumptions the plan depends on
- actions that remain manual

### 4. Source Summary

- source collections or cores
- important schema, analyzer, and query patterns
- known source-side constraints
- major risks discovered during assessment

### 5. Target Design Summary

- target index topology
- mapping and analyzer choices
- aliases and routing assumptions
- application integration assumptions

### 6. Stage Plan

For each stage:

- stage name
- objective
- prerequisites
- actions to run
- expected duration
- success criteria
- stop conditions
- owner

### 7. Validation Plan

- functional checks
- judged relevance checks
- traffic comparison or shadow validation
- operational thresholds
- evidence required to pass

### 8. Approval Gates

- which stages need approval
- who can approve
- what evidence they must review
- what conditions must be satisfied

### 9. Rollback Plan

- rollback triggers
- rollback actions
- rollback owner
- time window for effective rollback

### 10. Open Questions And Risks

- unresolved risks
- accepted risks
- blockers
- dependencies on other teams or systems

---

## Recommended Supporting Attachments

Keep the main playbook concise. Attach or link supporting evidence instead of bloating the core plan.

Common attachments:

- assessment summary
- risk register
- target design review
- query translation samples
- judged relevance report
- sample result diffs
- operational dashboard links
- cutover checklist
- rollback checklist
- incident or exception notes

Reviewers should be able to trace every important stage decision back to evidence.

---

## How Earlier Artifacts Feed The Playbook

The playbook should not be written from scratch in isolation. It should be assembled from earlier outputs.

| Upstream artifact | Feeds which playbook section |
|---|---|
| Pre-migration assessment | source summary, scope, major risks, complexity posture |
| Target design review | topology, mappings, analyzer choices, application assumptions |
| Validation and cutover plan | validation section, go/no-go thresholds, cutover evidence |
| Operations runbook | metrics, alert posture, rollback triggers, watch windows |
| Approval and safety policy | approval gates, escalation rules, allowed execution boundaries |

If these inputs do not exist yet, the playbook is premature.

---

## What Reviewers Should Check

### Review For Completeness

- Is the migration goal clear?
- Is the scope bounded?
- Are the environments named correctly?
- Are the owners named?
- Are prerequisites concrete?

### Review For Safety

- Does the plan stay within approved environments and access boundaries?
- Are dangerous actions clearly marked?
- Are approval gates explicit?
- Is rollback realistic, not symbolic?

### Review For Technical Credibility

- Does the target design reflect the assessed source reality?
- Are the validation methods strong enough for the workload?
- Are stage success criteria measurable?
- Are operational limits and watch windows stated clearly?

### Review For Operational Fit

- Can operators tell what happens on cutover day?
- Are stop conditions obvious?
- Is there a clear escalation path?
- Can the team execute this with available staffing?

---

## Review Questions That Matter Most

These questions catch more weak playbooks than long formatting checklists do.

1. What exactly will happen if we approve this?
2. What evidence says this stage is ready?
3. What would make us stop?
4. Who has authority to approve, pause, or roll back?
5. What is still uncertain?

If the playbook cannot answer those five questions cleanly, it is not ready.

---

## Example Stage Skeleton

Use a stage-oriented structure rather than a monolithic document.

```text
Stage: Shadow Traffic Validation
Objective: Compare OpenSearch results and operational behavior under representative live traffic without exposing end users.
Prerequisites:
- target index loaded with agreed snapshot
- query translation layer deployed in validation path
- judged query set baselined
- monitoring dashboards live
Actions:
- replay 10% mirrored read traffic for 24 hours
- collect latency, error-rate, and result-diff samples
- review top regressions daily
Success criteria:
- no critical functional failures
- relevance acceptance thresholds met or deviations accepted explicitly
- latency and error rates within agreed limits
Stop conditions:
- sustained target instability
- unexplained critical result regressions
- replay lag beyond threshold
Owner: Migration lead
Approval required to proceed to next stage: Yes
```

This is the level of specificity reviewers need.

---

## Approval Gate Pattern

Use a simple gate structure:

| Gate | Typical decision | Required evidence |
|---|---|---|
| **Assessment complete** | proceed to target design and implementation planning | source audit, risk register, scope confirmation |
| **Design approved** | proceed to build, mapping, and query work | target design review, unresolved risk list |
| **Validation approved** | proceed to shadow traffic or staged cutover | judged relevance report, functional checks, operational baseline |
| **Cutover approved** | expose production traffic | cutover checklist, rollback owner, current telemetry, issue review |
| **Completion approved** | close migration stage | post-cutover evidence, incident summary, handoff notes |

Do not overload a single approval to cover all downstream stages.

---

## Decision Heuristics

- If reviewers cannot answer "what exactly happens next if we approve this?" the playbook is not ready.
- If stage success criteria are qualitative but not measurable, tighten the playbook before asking for approval.
- If the executable workflow is easier to read than the playbook, the human-review artifact is underspecified.
- If unresolved risks are being pushed into later tuning with no owner, treat that as a sign the stage boundary is weak.
- If one approval is being used to justify multiple later stages, split the playbook or add explicit gate records.

---

## Common Failure Modes

- Treating the playbook as a generated form nobody really reads
- Omitting explicit stop conditions because the team wants flexibility
- Folding unresolved risks into "future tuning" with no owner
- Approving a plan with no named rollback authority
- Writing one huge plan instead of stage-bounded approvals
- Letting supporting evidence live only in chat transcripts or meeting notes
- Treating "approved once" as permanent consent after scope drift

---

## Relationship To Runtime Workflow Files

In some systems the executable artifact may be a `workflow-config.yaml`, `.wf.yaml`, or another machine-readable object. That executable file is not the whole playbook.

Use this distinction:

- **Playbook:** human-reviewable migration plan with scope, evidence, approvals, and rollback posture
- **Workflow file:** machine-readable execution payload for a specific stage or toolchain

The workflow file may be generated from the playbook, but reviewers should not be forced to infer safety and intent from low-level execution syntax alone.

---

## Suggested Default Artifact Set

For most migrations, the minimum useful artifact set is:

- assessment summary
- risk register
- target design review
- migration playbook
- validation report
- cutover checklist
- rollback checklist

This is small enough to maintain and strong enough to support approval discipline.

---

## Open Questions

- Which portions of the playbook should be standardized across all migrations vs left scenario-specific?
- How should the repo represent playbooks in worked examples: prose-first markdown, executable YAML plus narrative wrapper, or both?
- What is the right lowest-friction approval record format for teams not using a formal change-management system?
