# Interview Guide

Use this guide for the expert-led portion of the pre-migration assessment. The interview is not just information gathering. It is also where OSC should challenge unsupported assumptions, expose hidden complexity, and present relevant choices.

## General Rules

- Start from the intake and artifacts, not from a blank conversation.
- Ask for examples, not abstractions.
- Separate facts from assumptions.
- Name likely redesign areas explicitly.
- Record contradictions as findings, not side notes.
- Present options only when enough context exists to make them meaningful.
- If the respondent is uncertain, accept a best guess labeled as `Estimated`.
- Offer a short “not sure?” fallback instead of forcing false precision.
- When tradeoffs matter, point to a short explainer such as [architecture-option-cards.md](/opt/work/OSC/agent99/architecture-option-cards.md).
- Invite clarifying sub-questions when the respondent does not know what level of detail is expected.

## Prompting Pattern for Interviewers

Use this structure when asking questions that involve tradeoffs or uncertain facts:

1. ask the main question
2. offer a best-guess fallback
3. say what to do if the respondent is unsure
4. provide one short reference if helpful
5. invite a clarifying sub-question

Example:

- Main question: `What is the primary migration goal?`
- Not sure? `Choose the closest fit: parity, quality improvement, cost reduction, platform standardization, or risk reduction.`
- If unsure: `Label it Estimated and tell us what artifact or stakeholder would confirm it.`
- Reference: [architecture-option-cards.md](/opt/work/OSC/agent99/architecture-option-cards.md)
- Clarifying sub-question: `Do you want us to answer from a product perspective or an infrastructure perspective?`

## Session 1: Business and Product

Objectives:
- validate the real migration driver
- define success and tolerated change
- identify critical search experiences

Questions:
- What business problem is the migration supposed to solve?
- If the migration succeeds technically but users say search feels worse, what happens?
- Which search-driven journeys affect revenue, retention, or support volume?
- Which experiences must remain stable?
- Which current quirks should be preserved, and why?
- What changes would be acceptable if they improved long-term quality or maintainability?

Watch for:
- purely political migration drivers
- no measurable definition of success
- “full parity” expectations with no tradeoff discussion

Best-guess support:
- Not sure? Ask the respondent to name the dominant driver first, even if multiple drivers exist.
- Helpful reference: [architecture-option-cards.md](/opt/work/OSC/agent99/architecture-option-cards.md)
- Suggested sub-question: `Are you asking for the official objective, or the practical reason the team wants this migration?`

## Session 2: Architecture and Integration

Objectives:
- map system boundaries and dependencies
- identify ingestion, transformation, and integration constraints
- frame target-state choices

Questions:
- What systems feed Solr today?
- Where do transforms happen now?
- Which applications query search directly?
- Are there hidden reporting, admin, or SEO consumers?
- Where do write semantics rely on Solr-specific behavior?
- Which target platform constraints are already fixed?

Options to present when relevant:
- dual-write vs batch cutover
- application transforms vs ingest pipelines
- denormalize vs nested modeling
- single shared index strategy vs domain-segmented indices

Watch for:
- hidden consumers
- Solr-as-database patterns
- unsupported plugin assumptions

Best-guess support:
- Not sure? Ask for the “main known systems” first and flag likely unknown consumers for follow-up.
- Helpful reference: [pre-migration-assessment-framework.md](/opt/work/OSC/agent99/pre-migration-assessment-framework.md)
- Suggested sub-question: `Do you want current-state architecture only, or known target-state constraints too?`

## Session 3: Search and Relevance

Objectives:
- understand ranking behavior, schema complexity, and tuning maturity
- identify parity illusions early

Questions:
- Which query parsers are in use?
- What top query patterns matter most?
- Which ranking controls exist today?
- How are synonyms, boosts, and business rules governed?
- Which behaviors are actually important to preserve?
- What evidence exists for current search quality?
- How will the team evaluate BM25-related ranking drift?

Options to present when relevant:
- parity-first vs redesign-first migration posture
- “better than current” vs “same as current” acceptance model
- offline relevance baseline before planning vs parallel baseline workstream

Watch for:
- no relevance benchmark
- undocumented boost logic
- assumption that shared Lucene lineage means ranking parity

Best-guess support:
- Not sure? Ask for the top three query types and any known “good” or “bad” examples.
- Helpful reference: [risk-and-readiness-rubric.md](/opt/work/OSC/agent99/risk-and-readiness-rubric.md)
- Suggested sub-question: `What counts as enough evidence here: logs, examples, or a formal benchmark?`

## Session 4: Operations and Security

Objectives:
- assess production readiness expectations
- understand troubleshooting, DR, and compliance constraints

Questions:
- What production SLOs must survive the migration?
- What recovery posture is required?
- How is access control enforced?
- What auditability is required?
- What signals prove the difference between bad data, bad query logic, and platform failure?
- Which operational knobs the team relies on today will be lost in managed OpenSearch?
- Who owns incidents after cutover?

Options to present when relevant:
- provisioned vs serverless OpenSearch
- app-side auth filtering vs engine-enforced filtering
- snapshot-driven DR vs higher-cost near-real-time alternatives

Watch for:
- app-side filtering presented as “good enough”
- no owner for incident response
- no rollback or truth-detection strategy

Best-guess support:
- Not sure? Ask the respondent to name the current operational owner and current recovery expectation, even if informal.
- Helpful reference: [architecture-option-cards.md](/opt/work/OSC/agent99/architecture-option-cards.md)
- Suggested sub-question: `Are you asking about today’s process, or the process we think we need after migration?`

## End-of-Interview Capture

At the end of each session, capture:
- confirmed facts
- challenged assumptions
- new risks
- option areas to evaluate
- required follow-up evidence
- named decision owners
