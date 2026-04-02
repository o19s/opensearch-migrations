# Pre-Migration Assessment: Source Audit and Readiness Control
**Scope:** How to inventory a Solr deployment before migration: source-side discovery, schema and query audit, operational baseline, organizational readiness, and hidden-complexity detection. Covers what evidence to gather before target design and implementation. Does not cover OpenSearch target design or cutover validation.
**Audience:** O19s consultants, engagement leads, solution architects, and migration owners
**Last reviewed:** 2026-03-20 | **Reviewer:** AI draft — expanded for Phase 1 advisory use

---

## Key Judgements

- **Do not design the target until you can explain the source.** Most migration mistakes happen because the team starts mapping fields before it understands query behavior, update patterns, ownership, and undocumented custom logic.
- **A schema audit without a query audit is incomplete.** The schema tells you what exists; the query logs tell you what matters. Migration effort should be driven by live behavior, not just static config.
- **Unknown customizations are the highest-risk discovery finding.** A forgotten request handler, a custom analyzer jar, or a hardcoded ranking rule in application code is far more dangerous than a large document count.
- **Dynamic fields hide complexity rather than removing it.** "We use dynamic fields" usually means the semantics live in naming conventions, application code, or tribal knowledge. Treat that as design debt, not simplicity.
- **The first useful output of assessment is a risk-ranked inventory, not a migration plan.** If the team jumps straight from discovery into implementation tasks, hidden complexity will surface at the worst possible time.
- **No query logs means no defensible relevance story.** Without search analytics, the team cannot choose a representative gold set, cannot prioritize query patterns, and cannot explain whether the migration improved user outcomes.
- **Readiness is organizational as much as technical.** A technically feasible migration still fails when nobody owns content access, synonym governance, cutover approval, or acceptance criteria.
- **One unexplained "weird thing" in Solr usually implies three more.** When the first hour of discovery finds a mystery plugin or undocumented boost logic, assume there are more hidden behaviors and widen the audit accordingly.

---

## Assessment Objectives

The pre-migration assessment should answer five questions:

1. What does the current Solr estate contain?
2. Which parts of it matter most in real usage?
3. Which behaviors are likely to break or change during migration?
4. Is the client team ready to support the migration operationally and organizationally?
5. What is the likely complexity class of this migration?

If the assessment does not answer those five questions, it is still just data collection.

---

## Evidence To Collect

### Source-Side Technical Inputs

Collect as many of these as the client can provide:

- `schema.xml` or Schema API output for each collection
- `solrconfig.xml`
- request handler definitions
- update processor chain definitions
- custom jars / plugins / class names
- collection list, shard count, replica count, node topology
- sample documents
- document counts by collection
- query logs or representative query samples
- facet, sort, highlight, grouping, suggest, and MLT usage patterns
- indexing/update patterns including partial or atomic updates
- current monitoring outputs and notable incidents

### Organizational Inputs

- who owns content access
- who owns ranking/synonyms/business rules
- who can approve cutover
- who accepts search quality
- who will operate the target system after migration

If these owners are missing, record that as a project risk immediately.

---

## The Five-Part Audit

### 1. Collection and Topology Inventory

For each collection, capture:

- collection name
- purpose / business function
- document count
- average document size if known
- shard count
- replica count
- traffic criticality
- freshness requirements

Also record:

- multi-collection query patterns
- environment sprawl (dev/stage/prod divergence)
- whether the cluster is shared with unrelated workloads

### 2. Schema and Analyzer Audit

Look for:

- field inventory and naming conventions
- dynamic field patterns
- copyField usage
- stored vs indexed behavior
- docValues expectations
- custom analyzers/tokenizers/filters
- synonym and stopword assets
- unusual field types

High-risk findings include:

- unexplained dynamic suffix systems
- analyzer chains that rely on custom jars
- copyField-heavy schemas with unclear intent
- field usage that appears inconsistent across collections

### 3. Query and Application Behavior Audit

You need both query patterns and where they come from.

Capture:

- top query families
- request handlers and parser types in use
- facets, filters, sorts, boosts, grouping, suggesters
- deep pagination patterns
- geo, nested, parent-child, or graph-like behavior
- known "special queries" owned by the business
- applications/services that call Solr directly

The key question is not "what parameters exist?" It is "which behaviors will users notice if they change?"

### 4. Indexing and Data Lifecycle Audit

Capture:

- source systems
- ingestion frequency
- bulk vs streaming
- use of update processors
- atomic update patterns
- delete behavior
- replay/backfill feasibility
- retention/lifecycle expectations

This is where you discover whether migration requires simple backfill, dual-write, CDC, or more bespoke data movement.

### 5. Operational and Governance Audit

Capture:

- latency and throughput baseline
- current pain points
- current monitoring and alerting maturity
- on-call expectations
- disaster recovery posture
- security/compliance constraints
- content and metadata ownership
- acceptance process for relevance changes

This determines whether the client can absorb the migration or only survive the build phase.

---

## Assessment Checklist

Use this as a copy-paste working checklist.

### Workload Inventory

- [ ] Search QPS by collection
- [ ] Peak traffic windows
- [ ] Indexing throughput and freshness expectations
- [ ] Top query families identified
- [ ] Long-tail or zero-result patterns noted

