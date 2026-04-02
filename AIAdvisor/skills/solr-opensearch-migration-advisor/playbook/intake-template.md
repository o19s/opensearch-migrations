# Client Intake Template: Solr → OpenSearch Migration
**Scope:** Structured question guide for the first 1-2 client sessions. Produces a foundation
document with enough detail to begin migration design.
**Audience:** OSC consultants running intake sessions
**Source:** Derived from consulting-methodology.md, consulting-concerns-inventory.md, and
field experience from Northstar demo engagement
**Last reviewed:** 2026-03-19  |  **Reviewer:** AI draft — needs expert review

---

## How to Use This Template

Run through the blocks in order during client intake. Each block has:
- **Goal** — what you're trying to learn
- **Questions** — numbered for cross-referencing in session notes
- **Watch for** — signals that indicate deeper investigation is needed
- **Output** — what the intake document should capture for this block

Not every question will be answered in session one. Track unanswered questions as action items
with an owner and priority. The intake is complete when all High-priority items have answers.

---

## Block 1: Content Sources & Document Lifecycle

**Goal:** Map every document type to its source system, understand how data flows into Solr,
and confirm whether a clean rebuild is possible without Solr.

### Questions

1. What are the primary source systems for your indexed content? (ERP, CMS, ticketing, etc.)
2. Which content types come from which source system?
3. How do documents get into Solr today — event-driven, batch, or a mix?
4. If batch: what is the frequency and typical batch size?
5. If we needed to rebuild the entire index from scratch — from source systems, not Solr — could we? How long would that take?
6. Are there any enrichments during indexing — fields that get computed, denormalized, or pulled from external services?
7. For each enrichment: is the service available on-demand, or does it run on a schedule?
8. Are there multiple paths that can write to the same index? (competing pipelines, manual scripts, admin tools)

### Watch for

- **"We can't rebuild without Solr"** — this means Solr is the source of truth for some data. Critical risk.
- **Enrichments that depend on external services** — these are pipeline dependencies that must survive migration.
- **Manual correction workflows** — undocumented scripts or admin actions that fix data in Solr directly.

### Output

| Content type | Source system | Indexing method | Enrichments | Notes |
|--------------|-------------|-----------------|-------------|-------|
| (fill per type) | | | | |

---

## Block 2: Query Behavior & Relevance

**Goal:** Understand the search workload profile, available analytics, and how relevance
is currently managed.

### Questions

9. Do you have query analytics? Click logs, search-result-click-through data, session tracking?
10. What tooling provides the analytics? (Fusion, custom instrumentation, Solr logs only)
11. What percentage of searches are known-item lookups (user knows exactly what they want) vs. exploratory (investigating a problem)?
12. What is the average query length (tokens)?
13. Are there specific query patterns that are business-critical? (part-number lookup, error-code search, etc.)
14. Who currently "owns" relevance? Is there a person or team responsible for search quality?
15. Do you have a documented relevance strategy, or is it tribal knowledge?
16. Are there boost rules, business rules, or manual overrides applied to search results?

### Watch for

- **No analytics** — flag as P0 blocker. You cannot measure migration success without a baseline.
- **"One person knows how the ranking works"** — bus factor risk. Capture that knowledge immediately.
- **Shift in search behavior over time** — indicates users adapted to the system. Migration must not break learned behaviors.

### Output

- Analytics inventory (tools, data available, gaps)
- Search profile summary (lookup vs. exploratory ratio, query characteristics)
- Relevance ownership and governance model

---

## Block 3: Access Control & Entitlements

**Goal:** Understand how search results are filtered by user identity, and how
those rules are enforced.

### Questions

17. How are search results scoped to the current user? (query-time filters, index-per-audience, application-layer filtering)
18. What dimensions are used for access control? (role, region, business unit, customer tier, etc.)
19. Where does the caller's entitlement context come from at query time? (SSO, LDAP, session, API header)
20. How many distinct access profiles exist in practice? (handful of roles, or per-user granularity)
21. Has there ever been a data leak incident — a user seeing content they shouldn't?
22. Are there compliance or regulatory requirements around search access? (GDPR, SOC2, industry-specific)

### Watch for

