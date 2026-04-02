# Approval and Safety Tiers
**Scope:** Governance model for AI-assisted migration work: what may be observed, proposed, or executed; where human approval is mandatory; what evidence is required before action; and when to escalate to a human operator. Covers migration planning, validation, and execution guidance. Does not define runtime enforcement code.
**Audience:** O19s consultants, migration leads, product owners, platform operators, and any team using an AI companion during migration
**Last reviewed:** 2026-03-20  |  **Reviewer:** AI draft — new RFC-supporting reference

---

## Key Judgements

- **Autonomy without explicit boundaries is just hidden risk.** Teams trust AI-assisted migration only when they can point to a clear model of what the AI may do, what it may only suggest, and what it must never do on its own.
- **Read-only actions are not automatically safe.** A read can still leak secrets, trigger rate limits, or create false confidence if the interpretation is poor. "Observe" needs scope boundaries, not just lower privilege.
- **Approval must be tied to evidence, not enthusiasm.** A human approval step is useful only if the reviewer is approving a concrete artifact with concrete consequences.
- **The dangerous failures are usually gradual, not dramatic.** Silent relevance regressions, partial mappings, and stale data are more likely than spectacular crashes. Safety tiers must therefore cover quality and integrity, not just destructive operations.
- **An approved playbook is not blanket consent for improvisation.** The AI may execute within the bounds of the approved plan and evidence. Crossing those bounds requires renewed human approval.
- **Production traffic cutover should always have a named human owner.** The AI can recommend, summarize, and monitor; it should not unilaterally decide the moment to expose all users to the new engine.
- **Rollback authority matters as much as execution authority.** If nobody is empowered to stop or reverse the migration, the team will push through weak signals because the process has no off-ramp.
- **Auditability is part of the product, not compliance garnish.** If you cannot reconstruct what the AI did, what evidence it cited, and who approved it, the migration process is not mature enough for enterprise trust.

---

## The Three Tiers

Use three action tiers throughout the migration.

| Tier | Purpose | Default posture |
|---|---|---|
| **Observe** | Gather and summarize information | Allowed within approved read scope |
| **Propose** | Recommend actions and explain tradeoffs | Allowed; does not change systems |
| **Execute** | Perform an action or submit work to a system | Requires explicit approval or prior approved playbook coverage |

Do not invent extra tiers unless the client has a strong governance reason. Complexity weakens adoption.

---

## Tier 1: Observe

### Typical Actions

- inspect source cluster metadata
- inspect target cluster health and settings
- summarize schema, mappings, analyzers, and query patterns
- read dashboards, logs, and migration telemetry
- compare document counts and sample results
- summarize application code that appears migration-relevant

### Observe Constraints

Observe is still bounded by:

- approved data sources
- approved credentials and roles
- approved environments
- privacy and compliance rules

Examples of Observe actions that still need caution:

- reading production query logs containing sensitive text
- inspecting mappings/settings in restricted environments
- collecting application code snippets with embedded secrets

### Evidence Expectations

Observed outputs should produce durable artifacts where useful:

- assessment summaries
- risk registers
- source audit notes
- target readiness reports
- operational findings

If the observation is important enough to influence a migration decision, write it down.

---

## Tier 2: Propose

### Typical Actions

- recommend target index design
- suggest query rewrites or analyzer changes
- draft transforms and migration playbooks
- recommend scaling, retry, or cutover timing
- propose rollback when indicators degrade
- draft application patches or refactor plans

### Proposal Requirements

A useful proposal includes:

- the recommended action
- why it is needed
- expected impact
- known risks
- required approvals
- what evidence the recommendation is based on

Bad proposal:

- "Scale to 8 workers."

Good proposal:

- "Scale document backfill workers from 4 to 8 because replay lag has grown for 40 minutes while CPU and bulk rejection metrics remain below thresholds. Risk: higher write pressure on the target cluster. Approval required from platform owner."

---

## Tier 3: Execute

### Typical Actions

- generate or update a concrete migration artifact
- submit a validated playbook/workflow
- start or pause a backfill stage
- run approved validation checks
- trigger an approved replay or test stage
- apply approved non-destructive configuration changes within plan boundaries

### Execution Rule

Execution is allowed only when one of these is true:

1. A human explicitly approves the action now
2. The action is explicitly covered by an already approved playbook and remains within the documented bounds of that playbook

If neither is true, the AI stops at Propose.

---

