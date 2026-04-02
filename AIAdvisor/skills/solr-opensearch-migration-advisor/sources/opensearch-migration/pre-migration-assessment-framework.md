# Pre-Migration Assessment Framework

Use this framework to run an expert-guided Solr-to-OpenSearch pre-migration assessment before any tactical implementation work begins.

The goal is to:
- collect enough evidence to understand the current state
- surface hidden risks and unsupported assumptions
- educate the client on architectural choices and tradeoffs
- produce a strategic migration plan with explicit decisions, gates, and unknowns

This is not an implementation plan. It is a readiness, strategy, and decision-making artifact.

## Outcomes

By the end of the assessment, the team should have:
- a documented current-state view
- a prioritized risk register
- a set of target-state architecture options
- a recommended migration posture
- explicit readiness gates
- a phased strategic plan
- a decision log with owners

## Recommended Delivery Model

Use a hybrid engagement model:

1. `Async intake`
   Collect structured answers and required artifacts before interviews.
2. `Expert review`
   OSC reviews evidence, pre-scores risk, and identifies contradictions or gaps.
3. `Guided interviews`
   OSC leads role-specific sessions to validate facts and challenge assumptions.
4. `Draft readout`
   OSC produces a first-pass assessment, options, risks, and recommended direction.
5. `Client tuning`
   Product, architecture, and delivery owners refine assumptions and priorities.
6. `Final strategic plan`
   OSC publishes a revised version with explicit next-step gates.

Recommended iteration count:
- Typical: `3-5` cycles
- Fewer than 3: risk of shallow discovery
- More than 5: often indicates unresolved ownership or unstable scope

## Assessment Phases

### Phase 0: Setup

Before intake begins:
- identify executive sponsor
- identify product owner
- identify architecture owner
- identify search/domain expert
- identify operations/security owner
- agree on assessment scope
- define delivery calendar and review cadence
- establish a shared workspace for evidence and outputs

### Phase 1: Intake and Evidence Collection

Goal:
- capture baseline facts, constraints, and artifacts

Outputs:
- completed intake questionnaire
- artifact inventory
- evidence gap list
- initial risk/readiness score

### Phase 2: Expert-Led Discovery

Goal:
- validate answers
- challenge assumptions
- identify unsupported migration expectations
- present relevant architecture choices

Outputs:
- interview notes
- contradiction log
- decision candidates
- updated risk register

### Phase 3: Strategic Synthesis

Goal:
- translate collected evidence into an actionable migration posture

Outputs:
- architecture options
- recommended strategy
- phased plan
- readiness gates
- known unknowns

### Phase 4: Client Review and Tuning

Goal:
- let the client challenge assumptions and refine priorities before implementation planning

Outputs:
- revised strategic plan
- approved assumptions
- named decision owners

## Intake Questionnaire

Keep the intake concise enough to complete, but opinionated enough to expose risk. Require each answer to include confidence:
- `Known`
- `Estimated`
- `Unknown`

### Section 1: Business Drivers and Success Criteria

Questions:
- Why is migration being considered now?
- What business outcome is expected from the migration?
- Is the goal parity, improvement, platform modernization, cost reduction, or risk reduction?
- What does success look like for users, operators, and leadership?
- What regressions are acceptable, and which are not?
- What timeline pressures are external versus self-imposed?

Guidance to bake in:
- if no customer-visible benefit exists, challenge whether migration should start at all
- if success is not measurable, implementation should not begin

### Section 2: Product and Search Experience

Questions:
- What user journeys depend on search?
- What search experiences exist today: keyword, browse, facets, autocomplete, recommendations, alerts, related content?
- Which experiences are business-critical?
- Which known complaints or search quality problems exist today?
- Which current behaviors are truly valuable versus merely familiar?

Guidance to bake in:
- require examples of critical queries and pages
- separate “must preserve” from “nice to preserve”

### Section 3: Current Solr Footprint

Questions:
- Which collections, cores, or domains are in scope?
- Which Solr features are in active use?
- Which custom request handlers, update processors, plugins, or scripts exist?
- Which analyzers, synonyms, stopwords, and linguistic assets are in use?
- Are nested docs, block joins, grouping, MLT, spellcheck, streaming expressions, or CDCR used?

Guidance to bake in:
- any custom component should be treated as redesign risk until proven otherwise
- any unsupported feature must trigger an option discussion, not a parity promise

### Section 4: Data and Content

