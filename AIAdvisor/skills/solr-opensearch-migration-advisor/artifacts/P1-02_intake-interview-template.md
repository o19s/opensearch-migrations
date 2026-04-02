# P1-02: Intake Interview Template — Solr 7 to OpenSearch Migration

**Project:** Enterprise Solr 7 to OpenSearch Migration
**Generated:** 2026-04-02
**Purpose:** Run your first 1-2 stakeholder sessions with this guide. Produces a foundation document with enough detail to begin migration design.
**Time estimate:** 60-90 minutes per session

**Team:**
- Project lead / search consultant (Sean)
- Solr expert
- OpenSearch expert
- Testing specialist
- Sys/network admin

---

## How To Use This Template

**Before the session:**
1. Send attendees the pre-read questions (Block 0) 2-3 days ahead
2. Decide who to interview: Session 1 = search lead + product owner. Do NOT invite the full team yet.
3. Print or share this template — fill in answers live during the session

**During the session:**
- Work through blocks in order. Each block has a Goal, Questions, Watch-For signals, and an Output template.
- Questions are numbered globally (Q1-Q59) for cross-referencing in session notes and follow-up emails.
- Not every question will be answered. Track unanswered items as homework with an owner and priority.

**After the session:**
- Fill the Session Close section (open questions, artifacts needed, risks, next steps)
- Snapshot with git tag: `v0.0-intake-session-01`
- Send each team member ONLY their assigned homework — not the full document

**Confidence labels** — ask respondents to mark each answer:
- `Known` — confident, can point to evidence
- `Estimated` — best guess, may need verification
- `Unknown` — genuinely don't know

---

## Block 0: Pre-Read Questions (Send Ahead)

> Send these 2-3 days before the session so attendees arrive prepared.

1. Why is migration being considered now? What's the primary business driver?
2. What does success look like — for users, for operations, for leadership?
3. Which regressions are acceptable? Which are not acceptable under any circumstance?
4. Is there a target date or deadline driving this migration?

These four questions set the tone. If the answers are vague or contradictory, the session will need to spend more time on Block 1.

---

## Block 1: Business Intent & Success Criteria

**Goal:** Understand why the migration is happening, who defines success, and what constraints exist.
**Suggested owner:** You (project lead) with executive sponsor / product owner.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q1 | What is the primary business driver? (cost, scale, EOL, modernization, risk reduction) | | |
| Q2 | Is this like-for-like (same behavior, new engine) or a reset (opportunity to redesign search)? | | |
| Q3 | Who is the "Definition of Success" owner — who signs off on the migration being complete? | | |
| Q4 | What business regressions are tolerated? (e.g., ranking changes OK? brief stale data OK?) | | |
| Q5 | Is this a bridge (1-2 year fix) or a 3-5 year platform investment? | | |
| Q6 | Are there timeline pressures? Hard deadlines? Blackout periods? | | |
| Q7 | Final destination: AWS OpenSearch Service, self-managed OpenSearch, or undecided? | | |

### Watch For

- **"We have to migrate because [political reason]"** — acknowledge it, set low relevance expectations, focus on infra and knowledge transfer.
- **No measurable success criteria** — do not start implementation planning until this is resolved.
- **Deadline already passed or unrealistically close** — reframe as phased program with sponsor.

### Output

- [ ] Primary driver documented
- [ ] Success criteria documented (measurable)
- [ ] Regression tolerance documented
- [ ] Timeline constraints and blackout periods listed

---

## Block 2: Content Sources & Document Lifecycle

**Goal:** Map every document type to its source system, understand how data flows into Solr, and confirm whether a clean rebuild is possible without Solr.
**Suggested owner:** Solr expert to investigate; content owners on client side to answer.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q8 | What are the primary source systems for indexed content? (ERP, CMS, ticketing, etc.) | | |
| Q9 | Which content types come from which source system? | | |
| Q10 | How do documents get into Solr today — event-driven, batch, or a mix? | | |
| Q11 | If batch: what is the frequency and typical batch size? | | |
| Q12 | Could we rebuild the entire index from scratch — from source systems, not Solr? How long? | | |
| Q13 | Are there enrichments during indexing — computed fields, denormalized data, external service calls? | | |
| Q14 | For each enrichment: is the service available on-demand, or on a schedule? | | |
| Q15 | Are there multiple paths that can write to the same index? (competing pipelines, manual scripts) | | |

### Watch For