## Always-Requires-Human-Approval Actions

These actions should always require an explicit human checkpoint:

- production traffic cutover
- rollback from a live cutover
- destructive changes to source systems
- destructive changes to target data or mappings
- IAM, credential, or access policy changes
- cluster resizing that changes cost or blast radius materially
- acceptance of unresolved critical regressions
- any action that exceeds the approved playbook scope

This list should be short, memorable, and non-negotiable.

---

## Never-Autonomous Actions

These should not be performed autonomously even if the AI is otherwise trusted:

- deleting source data
- deleting target production indexes without direct operator intent
- changing production traffic routing with no human confirmation
- altering security/compliance controls on its own judgment
- waiving required validation evidence because of schedule pressure
- inventing an unreviewed migration path in response to unexpected failures

If the situation is novel enough that the AI is improvising, it is no longer in safe autonomous territory.

---

## Approval Objects

Approvals should attach to a concrete object, not a vague conversation.

Good approval objects:

- assessment summary
- risk register
- target design review
- query validation report
- playbook / workflow config
- cutover checklist
- rollback recommendation

For each approval object, capture:

- artifact version or identifier
- approver name and role
- date/time
- decision (`approved`, `approved with conditions`, `rejected`)
- conditions or constraints

---

## Evidence Required Before Execution

Before the AI executes within a migration workflow, require evidence appropriate to the stage.

### Before Running Migration Stages

- source and target identified correctly
- credentials and environment scope confirmed
- relevant playbook validated
- rollback path identified

### Before Recommending Cutover

- judged relevance results available
- major regressions explained or accepted
- functional smoke tests passed
- operational dashboards healthy
- rollback trigger and owner confirmed

### Before Recommending Rollback

- failure threshold crossed or clearly trending toward breach
- evidence summarized
- impact of rollback understood
- owner available to approve and carry it out

---

## Escalation Triggers

Move from AI-led flow to human-led operation when any of these occur:

- approval ownership is unclear
- evidence sources disagree materially
- critical regressions remain unexplained
- the migration deviates from the approved playbook
- the AI cannot access enough trustworthy data to justify its recommendation
- security, compliance, or access questions become part of the decision path
- rollback conditions may be met

Escalation is not failure. It is correct operation.

---

## Operator Handoff Pattern

When escalating, the AI should hand off in a compact, decision-ready format:

1. Current state
2. Action being considered
3. Evidence for and against
4. Risks of acting
5. Risks of waiting
6. Recommended human decision

This keeps the AI useful without pretending it should own the decision.

---

## Audit Trail Requirements

At minimum, record:

- what the AI observed
- what it proposed
- what was executed
- what evidence was cited
- who approved execution
- what changed in the environment
- what the result was

If the process produces no audit trail, it will be hard to defend after an incident or even during routine stakeholder review.

---

## Compact Default Policy

Use this default posture unless the client requires stricter controls:

- `Observe`: allowed on approved systems and datasets
- `Propose`: always allowed; no system mutation
- `Execute`: allowed only with current human approval or approved-playbook coverage
- `Cutover`: human approval always required
- `Rollback`: human approval always required
- `Security/compliance changes`: human approval always required
- `Source-side destructive actions`: never autonomous

---

## Decision Heuristics

- If an action changes production behavior and the approval object is vague, stop at `Propose`.
- If the evidence pack is incomplete or contradictory, escalate to a human owner rather than interpreting ambiguity optimistically.
- If a proposed action falls outside the approved playbook scope, require a renewed approval cycle.
- If no named human can authorize rollback, do not treat the system as execution-ready.
- If the team cannot reconstruct what the AI observed, proposed, and executed, treat the process as under-governed even if no incident has happened yet.

---

## Common Mistakes

- Treating "read-only" as if it eliminates all governance concerns
- Letting a stakeholder verbally approve something without a versioned artifact
- Assuming an approved playbook covers ad hoc recovery actions that were never reviewed
- Allowing the AI to interpret weak evidence as sufficient because the project is behind schedule
- Forgetting to define who can say no at cutover time
- Logging system actions but not the reasoning and evidence that led to them

---

## Open Questions / Evolving Guidance

- How much of this policy should be machine-readable versus purely procedural?
- What is the right minimum audit trail for smaller migrations that do not have formal change-management systems?
- How should approval policy adapt for low-risk sandbox migrations versus production cutovers?
- What additional controls are needed when the AI can scan application code and propose patches across large repositories?