Questions:
- What content sources feed Solr?
- What is the document volume, freshness requirement, and growth rate?
- How is content transformed before indexing?
- Who owns the content model and metadata quality?
- Are there known content gaps, duplication issues, or stale data problems?

Guidance to bake in:
- content access and ownership are often the critical path
- separate source-of-truth issues from search-engine issues

### Section 5: Queries and Relevance

Questions:
- What are the top query patterns?
- Which query parsers are used?
- What boost rules, business ranking logic, or query rewrites exist?
- What relevance metrics or analytics exist today?
- Is there a judgment set, analytics baseline, or replay capability?

Guidance to bake in:
- if no baseline exists, implementation should pause until one is defined
- do not treat “looks good” as sufficient evaluation

### Section 6: Operations and Reliability

Questions:
- What are the availability, latency, and freshness SLAs?
- What backup, failover, and DR patterns exist now?
- What current incidents or operational pain points exist?
- Who is on call, and what skills do they have?
- What monitoring and alerting signals are used today?

Guidance to bake in:
- require RTO/RPO expectations
- ask which operational capabilities must survive the migration

### Section 7: Security and Compliance

Questions:
- How is access control enforced today?
- Is filtering done in the app, engine, or both?
- What regulated or sensitive data may enter the index?
- What auditability or explainability obligations exist?
- Are there tenant isolation requirements?

Guidance to bake in:
- security translation is never a side topic
- snippets, autocomplete, and logs can leak sensitive data even when primary result sets are filtered

### Section 8: Target-State Assumptions

Questions:
- Why OpenSearch, and which flavor: AWS managed, self-managed, or other?
- Is the team considering provisioned or serverless?
- What platform constraints already exist: region, VPC, IAM, procurement, budget?
- Which assumptions about parity or ease of migration are already being made?

Guidance to bake in:
- explicitly ask which assumptions are facts versus preferences

### Section 9: Team, Ownership, and Governance

Questions:
- Who owns search strategy?
- Who owns relevance decisions?
- Who owns implementation?
- Who can approve tradeoffs and de-scoping?
- Who can stop a rollout?

Guidance to bake in:
- missing decision ownership is a major strategic risk

## Evidence and Artifact Request List

Do not rely on survey responses alone. Collect evidence.

Required artifacts:
- current architecture diagram
- Solr schema/configset
- sample collection definitions
- request handler list
- custom plugin or update processor inventory
- top query logs for the last 30 days
- search analytics or top-task reports
- synonyms, stopwords, dictionaries, and taxonomies
- sample documents and field inventory
- performance baselines: p50, p95, p99, indexing throughput, index size
- SLA and incident records
- current backup/restore and DR process
- security model documentation
- roadmap and major timeline constraints

Useful additional artifacts:
- screenshots of critical search experiences
- decision records from earlier platform discussions
- current pain-point list from support or product teams
- examples of failed or difficult queries

For each missing artifact, record:
- owner
- requested date
- business impact if absent

## Expert-Led Interview Design

Do not run one generic meeting if role-specific sessions are feasible.

Recommended sessions:

1. `Business and Product`
   Focus on goals, success criteria, tolerated change, and user impact.
2. `Architecture and Integration`
   Focus on system boundaries, ingestion model, application dependencies, and target platform constraints.
3. `Search and Relevance`
   Focus on schema, analyzers, query patterns, tuning assets, and known search behavior.
4. `Operations and Security`
   Focus on SLAs, observability, DR, ownership, authz, and compliance obligations.

For each session:
- start with what the intake claims
- validate facts
- look for contradictions
- expose hidden consumers and undocumented behavior
- present 2-4 relevant target-state options
- capture decision candidates and open questions

## Architecture Option Cards

For each major decision, prepare a short option card with:
- decision area
- options considered
- when each option fits
- advantages
- disadvantages
- risk level
- cost/complexity implications
- required client decisions
- OSC recommendation

Recommended option-card topics:
- parity-first migration vs redesign-first migration
- dual-write cutover vs batch cutover
- denormalization vs nested or join-style models
- application transforms vs ingest pipeline transforms
- provisioned vs serverless OpenSearch
- app-side authorization vs engine-enforced filtering
- exact behavioral preservation vs “better than current” acceptance model
- single index strategy vs domain-segmented index strategy

## Readiness and Risk Scoring

Use a simple score to guide discussion, not to create false precision.