- **"We can't rebuild without Solr"** — Solr is the source of truth for some data. Critical risk.
- **Enrichments that depend on external services** — pipeline dependencies that must survive migration.
- **Manual correction workflows** — undocumented scripts or admin actions that fix data in Solr directly.

### Output

| Content type | Source system | Indexing method | Enrichments | Rebuild possible? | Notes |
|---|---|---|---|---|---|
| | | | | | |

---

## Block 3: Query Behavior & Relevance

**Goal:** Understand the search workload profile, available analytics, and how relevance is currently managed.
**Suggested owner:** You (project lead) + testing specialist for measurement setup.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q16 | Do you have query analytics? Click logs, search-result-click-through data, session tracking? | | |
| Q17 | What tooling provides the analytics? (Fusion, custom instrumentation, Solr logs only) | | |
| Q18 | What % of searches are known-item lookups vs. exploratory? | | |
| Q19 | What is the average query length (tokens)? | | |
| Q20 | Are there specific query patterns that are business-critical? (part-number lookup, error-code search) | | |
| Q21 | Who currently "owns" relevance? Is there a person or team responsible for search quality? | | |
| Q22 | Do you have a documented relevance strategy, or is it tribal knowledge? | | |
| Q23 | Are there boost rules, business rules, or manual overrides applied to search results? | | |

### Watch For

- **No analytics** — flag as P0 blocker. You cannot measure migration success without a baseline.
- **"One person knows how the ranking works"** — bus factor risk. Capture that knowledge immediately.
- **No documented relevance strategy** — migration is the opportunity to create one.

### Output

- [ ] Analytics inventory (tools, data available, gaps)
- [ ] Search profile summary (lookup vs. exploratory ratio, query characteristics)
- [ ] Relevance ownership and governance model
- [ ] Boost/business rules inventory started

---

## Block 4: Access Control & Entitlements

**Goal:** Understand how search results are filtered by user identity, and how those rules are enforced.
**Suggested owner:** Sys/network admin to investigate; security team on client side to answer.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q24 | How are search results scoped to the current user? (query-time filters, index-per-audience, app-layer) | | |
| Q25 | What dimensions are used for access control? (role, region, business unit, customer tier) | | |
| Q26 | Where does the caller's entitlement context come from at query time? (SSO, LDAP, session, API header) | | |
| Q27 | How many distinct access profiles exist in practice? (handful of roles, or per-user granularity) | | |
| Q28 | Has there ever been a data leak incident — a user seeing content they shouldn't? | | |
| Q29 | Are there compliance or regulatory requirements around search access? (GDPR, SOC2, industry-specific) | | |

### Watch For

- **"The application handles it"** — dig deeper. Is the app building filter queries, or post-filtering results?
- **Large number of access combinations** — may need a different index strategy.
- **No leak history AND no audit capability** — absence of evidence is not evidence of absence.

### Output

- [ ] Filter dimensions and enforcement mechanism documented
- [ ] Access profile count and complexity assessed
- [ ] Compliance requirements listed
- [ ] Data leak history and audit capability noted

---

## Block 5: Synonyms, Linguistics & Metadata Assets

**Goal:** Inventory the "invisible" assets that live outside the schema and are easy to lose during migration.
**Suggested owner:** Solr expert to extract files; metadata owners on client side to explain intent.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q30 | Do you maintain a synonym dictionary? How large? Who owns it? | | |
| Q31 | Are synonyms applied at index time, query time, or both? What goes where? | | |
| Q32 | Are there product aliases or part-number cross-references that users rely on? | | |
| Q33 | Who maintains these mappings? Is it automated or manual? | | |
| Q34 | Do you have custom stop word lists, or standard English defaults? | | |
| Q35 | Are there other linguistic assets? (lemmatization, spelling dictionaries, taxonomies, entity databases) | | |
| Q36 | Have you had incidents caused by synonym or stopword configuration? What happened? | | |

### Watch For

- **Manual synonym maintenance by a single person** — critical bus-factor risk. Capture immediately.
- **"Extensive" or "possibly over-engineered" synonym list** — audit opportunity during migration.
- **Index-time synonyms for cross-reference lookups** — need special handling in OpenSearch.

### Output

- [ ] Synonym strategy documented (index-time vs. query-time split)
- [ ] Metadata asset inventory with owners
- [ ] Automation status and bus-factor assessment
- [ ] Known incidents from linguistic configuration

---

## Block 6: Schema Features & Redesign Zones

