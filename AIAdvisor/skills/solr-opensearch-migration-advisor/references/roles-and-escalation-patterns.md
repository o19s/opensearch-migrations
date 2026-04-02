# Roles and Escalation Patterns
**Scope:** Compact guidance for staffing Solr to OpenSearch migrations: core roles, tier-based merges, escalation triggers, and specialist add-on roles for outlier migrations.
**Audience:** O19s consultants and agents advising on staffing, governance, and delivery risk
**Last reviewed:** 2026-03-19  |  **Reviewer:** AI draft

---

## Key Judgements

- **A migration does not fail because of missing titles. It fails because ownership is missing.** The job is to make sure every critical responsibility has a named owner, even if one person wears several hats.
- **The role model should stay small by default.** Keep the canonical set compact, then add specialist roles only when a trigger condition is present.
- **Content, relevance, and production operations are the three most dangerous ownership gaps.** Teams usually notice missing developers. They notice missing content and ops only after the schedule slips.
- **Security and compliance should be explicit in enterprise migrations.** Treating them as part-time architecture concerns is how teams discover blockers late.
- **Tiering is useful because it normalizes multi-hatting.** A Tier 2 team is not "wrong" for merging roles; it is wrong only if the merges are undocumented.
- **Outlier roles should be activated by evidence, not imagination.** Add specialist roles because the migration shape demands them, not because the framework has room for them.
- **A troubled migration needs truth-detection roles more than more meetings.** In rescue situations, query logs, evidence, and acceptance criteria matter more than org charts.

---

## Canonical Core Roles

Use this as the default role set. On small teams, one person may own multiple roles.

| Role | Primary ownership | Risk if missing |
|---|---|---|
| **Stakeholder / Sponsor** | Defines business success, budget, cutover tolerance | Goalposts shift; funding or sign-off weakens late |
| **Product Owner** | Prioritizes user needs, scope, and experience tradeoffs | Search quality decisions become opinion-driven |
| **Project Manager** | Timeline, dependencies, blockers, delivery rhythm | Workstreams drift and hidden blockers accumulate |
| **Architect** | Target posture, integration boundaries, platform choices | Team misses cross-system complexity and non-functional scope |
| **Software Engineer** | Search API, app integration, migration implementation | Build work stalls even if strategy is sound |
| **Content Owner** | Source content access, extraction, lifecycle clarity | Migration blocks on access and "what are we indexing?" confusion |
| **Metadata Owner** | Synonyms, taxonomies, business rules, dictionaries | Relevance work hits a ceiling fast |
| **Data / Integration Owner** | ETL, CDC, backfill, enrichment, replay reliability | Missing docs, duplicates, stale-overwrites-fresh bugs |
| **Search Relevance Strategist** | Ranking philosophy, measurement posture, evaluation design | Migration becomes lift-and-shift with no defensible quality outcome |
| **Search Relevance Engineer** | Query tuning, analyzers, experiments, offline testing | No baseline/tune loop; no way to prove improvement |
| **Platform Ops / SRE** | Monitoring, capacity, HA/DR, runbooks, on-call posture | Cutover succeeds briefly but production operation is brittle |
| **Security / Compliance Owner** | Access control, IAM/SAML, privacy, auditability | Enterprise rollout stalls on approval or leaks risk |
| **QA / Acceptance Lead** | Regression criteria, UAT evidence, release sign-off | Teams argue from anecdotes instead of test evidence |

---

## Minimum Viable Coverage

If the team is very small, do not preserve every title. Preserve these responsibility groups:

| Responsibility group | Must be covered by |
|---|---|
| Business success and scope | Stakeholder + Product Owner |
| Search quality and measurement | Relevance Strategist + Relevance Engineer |
| Content and ingestion reality | Content Owner + Data / Integration Owner |
| Production readiness | Architect + Platform Ops / SRE |
| Delivery evidence | Project Manager + QA / Acceptance Lead |

If any of those groups is unowned, document it as a project risk immediately.

---

## Tier Model

This is the compact version of the 5-tier staffing model.

| Tier | Typical team shape | Healthy merge pattern | Escalation warning |
|---|---|---|---|
| **Tier 1: Sole operator** | 1 person | Almost everything merged | High risk of over-focusing on infra and under-investing in relevance |
| **Tier 2: Lean team** | 2-5 people | PO+PM, Architect+Engineer, Strategist+Engineer | Content ownership and success criteria are usually fuzzy |
| **Tier 3: Standard team** | 5-10 people | Some search-role overlap still normal | Synonym governance and acceptance criteria often lag |
| **Tier 4: Enterprise team** | 10+ people | Roles mostly split | Cross-team alignment, approvals, and observability become the bottleneck |
| **Tier 5: Rescue / challenge** | Any size, but trust is low | Ownership is disputed or nominal | Move to evidence-first operation: query logs, gold queries, explicit cutover gates |

---

## Common Safe Role Merges

These merges are common and usually survivable if the person is strong and the merge is explicit.

| Merge | Usually safe when | Watch for |
|---|---|---|
| **Product Owner + Project Manager** | Small product-led teams | Roadmap pressure overwhelming user-need decisions |
| **Architect + Software Engineer** | Mid-level engineering leadership is hands-on | Architecture becoming whatever was fastest to code |
| **Relevance Strategist + Relevance Engineer** | Strong search specialist present | Strategy collapsing into low-level tweaks |
| **Content Owner + Data / Integration Owner** | Source systems are simple and well understood | Hidden data lifecycle and deletion edge cases |
| **Platform Ops / SRE + Architect** | Early-stage or low-scale deployments | Missing runbooks, alerting, and operational proof |