- **"The application handles it"** — dig deeper. Is the app building filter queries, or is it post-filtering results? Post-filtering is a security risk.
- **Large number of access combinations** — may need a different index strategy than simple query-time filters.
- **No leak history but no audit capability either** — absence of evidence is not evidence of absence.

### Output

- Filter dimensions and enforcement mechanism
- Access profile count and complexity
- Compliance requirements
- Data leak history and audit capability

---

## Block 4: Synonyms, Linguistics & Metadata Assets

**Goal:** Inventory the "invisible" assets that live outside the schema and are easy
to lose during migration.

### Questions

23. Do you maintain a synonym dictionary? How large? Who owns it?
24. Are synonyms applied at index time, query time, or both? What goes where?
25. Are there product aliases or part-number cross-references that users rely on? (old part → new part)
26. Who maintains these mappings? Is it automated or manual?
27. Do you have custom stop word lists, or standard English defaults?
28. Are there other linguistic assets? (lemmatization files, spelling dictionaries, taxonomies, entity databases)
29. Have you had incidents caused by synonym or stopword configuration? What happened?

### Watch for

- **Manual synonym maintenance by a single person** — critical bus-factor risk. See "Knowledge holder departure" pattern in consulting-methodology.md.
- **"Extensive" or "possibly over-engineered" synonym list** — audit opportunity during migration.
- **Index-time synonyms for cross-reference lookups** — these need special handling in OpenSearch (separate analyzer chains).

### Output

- Synonym strategy (index-time vs. query-time split)
- Metadata asset inventory with owners
- Automation status and bus-factor assessment
- Known incidents from linguistic configuration

---

## Block 5: Schema Features & Redesign Zones

**Goal:** Identify Solr features in use that don't translate directly to OpenSearch
and will need redesign rather than porting.

### Questions

30. Do you use field collapsing or result grouping? Which search flows? What field?
31. Do you use Solr's streaming expressions or parallel SQL?
32. Are there any custom Solr plugins (custom UpdateProcessors, custom QParser, etc.)?
33. Do you use Solr's atomic/partial updates? How heavily?
34. Are there nested or child documents in your index?
35. Do you use Solr's function queries (`bf`, `bq`, custom `FunctionQuery`)?
36. Are there any features where you're aware the behavior is "quirky" but users depend on it?

### Watch for

- **Custom plugins** — these are the hardest migration items. Flag immediately.
- **Field collapsing** — OpenSearch `collapse` exists but behaves differently. Mark as redesign zone.
- **Streaming expressions** — no OpenSearch equivalent. Requires full redesign.
- **"We're not sure what it does but it's been there for years"** — investigate before migrating.

### Output

- Feature inventory with OpenSearch equivalence assessment
- Redesign zones (features that need rethinking, not just translating)
- Unknown/undocumented features to investigate

---

## Block 6: Team Readiness & Staffing

**Goal:** Assess whether the client team can support the migration at the required
pace, and identify dependency bottlenecks.

### Questions

37. Who is on the migration team? (roster with roles)
38. What percentage of their time is allocated to the migration?
39. Who on the team has OpenSearch or Elasticsearch experience?
40. Is there a content owner who can authoritatively say what should and shouldn't be in the index?
41. Who makes the go/no-go decision for cutover?
42. Are there any team changes planned during the migration window? (departures, reorgs, hiring)

### Watch for

- **Team at <30% allocation** — OSC carries the work, but client dependencies will bottleneck. Get sponsor commitment for response windows.
- **No content owner** — this role is critical path and often missing from the roster.
- **Single-person dependencies** — any process or knowledge that lives in one person's head is a risk.

### Output

- Team roster with roles, allocation, and OpenSearch experience
- Dependency map: what OSC needs from whom, and when
- Staffing risks and mitigation plan

---

## Block 7: Performance & Workload

**Goal:** Establish current performance baseline and understand workload shape
for OpenSearch sizing.

### Questions

43. What are your current latency targets or SLAs? Formal or informal?
44. What is your daily query volume? Is it evenly distributed or are there peak hours?
45. Are there seasonal spikes? When is your busiest period?
46. What is the typical batch size for incremental updates?
47. Are there any known "expensive" queries or query patterns that cause performance issues?
48. What is your current Solr cluster sizing? (nodes, memory, disk)