**Goal:** Identify Solr features in use that don't translate directly and will need redesign.
**Suggested owner:** Solr expert leads; OS expert assesses equivalence.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q37 | Do you use field collapsing or result grouping? Which search flows? What field? | | |
| Q38 | Do you use Solr's streaming expressions or parallel SQL? | | |
| Q39 | Are there custom Solr plugins? (UpdateProcessors, QParser, custom JAR files) | | |
| Q40 | Do you use Solr's atomic/partial updates? How heavily? | | |
| Q41 | Are there nested or child documents in your index? | | |
| Q42 | Do you use function queries? (`bf`, `bq`, custom `FunctionQuery`) | | |
| Q43 | Any features where the behavior is "quirky" but users depend on it? | | |

### Watch For

- **Custom plugins** — hardest migration items. Flag immediately as redesign zones.
- **Field collapsing** — OpenSearch `collapse` exists but behaves differently.
- **Streaming expressions** — no OpenSearch equivalent. Requires full redesign.
- **"Not sure what it does but it's been there for years"** — investigate before migrating.

### Output

| Feature | In use? | OpenSearch equivalent | Effort | Redesign needed? |
|---|---|---|---|---|
| Field collapsing / grouping | | `collapse` + `top_hits` | | |
| Streaming expressions | | None | | |
| Custom plugins | | Varies | | |
| Atomic updates | | Partial update via `doc` | | |
| Nested/child docs | | `nested` type or `join` | | |
| Function queries | | `function_score` | | |

---

## Block 7: Team Readiness & Staffing

**Goal:** Assess whether the client team can support the migration, and identify dependency bottlenecks.
**Suggested owner:** You (project lead).

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q44 | Who is on the migration team? (roster with roles) | | |
| Q45 | What percentage of their time is allocated to the migration? | | |
| Q46 | Who on the team has OpenSearch or Elasticsearch experience? | | |
| Q47 | Is there a content owner who can authoritatively say what should/shouldn't be in the index? | | |
| Q48 | Who makes the go/no-go decision for cutover? | | |
| Q49 | Are there any team changes planned during the migration window? (departures, reorgs, hiring) | | |

### Watch For

- **Team at <30% allocation** — dependency bottlenecks will dominate. Get sponsor commitment for response windows.
- **No content owner** — this role is critical path and often missing.
- **Single-person dependencies** — any process or knowledge that lives in one person's head is a risk.

### Output

| Name | Role | Allocation | OS/ES experience? | Notes |
|---|---|---|---|---|
| | | | | |

---

## Block 8: Performance & Workload

**Goal:** Establish current performance baseline and understand workload shape for OpenSearch sizing.
**Suggested owner:** Sys/network admin + Solr expert.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q50 | What are your current latency targets or SLAs? Formal or informal? | | |
| Q51 | What is your daily query volume? Evenly distributed or peak hours? | | |
| Q52 | Are there seasonal spikes? When is your busiest period? | | |
| Q53 | What is the typical batch size for incremental updates? | | |
| Q54 | Are there known "expensive" queries that cause performance issues? | | |
| Q55 | What is your current Solr cluster sizing? (nodes, memory, disk, JVM heap) | | |

### Watch For

- **No formal SLA** — help the client define one. Migration is the opportunity.
- **Peak season overlap with migration timeline** — do NOT cut over during peak.
- **Solr cluster is oversized** — current "fast" performance may not survive right-sizing.

### Output

- [ ] Current and target latency requirements
- [ ] Traffic profile (volume, peaks, seasonality)
- [ ] Current cluster topology for sizing comparison

---

## Block 9: Cutover & Rollback

**Goal:** Understand timeline pressure, risk tolerance, and rollback capability.
**Suggested owner:** Sys/network admin leads; all review.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q56 | Is there a target date or deadline driving this migration? | | |
| Q57 | What's your appetite for a dual-write period? (running both engines simultaneously) | | |
| Q58 | If cutover goes wrong, how quickly do you need to be back on the old system? | | |
| Q59 | Are there blackout periods where you cannot risk a search disruption? | | |
| Q60 | Do you have traffic routing infrastructure for gradual cutover? (LB rules, feature flags, DNS) | | |
| Q61 | Who controls the traffic routing? How fast can it be switched? | | |

### Watch For

- **"Zero downtime" without defining what that means** — clarify: is stale data acceptable? How stale?
- **Assumed failback capability that hasn't been tested** — verify the mechanism.
- **No dual-write budget** — forces a "Big Bang" cutover, which is high-risk.

### Output

- [ ] Timeline constraints and deadline pressure
- [ ] Dual-write appetite and budget
- [ ] Failback requirement (speed, mechanism, verified?)
- [ ] Blackout periods
- [ ] Cutover strategy recommendation