---

## Unsafe Missing Roles

These gaps should trigger immediate escalation rather than quiet acceptance.

| Gap | Why it is dangerous | Default response |
|---|---|---|
| **No Content Owner** | The schedule will block on access and source ambiguity | Escalate before sprint 1 |
| **No Relevance owner** | Team can migrate infrastructure but cannot prove search quality | Re-scope as technical PoC or add search expertise |
| **No Platform Ops / SRE owner** | Production readiness is assumed rather than demonstrated | Add explicit operational workstream and named owner |
| **No Security / Compliance owner** | Enterprise approvals arrive late and derail cutover | Pull review forward; require early control mapping |
| **No QA / Acceptance owner** | Final sign-off becomes vibes and politics | Define gold queries, UAT criteria, and sign-off owner |
| **No Stakeholder with decision authority** | Nobody can define "good enough" | Stop calling it a delivery plan; it is discovery |

---

## Specialist Add-On Roles

Do not add these by default. Add them when the migration pattern requires them.

| Specialist role | Add when | Common artifacts |
|---|---|---|
| **Identity / Access Specialist** | DLS/FLS, SAML, IAM federation, tenant entitlements | Role maps, access matrices, auth flow diagrams |
| **Legacy Plugin Specialist** | Custom Solr request handlers, token filters, Java plugins, bespoke similarity | Plugin inventory, parity decisions, non-survivor list |
| **ML / Vector Search Owner** | Hybrid search, embeddings, rerankers, semantic search roadmap | Embedding strategy, evaluation plan, latency budget |
| **Geo / Spatial Search Specialist** | Geoshapes, polygons, routing, logistics queries | Geo test corpus, precision/recall examples, perf thresholds |
| **Merchandising / Business Rules Owner** | Ecommerce boosts, bury rules, campaigns, seasonal ranking | Rules register, approval workflow, rollback procedure |
| **Records / Legal Hold Owner** | Retention constraints, legal discovery, regulated deletion | Retention matrix, hold rules, deletion audit path |
| **Multi-region / DR Architect** | Active-active, sovereign region needs, hard RTO/RPO requirements | Failover design, restore tests, regional ownership model |
| **Search Analytics Scientist** | High-volume click data, counterfactual evaluation, advanced judgment design | Query sets, metric definitions, evaluation notebooks |

---

## Trigger Matrix

Use this matrix to keep outlier knowledge compact.

| If you see this signal | Add this role | Why |
|---|---|---|
| `restricted documents`, `row-level access`, `federated auth` | **Identity / Access Specialist** | Access logic is now a first-class migration problem |
| `custom Solr plugin`, `request handler`, `bespoke analyzer`, `Java JAR` | **Legacy Plugin Specialist** | Hidden engine behavior will not survive by accident |
| `vector`, `semantic`, `hybrid`, `reranking` | **ML / Vector Search Owner** | The migration now includes retrieval architecture change |
| `geo filter`, `distance sort`, `polygon`, `map search` | **Geo / Spatial Search Specialist** | Spatial correctness and performance need dedicated scrutiny |
| `campaign boosts`, `bury`, `sponsored ranking`, `conversion rules` | **Merchandising / Business Rules Owner** | Business ranking logic needs governance, not ad hoc boosts |
| `legal hold`, `records`, `regulated retention`, `eDiscovery` | **Records / Legal Hold Owner** | Delete and retention semantics become cutover-critical |
| `multi-region`, `disaster recovery`, `active-active`, `country isolation` | **Multi-region / DR Architect** | Infrastructure posture becomes a design axis, not an ops afterthought |
| `click model`, `counterfactual`, `large judgment set`, `data science` | **Search Analytics Scientist** | Measurement complexity exceeds standard relevance practice |

---

## Escalation Patterns

### 1. Discovery Escalation

Trigger when the team cannot answer basic ownership questions.

- Who defines success?
- Who approves ranking changes?
- Who owns content access?
- Who will carry the pager after cutover?

If two or more answers are missing, treat the project as discovery-first, not delivery-ready.

### 2. Quality Escalation

Trigger when the team wants parity but lacks evidence.

- No gold query set
- No analytics baseline
- No named relevance owner
- No acceptance lead

Response: freeze parity claims and move to baseline-first work.

### 3. Enterprise Control Escalation

Trigger when platform/security requirements are assumed rather than mapped.

- IAM/SSO is "someone else's problem"
- DLS/FLS behavior is undocumented
- Compliance review starts near cutover
- Restore procedure has never been tested

Response: pull security and operations forward into the first design checkpoint.

### 4. Rescue Escalation

Trigger when the migration is politically stuck or technically haunted.

- Stakeholders insist on 100% parity with undocumented behavior
- Query differences are argued from anecdotes
- Solr schema contains unexplained boosts or custom code
- Ownership is nominal but nobody makes decisions

Response:

- Establish a truth set: query logs, gold queries, acceptance criteria
- Identify deliberate non-survivors early
- Publish an explicit risk register with named owners
- Convert subjective complaints into measurable cases

---

## Compact Agent Guidance

When using this file in an agent flow:

1. Identify the tier.
2. Map canonical roles to named people.
3. Flag unowned responsibility groups before discussing implementation.
4. Add specialist roles only when trigger signals are present.
5. Keep the active context small by carrying only:
   - tier
   - named owners
   - missing critical roles
   - triggered specialist roles

That is usually enough to guide staffing and risk decisions without dragging a large role taxonomy into every session.