Score each category on a `0-3` scale:
- `0` = unknown or missing
- `1` = weak / partially understood
- `2` = mostly understood with some gaps
- `3` = strong evidence and clear ownership

Recommended scored categories:
- business clarity
- success criteria
- content access
- feature inventory completeness
- query/relevance maturity
- operational readiness
- security/compliance clarity
- target platform clarity
- ownership/governance
- measurement and evidence quality

Suggested overall interpretation:
- `0-12`: not ready for planning beyond discovery
- `13-20`: partial readiness, major strategic gaps remain
- `21-26`: viable for strategic planning, not yet for implementation
- `27-30`: strong planning readiness, can define gated implementation roadmap

Also flag risk level separately:
- `Low`
- `Medium`
- `High`
- `Critical`

High-risk conditions should override a “good” score if they affect:
- security
- unsupported features
- content access
- success criteria
- ownership gaps

## Readiness Gates

Implementation planning should not begin until these are explicitly reviewed:

- success criteria are documented and approved
- product owner and architecture owner are named
- source content access is confirmed
- Solr feature inventory is complete
- top query patterns are known
- relevance baseline exists or a baseline plan is approved
- target platform constraints are validated
- security model is documented
- rollback posture is defined at the strategic level
- major unsupported assumptions are called out explicitly

If these are not met, the assessment should say:
`Do not begin implementation planning yet. Continue discovery.`

## Standard Output Package

The client-facing output should include the following sections.

### 1. Executive Summary

Include:
- migration driver
- current readiness level
- highest-priority risks
- recommended migration posture
- immediate next decisions

### 2. Current-State Assessment

Include:
- in-scope systems and search experiences
- Solr feature usage summary
- content and query maturity summary
- operational and security posture summary

### 3. Key Findings

Include:
- top risks
- parity illusions
- unsupported assumptions
- missing evidence
- opportunities to improve the target-state design

### 4. Architecture Options and Recommendation

Include:
- major decisions
- option comparisons
- recommended approach
- rationale and tradeoffs

### 5. Risk Register

Include columns for:
- risk
- impact
- likelihood
- severity
- evidence
- mitigation
- owner
- status

### 6. Readiness Score and Gates

Include:
- scored categories
- gating failures
- recommended next-step sequence

### 7. Strategic Migration Plan

Keep it phase-based and non-tactical.

Suggested phases:
- discovery completion
- target-state design
- measurement and validation design
- implementation planning
- execution readiness
- cutover readiness

For each phase include:
- objective
- entrance criteria
- exit criteria
- owners
- key outputs

### 8. Decision Log

Track:
- decision
- owner
- status
- date
- rationale
- downstream impact

### 9. Assumptions and Unknowns

Separate these clearly:
- assumptions accepted for planning
- unknowns requiring evidence
- unresolved risks that block implementation

## Recommended Iteration Rhythm

Use this cadence:

1. `Pass 1`
   Gather facts, evidence, and obvious risks.
2. `Pass 2`
   Challenge assumptions and present architecture options.
3. `Pass 3`
   Publish draft strategy and readiness gates.
4. `Pass 4`
   Tune with client stakeholders and finalize the strategic plan.

Optional additional pass:
- executive or steering review if the migration has major funding or org-change implications

## Expert Guidance Patterns to Bake In

Make the assessment opinionated by embedding guidance directly into prompts.

Examples:

- If custom update processors exist:
  treat as redesign risk until replacement design is reviewed.
- If no relevance baseline exists:
  require a measurement plan before implementation planning.
- If the team expects exact parity:
  require explicit signoff on where parity is realistic and where redesign is required.
- If content ownership is unclear:
  elevate as a delivery risk immediately.
- If security filtering is app-side only:
  require explicit review of leakage risk through snippets, autocomplete, and logs.

## What Good Looks Like

A strong assessment result will:
- challenge the premise when migration is not clearly justified
- distinguish facts from assumptions
- identify what must be preserved versus what should be redesigned
- give the client a small set of real choices, not a vague pile of considerations
- make ownership and evidence gaps visible
- end with a gated strategic plan rather than implementation tasks

## Suggested Next Assets to Create

To operationalize this framework, create:
- `assessment-intake-questionnaire.md`
- `artifact-request-checklist.md`
- `interview-guide.md`
- `architecture-option-cards.md`
- `risk-and-readiness-rubric.md`
- `strategic-readout-template.md`