---

## Block 10: Monitoring & Observability

**Goal:** Understand current monitoring capabilities and gaps for the target platform.
**Suggested owner:** Sys/network admin.

### Questions

| # | Question | Answer | Confidence |
|---|----------|--------|------------|
| Q62 | What monitoring do you have on Solr today? (Grafana, CloudWatch, vendor-specific) | | |
| Q63 | Do you track zero-result rate or search abandonment rate? | | |
| Q64 | Are there canary queries or automated health checks for search? | | |
| Q65 | What alerting is in place? Who gets paged when search is slow or broken? | | |
| Q66 | What monitoring stack will be available for OpenSearch? (same as Solr, or new?) | | |

### Watch For

- **No zero-result or abandonment tracking** — add to build plan. Critical migration health signals.
- **"We'll set up monitoring later"** — push back. Must be in place before dual-write begins.
- **Unhappiness with current monitoring** — migration is a natural point to upgrade.

### Output

- [ ] Current monitoring inventory
- [ ] Target monitoring stack
- [ ] Gaps to address during migration build phase

---

## Session Close

Complete this section at the end of every session. This is the handoff artifact.

### Coverage Check

| Block | Status |
|---|---|
| 1. Business Intent & Success | Covered / Partial / Not started |
| 2. Content Sources & Lifecycle | Covered / Partial / Not started |
| 3. Query Behavior & Relevance | Covered / Partial / Not started |
| 4. Access Control & Entitlements | Covered / Partial / Not started |
| 5. Synonyms & Linguistics | Covered / Partial / Not started |
| 6. Schema Features & Redesign Zones | Covered / Partial / Not started |
| 7. Team Readiness & Staffing | Covered / Partial / Not started |
| 8. Performance & Workload | Covered / Partial / Not started |
| 9. Cutover & Rollback | Covered / Partial / Not started |
| 10. Monitoring & Observability | Covered / Partial / Not started |

### Open Questions

| # | Question | Assigned to | Priority | Due |
|---|----------|-------------|----------|-----|
| | | | | |

> Keep original question numbers. Do not renumber across sessions.

### Data Artifacts Needed

| Artifact | From | Priority | Status |
|----------|------|----------|--------|
| schema.xml or Schema API JSON | Solr expert | P0 | |
| solrconfig.xml (request handlers) | Solr expert | P0 | |
| Top 100-200 queries by volume | Analytics / logs | P0 | |
| Synonym files (full export) | Solr expert | P1 | |
| Collection list with doc counts | Solr expert | P1 | |
| Cluster topology (nodes, shards, replicas) | Sys admin | P1 | |
| Zero-result query report | Analytics | P1 | |
| Part-number / alias mapping tables | Metadata owner | P1 | |
| Slow query log (>500ms) | Solr expert | P2 | |
| Facet usage data | Analytics | P2 | |

### Key Risks Identified

| Risk | Severity | Mitigation | Owner |
|------|----------|-----------|-------|
| | | | |

### Next Session Agenda

- Topics to cover:
- Artifacts expected by then:
- People needed:

---

## Intake Completion Criteria

The intake is **structurally complete** when:

- [ ] All content types mapped to source systems
- [ ] Indexing pipeline documented (batch/event/mix, enrichments, rebuild capability)
- [ ] Query analytics availability confirmed (or flagged as a blocker)
- [ ] Access control mechanism and dimensions documented
- [ ] Synonym/linguistic asset inventory complete
- [ ] Redesign zones identified (features that won't port directly)
- [ ] Team roster with allocations confirmed
- [ ] Performance baseline and targets documented
- [ ] Cutover constraints, failback requirements, and blackout periods known
- [ ] Monitoring stack inventoried

Items may have placeholders if details are pending, but every block must have at least a directional answer or a tracked action item with an owner.

---

## After Intake: Recommended Milestones

| Milestone | Git tag | Meaning |
|-----------|---------|---------|
| Session captured | `v0.0-intake-session-NN` | Notes captured, homework assigned |
| Intake complete | `v0.1-foundation-lock` | All blocks answered or tracked, ready for design |
| Design complete | `v0.2-design-lock` | Mapping, query translations, task plan reviewed |
| Hello Search | `v0.3-hello-search` | Working demo with sample corpus |
| Dual-write active | `v0.4-dual-write` | Both engines receiving production data |
| Cutover | `v1.0-cutover` | Production traffic fully on OpenSearch |