### Schema Audit

- [ ] Field inventory exported
- [ ] Dynamic field patterns documented
- [ ] Analyzer chains reviewed
- [ ] copyField / derived field logic documented
- [ ] Custom field types or plugins flagged

### Query Audit

- [ ] Request handlers identified
- [ ] Parser types identified (`edismax`, `lucene`, custom)
- [ ] Facets / filters / sorts inventoried
- [ ] Highlighting / grouping / suggest / MLT usage recorded
- [ ] Deep pagination and export patterns recorded

### Application Audit

- [ ] Calling services/applications identified
- [ ] Solr client libraries identified
- [ ] Hardcoded query patterns or boosts noted
- [ ] Application-side ranking logic or fallbacks noted

### Data Movement Audit

- [ ] Source-of-truth systems identified
- [ ] Document IDs and update semantics understood
- [ ] Delete semantics understood
- [ ] Backfill path plausible
- [ ] Dual-write feasibility assessed

### Governance Audit

- [ ] Content owner named
- [ ] Metadata/synonym owner named
- [ ] Relevance owner named
- [ ] Cutover approver named
- [ ] Post-migration operator named

### Measurement Audit

- [ ] Query logs available
- [ ] Analytics access available
- [ ] Candidate gold query set can be built
- [ ] Baseline latency/error metrics available

---

## Discovery Interview Prompts

Ask these early. They expose hidden complexity faster than static documents alone.

- "Walk me through your most important collections and what each one does."
- "Which search behaviors are business-critical if they change?"
- "Where do boosts, synonyms, and ranking rules live today?"
- "What parts of Solr would scare you most if they changed tomorrow?"
- "Who owns search quality, and how do they know when it got better or worse?"
- "How do documents get created, updated, and deleted?"
- "What custom plugins or jars are in the deployment, and who understands them?"
- "If cutover went badly, who would decide to roll back?"

The answers to these are usually more informative than the first config dump.

---

## Complexity Scoring Heuristics

Score each dimension from 1 to 5.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Schema complexity** | Mostly standard fields and analyzers | Some dynamic fields and copyField logic | Custom analyzers, plugins, or hard-to-explain field conventions |
| **Query complexity** | Basic keyword + facets | Mixed query types with boosts/sorts | Heavy custom parsing, grouping, geo, or unexplained query behavior |
| **Data movement complexity** | Simple backfill acceptable | Some freshness constraints | CDC, atomic updates, deletes, and strict consistency needs |
| **Application complexity** | One calling app, clean abstraction | Multiple services with mixed ownership | Many apps, hardcoded Solr behavior, unclear query-generation paths |
| **Operational complexity** | Small, well-understood deployment | Moderate scale with some gaps | Large or brittle cluster, weak observability, high sensitivity to regressions |
| **Organizational readiness** | Named owners and clear approvals | Some gaps but recoverable | No clear ownership for content, relevance, or cutover |

### Interpreting the Score

- Mostly `1-2`: straightforward migration candidate
- Mostly `3`: standard but non-trivial migration; plan for iteration
- Any `5`: treat as a risk-led migration and widen discovery before committing timelines

Do not average away a `5`. One severe unknown can dominate the delivery risk.

---

## Red Flags That Should Slow Planning

- no query logs
- no one can explain ranking behavior
- undocumented custom jars
- schema differs materially across environments
- "we think the app just sends a few simple queries"
- no named content owner
- no acceptance owner for relevance
- migration motivation is purely political and quality tolerance is undefined

Any two of these together should shift the engagement into discovery-heavy mode.

---

## Expected Outputs Of This Phase

The pre-migration phase should produce:

- source audit summary
- risk register
- complexity scorecard
- initial query-set candidate list
- list of non-survivor or redesign-risk features
- recommended migration posture (`simple reindex`, `dual-write`, `shadow-first`, `do not plan yet`)

This is the handoff into target design. If you skip these outputs, Phase 2 will inherit unresolved ambiguity.

---

## Decision Heuristics

- **If there are no query logs, instrument first and delay serious relevance planning.** Otherwise the team will optimize for guesswork.
- **If custom plugins appear in the first pass, widen the scope immediately.** Assume application-layer changes and non-trivial feature redesign until proven otherwise.
- **If the client cannot name who owns synonyms or ranking rules, treat relevance readiness as red.** The migration may still proceed, but not with claims of smooth quality validation.
- **If document IDs and delete semantics are unclear, stop talking about cutover dates.** Data movement risk now dominates.
- **If a collection is low-value and high-complexity, de-scope it from the first migration wave.** Not every collection deserves to be in the pilot or phase-one cutover.

---

## Common Mistakes

- Treating schema export as a substitute for workload understanding
- Assuming dynamic fields mean the schema is simple
- Ignoring application code that constructs Solr queries
- Letting "we don't know who owns that" remain an informal note instead of a tracked risk
- Planning timelines before hidden customizations are triaged
- Collapsing all collections into one migration complexity estimate

---

## Open Questions / Evolving Guidance

- What is the right minimum audit artifact set when the client can only provide partial Solr access?
- How should this assessment adapt for hybrid/vector search ambitions discovered mid-project?
- What lightweight automation should accompany this reference for schema/query inventory extraction in future iterations?