### Watch for

- **No formal SLA** — help the client define one. This is a migration opportunity.
- **Peak season overlap with migration timeline** — do not cut over during peak.
- **Solr cluster is oversized** — current "fast" performance may not survive right-sizing to OpenSearch.

### Output

- Current and target latency requirements
- Traffic profile (volume, peaks, seasonality)
- Workload characteristics for sizing

---

## Block 8: Cutover & Rollback

**Goal:** Understand timeline pressure, risk tolerance, and rollback capability.

### Questions

49. Is there a target date or deadline driving this migration?
50. What's your appetite for a dual-write period? (running both engines simultaneously)
51. If we cut over and something goes wrong, how quickly do you need to be back on the old system?
52. Are there blackout periods where you cannot risk a search disruption?
53. Do you have existing traffic routing infrastructure that could support gradual cutover? (load balancer rules, feature flags, DNS-based routing)
54. Who controls the traffic routing? How fast can it be switched?

### Watch for

- **Deadline already passed or unrealistically close** — reframe as phased program with sponsor.
- **"Zero downtime" without defining what that means** — clarify: is stale data acceptable? How stale?
- **Assumed failback capability that hasn't been tested** — verify the mechanism, don't trust assumptions.

### Output

- Timeline constraints and deadline pressure
- Dual-write appetite and budget
- Failback requirement (speed, mechanism)
- Blackout periods
- Cutover strategy recommendation

---

## Block 9: Monitoring & Observability

**Goal:** Understand current monitoring capabilities and gaps for the target platform.

### Questions

55. What monitoring do you have on Solr today? (Grafana, CloudWatch, vendor-specific, etc.)
56. Do you track zero-result rate or search abandonment rate?
57. Are there canary queries or automated health checks for search?
58. What alerting is in place? Who gets paged when search is slow or broken?
59. What monitoring stack will be available for OpenSearch? (same as Solr, or new?)

### Watch for

- **No zero-result or abandonment tracking** — add to build plan. These are critical migration health signals.
- **"We'll set up monitoring later"** — push back. Monitoring must be in place before dual-write begins.
- **Unhappiness with current monitoring** — migration is a natural point to upgrade.

### Output

- Current monitoring inventory
- Target monitoring stack
- Gaps to address during migration build phase

---

## Session Close: Homework & Next Steps

At the end of each session, produce:

1. **Coverage check** — table of topics covered vs. open
2. **Open questions** — numbered, with assigned owner and priority
3. **Data artifacts needed** — specific files, exports, or reports the client team should gather
4. **Key risks identified** — with severity and proposed mitigation
5. **Next session agenda** — what to cover next time

Write these into the intake session document (see `examples/[client]/intake/` for format)
and snapshot with a git tag.

---

## Intake Completion Criteria

The intake is **structurally complete** when:

- [ ] All content types are mapped to source systems
- [ ] Indexing pipeline is documented (batch/event/mix, enrichments, rebuild capability)
- [ ] Query analytics availability is confirmed (or flagged as a blocker)
- [ ] Access control mechanism and dimensions are documented
- [ ] Synonym/linguistic asset inventory is complete
- [ ] Redesign zones are identified (features that won't port directly)
- [ ] Team roster with allocations is confirmed
- [ ] Performance baseline and targets are documented
- [ ] Cutover constraints, failback requirements, and blackout periods are known
- [ ] Monitoring stack is inventoried

Items may have "MORE HERE" placeholders if details are pending, but every block
must have at least a directional answer or a tracked action item with an owner.

---

## After Intake: Recommended Snapshots

| Milestone | Git tag pattern | What it means |
|-----------|----------------|---------------|
| Session complete | `v0.0-intake-session-NN` | Session notes captured, homework assigned |
| Intake complete | `v0.1-foundation-lock` | All blocks answered or tracked, ready for design |
| Design complete | `v0.2-design-lock` | Mapping, query translations, and task plan reviewed |
| Hello Search | `v0.3-hello-search` | Working demo with sample corpus |

See "Session Management" section in `consulting-methodology.md` for multi-session guidance.
