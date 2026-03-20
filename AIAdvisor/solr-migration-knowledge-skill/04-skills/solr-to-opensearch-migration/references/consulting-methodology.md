# Search Engine Migration: Consulting Methodology
**Source:** OSC Playbook — Search Engine Migration (internal consulting document)
**Distilled for:** Agent skill reference — process, people, and risk guidance

---

## Core Philosophy

Two things are non-negotiable for a successful migration:

1. **Experiment-driven development** — every relevance change is a hypothesis with a measurement. Not optional. Migrations that skip this produce unmeasurable outcomes and lose stakeholder confidence.
2. **Knowledge transfer as the primary OSC goal** — the client must be able to sustain the migration past consulting engagement. If they can't, the project fails on a long timeline even if it "succeeds" short-term.

**Migration definition of success:** The new search engine returns *more relevant* results for customers, AND is more operationally and/or financially appropriate for the client. Both conditions. A migration that only satisfies the second (cost savings, license swap) without the first is a morale and credibility risk.

---

## When NOT to Migrate

This deserves to come first. Before investing in migration, challenge the premise:

> **"If the migration is like-for-like with no known customer benefit — don't do it. Improve search quality using the existing platform instead."**

Red flags that suggest migration isn't the right move:
- Migration is purely political (license fees, internal org pressure) with no visible customer benefit
- Team has no clarity on what "better search" means for customers
- No analytics exist to measure current search quality — you're flying blind
- The existing platform has significant untapped tuning potential that's never been explored

If you must proceed with a politically-driven migration, acknowledge it honestly, set low relevance expectations, and focus energy on knowledge transfer and infrastructure improvement.

---

## Team Roles (Who You Need)

A migration needs all of these covered. Roles can be doubled up on small teams, but gaps will create problems:

For the compact canonical model, tier guidance, and specialist add-on roles, see
[`roles-and-escalation-patterns.md`](/opt/work/OSC/agent99/04-skills/solr-to-opensearch-migration/references/roles-and-escalation-patterns.md).

| Role | Owns |
|------|------|
| **Stakeholder** | Aligning search improvements with financial/corporate benefit. Without this, migrations lose funding mid-stream. |
| **Product Owner** | Ensuring search improvements meet actual customer information needs — not just what the team *thinks* customers need. |
| **Project Manager** | Planning, prioritizing, translating customer needs into features. Manages the workstream timeline. |
| **Product Developer** | Design and UX implementation. Often underinvolved in migrations until too late. |
| **Content Owner** | Defining the content set, coordinating content access and transport. **Often the critical path.** |
| **Metadata Owner** | Synonyms, lemmatization, spelling dictionaries, taxonomies. Manages the assets that make tuning possible. |
| **Architect** | Integration strategy, cross-cutting concerns, big-picture technology fit. |
| **Search Relevance Strategist** | Solution strategy for search improvements. Owns the "what are we optimizing for" question. |
| **Search Relevance Engineer** | Search engine tuning, measurements, experiments. Executes the hypothesis-driven work. |
| **Software Engineer** | Implementation of functionality and features. Builds the pipeline, integration layers, product UI. |
| **Data Analyst** | Analytics access, customer engagement signals, judgment/rating data acquisition. |
| **Platform Ops / SRE** | Monitoring, HA/DR readiness, capacity planning, operational runbooks, and production support posture. |
| **Security / Compliance Owner** | Access control, privacy, IAM/SSO review, and enterprise approval path. |
| **QA / Acceptance Lead** | Regression evidence, user acceptance criteria, and release/cutover validation. |

**Common failure mode:** Not enough people, or people who are under-committed. If the client has the resources but won't assign them, flag this as critical immediately — not after the first milestone slips.

---

## Prerequisites (Gate Before Starting)

Do not begin migration work until all of these are true:

- [ ] Stakeholders have communicated a measurable definition of success
- [ ] Project scope, team, and goals are well-defined and agreed
- [ ] Team understands the *benefits and reasons* for migration (not just "we have to")
- [ ] There is a clear path to access the content being migrated
- [ ] There is a clear path to customer analytics (existing, or a plan to instrument)

If analytics don't exist yet: instrument the live product and gather at least 2-4 weeks of real query data *before* starting migration work. You cannot measure relevance improvement without a baseline.

---

## Project Workstreams

Run these in parallel with explicit owners and cross-workstream sync cadence:

| Workstream | Key concerns |
|------------|--------------|
| **Content** | Access, volume, freshness, pipeline to new engine |
| **Pipeline** | Extract → Enrich → Transform → Load. Separate from reindexer. |
| **Analytics** | Customer query data, engagement signals, ongoing instrumentation |
| **Offline Testing** | Judgment sets, relevance metrics, tooling (Quepid, RRE) |
| **Operations/Performance** | Infrastructure, HA, DR, monitoring, alerting |
| **Search Experience** | UI/UX, facets, typeahead, result display |
| **Search Relevance** | Schema design, query shape, analyzer tuning, hypothesis experiments |

---

## Risk Register (Known Migration Risks)

| Risk | Mitigation |
|------|-----------|
| **Content access is slow or blocked** | This is the #1 reason migrations miss milestones. Estimate generously, prioritize early, escalate immediately when delayed. Get content access on day one. |
| **Vague understanding of customer information needs** | Instrument analytics on the live product before migration. Gather 2-4 weeks of real query data minimum. |
| **Project outlasts consulting engagement** | Prioritize knowledge transfer as the first goal, not an afterthought. The client must own the result. |
| **Like-for-like migration with no clear benefit** | Challenge whether migration is the right answer. Improving the existing platform may be better ROI. |
| **Team under-staffed or under-skilled** | Multiple hats are fine if agreed up front. Under-commitment from a capable team is a red flag — escalate. |
| **Budget/complexity surprise** | Reframe as a Proof of Concept to better estimate full costs. Stake the ground early. |
| **Goalposts moved / leadership change** | Pivot to search quality improvement on the existing platform — keeps momentum and delivers value regardless of migration outcome. |
| **Relevance on new engine not meeting expectations** | Document what you've tried, seek external input (other consultants, community). Don't iterate in silence. |

---

## Phase 0: Preparation

Before any technical work begins:

1. **Stand up a project wiki.** Migrations generate heavy analysis and comparison notes. Everyone must contribute. This is non-negotiable — undocumented decisions become tribal knowledge that leaves with consultants.
2. **Document current architecture.** Map every system component impacted by the migration. Know your blast radius.
3. **Inventory functional capabilities.** List everything the existing search platform does, especially features that may be absent in the target engine. These are the complex parts of the project.
4. **Confirm target platform.** If the team hasn't decided (Solr vs OpenSearch/Elasticsearch), decide and document it now with rationale.

---

## Data Preparation

### Content
- Define and formally declare the content set (agree with the whole team)
- Upload to a shared, accessible location
- Analyze: average doc size, total volume, markup format, field inventory
- Estimate impact on schema and index configuration
- Budget infrastructure costs from this analysis

### Queries
- Gather customer queries from analytics and product owner
- Categorize/classify manually — understand the *types* of information needs, not just the long tail
- Build visualizations: word clouds, classification charts
- Create user stories from the information needs
- Define the judgment query superset (the queries you'll use for offline relevance testing)

### Metadata Assets
Inventory these early — they take time to acquire and refine:
- Lemmatization files
- Stop word lists
- Synonym dictionaries
- Taxonomies/ontologies
- Spelling dictionaries
- Entity databases
- Proprietary data for augmentation

---

## The "Hello Search!" Milestone

This is a deliberate motivational milestone, not just a technical checkpoint. The goal is to show the team something working — even imperfectly — to build momentum.

Deliverables:
- Schema defined (relevance fields, facet/filter fields, exotics like geo)
- Content indexed
- Initial query shape defined
- Prototype search interface (can be CLI, admin UI, or minimal web page)
- Demo to the full team: "we can run a query"

**Why this matters:** Migrations are long. People lose faith. A working demo — even a rough one — is worth more than three months of architecture diagrams for team morale. Do this early and celebrate it.

---

## Relevance Measurement Framework

### Tooling Options

| Tool | Type | Notes |
|------|------|-------|
| **Quepid** | Offline | Industry standard for judgment-based relevance testing. Use for baseline and regression. |
| **RRE (Rated Ranking Evaluator)** | Offline | CI/CD-integrated relevance testing. Good for automated gates. |
| **Search-Collector** | Online | Implicit feedback collection from production traffic. |
| **A/B testing** | Online | Side-by-side comparison with traffic splitting. Requires sufficient volume. |
| **Interleaving** | Online | More statistically efficient than A/B for relevance comparison. |

### Metrics (Choose Based on Customer Needs)

- **P@k / R@k / F1@k** — Precision/recall at rank k. Good for known-item search.
- **nDCG** — Normalized Discounted Cumulative Gain. Best for graded relevance (not just binary). Standard for most search use cases.
- **ERR** — Expected Reciprocal Rank. Good when users stop at first relevant result.

**Always measure apples-to-apples between old and new engine.** Same queries, same judgments, same metric. Without this, comparison is meaningless.

### Judgment Acquisition

Two sources, both required:
1. **Customer analytics** — implicit signals (clicks, dwell time, reformulations). Reflects actual behavior. Noisy but high volume.
2. **Human judgments** — explicit ratings. Requires methodology agreement, initial set creation, validation, and a growth plan. Expensive but ground truth.

Form methodology and get team agreement before collecting judgments. Disagreement on *what counts as relevant* is a project-stopper if discovered late.

---

## The Baseline → Tune Loop

This is the core operating rhythm once search is running:

```
measure → log → analyze → decide → report → (repeat)
```

### Baseline (first pass):
- Run measurement tools
- Log results — this is "what we need to beat"
- Communicate to stakeholders
- Set realistic targets (set the bar low, then exceed it)
- Identify best/worst queries and information needs

### Tuning (ongoing):
- One hypothesis = one story in the sprint
- Discard or promote each experiment based on measurement
- Never tune without measuring — opinion-based tuning destroys credibility
- Communicate wins and losses to stakeholders — transparency builds trust

**The tuning loop is never "done."** It becomes part of the team culture, not a migration phase.

---

## Reporting Culture

Establish data-driven culture from day one:

**Proactive dashboards:**
- Relevance KPI dashboard (nDCG trends over time)
- Performance dashboard (latency, throughput, error rates)
- Operational dashboard (cluster health, indexing lag)
- Experience dashboard (A/B results, engagement metrics)

**Reactive alerting:**
- Relevance KPI thresholds
- Performance KPI thresholds
- Engagement KPI thresholds (search abandonment, zero-result rate)

If clients can scrutinize your data openly, they trust you. Black-box consulting that only shows wins destroys trust when problems emerge.

---

## Infrastructure / Operations Checklist

Each of these is months of effort for a mature platform. Introduce them early so ops teams aren't surprised:

- **Security** — auth model, encryption at rest/transit, network isolation
- **Deployments** — CI/CD pipeline, blue/green or rolling, config management
- **High Availability** — multi-node, replica placement, failure scenarios
- **Disaster Recovery** — backup strategy, RTO/RPO definitions, restore testing
- **Cluster Sizing** — initial sizing, growth plan, scaling triggers
- **Sharding** — shard count strategy, rebalancing plan
- **Replication** — replica count, cross-AZ/cross-region requirements
- **Monitoring** — cluster health, slow logs, JVM metrics, disk usage
- **Alerting** — thresholds, on-call routing, runbooks

> "A production search engine is a living creature that needs to be fed, cared for, and kept happy."

---

## Common Issues Playbook

| Issue | Response |
|-------|----------|
| **Team under-staffed / under-skilled** | Multiple hats if needed. Under-commitment from capable team → escalate as critical. |
| **Content taking longer than estimated** | Revise timeline, raise flags immediately, engage stakeholders — they will help unblock. |
| **Bikeshedding / analysis paralysis** | Run a one-sprint micro-project: small content set, basic index, show queries. Momentum over perfection. |
| **Budget surprise** | Reframe as PoC to estimate full costs. Explicit stake in the ground. |
| **Goalposts moved / leadership change** | Pivot to relevance improvement on existing platform. Maintain value delivery. |
| **Political migration with no customer benefit** | Acknowledge it, focus on knowledge transfer and infra improvement. Finish cleanly. |
| **Nobody agrees on what's relevant** | Reveal disagreement with data. Human judgment exercise + reliability analysis. Customer analytics as arbiter. |
| **Relevance not meeting expectations despite effort** | Document trials, seek external input. Don't iterate in isolation. |
| **Knowledge holder departing** | See dedicated section below. Capture knowledge and automate manual processes before the person leaves. |

### Knowledge Holder Departure (The "Bus Factor" Pattern)

One of the most common and most underestimated risks in migration engagements: a single person owns a critical process or asset, and they are leaving — or could leave — during the migration window.

**Common manifestations:**
- One person manually maintains the synonym dictionary (especially part-number cross-references)
- One person knows the undocumented boost rules or relevance tuning logic
- One person wrote the indexing pipeline scripts and never documented them
- One person understands the access-control business rules

**Why migrations surface this:** Migrations force an inventory of everything search depends on. Manual processes that were invisible during steady-state become visible — and fragile — when you try to reproduce them on a new platform.

**Response pattern:**
1. **Identify during intake.** Ask explicitly: "Are there any processes or knowledge that depend on a single person?" Most clients won't volunteer this — ask about each asset type (synonyms, boosts, pipeline scripts, access rules).
2. **Prioritize capture over automation.** Get the current state exported and documented *immediately*, even if the format is messy. You can automate later; you can't automate what you've lost.
3. **Automate as part of migration.** The migration is the natural moment to replace manual processes. A manually maintained synonym file should become a build artifact generated from a source system (ERP, PIM, taxonomy service). A manually applied boost rule should become a configuration-driven relevance policy.
4. **Don't carry the manual process forward.** Migrating a manual process to a new engine is carrying debt to a new house. If the person leaves, the process dies on both platforms.

**War story (composite):** Client's parts catalog had a 20% dependency on old-to-new part-number rewrites, maintained manually by one person in a text file. That person's departure was announced mid-migration. The team scrambled to export the file, but discovered that ~30% of the entries existed only in the maintainer's "working copy" and had never been committed. Resolution: emergency knowledge-capture session, then automated the mapping by sourcing part supersession data directly from the ERP. Total delay: 2 weeks. If the departure had happened 3 weeks later, the data would have been partially lost.

**Decision heuristic:** If a manual process owner is departing, treat knowledge capture as a P0 task — ahead of schema design, ahead of query translation. You can design a schema without the person; you cannot recreate their undocumented synonym entries.

---

## Session Management

Migrations are multi-session engagements. A single intake conversation rarely captures everything.
Structure sessions deliberately to build momentum and avoid rework.

### Session Cadence

| Session | Goal | Typical duration |
|---------|------|-----------------|
| **Session 1: Foundation intake** | Map content sources, query profile, access control, team roster. Identify major risks. | 60-90 min |
| **Session 2: Gap fill** | Close open questions from session 1. Review data artifacts received. Begin design-level discussions. | 60 min |
| **Session 3: Design review** | Walk through proposed mapping, query translations, and task plan. Get client sign-off on approach. | 60-90 min |
| **Ongoing** | Sprint-level check-ins during build and validation phases. | 30 min |

Not every engagement needs this exact cadence. Adjust based on client availability and complexity.
The key principle: **each session should have a defined goal and produce a tangible artifact.**

### Snapshot Discipline

After each session, capture state and tag it:

1. **Write the session document** into `03-specs/[client]/intake/session-NN-[topic].md` with structured sections: what was covered, what was answered, what remains open, action items with owners.
2. **Commit and tag** with `v0.0-intake-session-NN`. This creates an immutable reference point for "what we knew after session N."
3. **Update the open questions table** — carry unanswered questions forward with their original numbers so they can be referenced across sessions.

**Why tags matter:** Clients often ask "what changed since last time?" The answer is `git diff v0.0-intake-session-01..v0.0-intake-session-02`. This is faster and more accurate than trying to summarize from memory.

### Milestone Tags

| Tag | Meaning |
|-----|---------|
| `v0.0-intake-session-NN` | Session notes captured, homework assigned |
| `v0.1-foundation-lock` | All intake blocks answered or tracked with owners. Ready for design. |
| `v0.2-design-lock` | Mapping, query translations, and task plan reviewed and accepted by client. |
| `v0.3-hello-search` | Working demo with sample corpus. Team has seen queries run. |
| `v0.4-dual-write` | Both engines receiving production data. Shadow comparison active. |
| `v1.0-cutover` | Production traffic fully on OpenSearch. Solr warm standby begins. |

### Carrying Forward Open Items

Each session document includes an "Open Questions" table with columns: number, question, assigned to, priority, status. Questions keep their original number across sessions — don't renumber. This allows cross-referencing: "Question 16 from session 1 was answered in session 3."

When a question is answered in a later session, update its status but leave it in the table for traceability. The intake is complete when all High-priority questions show status "Answered" or "Accepted as out-of-scope."

---

## Stakeholder Communication Strategy

Migrations involve people at different levels of detail and different levels of concern. Not everyone needs the same information at the same time.

### Audience Segmentation

| Audience | What they care about | What to share | When |
|----------|---------------------|---------------|------|
| **Executive sponsor** | Timeline, budget, risk, go/no-go | Risks table, phased timeline, milestone status. No technical detail. | Major milestones + escalations |
| **Product manager** | Scope, user impact, acceptance criteria | Requirements, design decisions that affect user experience, validation plan | Weekly or per-sprint |
| **Primary contact (search lead)** | Everything — they are the conduit | Full session documents, open questions, design artifacts | Every session |
| **Technical team members** | Their specific domain questions and action items | Only their assigned questions and data artifact requests. Don't dump the full doc. | As needed per homework table |
| **Operations / infrastructure** | Provisioning, monitoring, failback, capacity | Tech steering doc, monitoring plan, cutover plan | When provisioning starts + pre-cutover |
| **Full team** | Kickoff context, overall approach | Completed foundation document as a "kickoff read" | After intake is complete (foundation-lock) |

### Principles

- **Widen the circle gradually.** Start with the primary contact (and optionally product manager). Add team members as their specific input is needed. Share the full picture with everyone only after the foundation is solid.
- **Don't share draft with the whole team.** Half-formed plans generate more questions than answers. An incomplete intake doc shared broadly creates confusion. Share it when it's at "foundation-lock" quality.
- **Assign homework, not documents.** Instead of sending Kilroy the full intake doc and asking him to "check the access control section," send him the 3 specific questions you need answered. People respond to concrete asks, not reading assignments.
- **Use the session document as the single source of truth.** Don't maintain separate status updates, email summaries, and session notes. One document, one location, git-tracked.
- **Escalation path is through the sponsor, not around them.** If a team member is unresponsive, escalate through the sponsor (Erin), not by cc'ing their manager directly. The sponsor owns resource allocation.

### Communication Artifacts

| Artifact | Audience | Cadence |
|----------|----------|---------|
| Session intake document | Primary contact + PM | Per session |
| Open questions / homework list | Individual team members (their items only) | As assigned |
| Risk summary (1-page) | Sponsor | At major milestones or when risks change |
| Phase completion summary | Full team | At each milestone tag |
| Design review deck / walkthrough | Technical team | Once, at design-lock |

### Anti-Patterns

- **"Weekly status email to everyone"** — becomes noise. People stop reading. Use milestone-based communication instead.
- **"Let's get everyone in a room for the intake"** — too many people in intake produces shallow answers. The search lead knows the system; the sponsor knows the politics. Interview them separately.
- **"I'll just send the whole doc"** — respects nobody's time. Excerpt the relevant section for each person.

---

## Communication Principles

- Open channels for challenges, blockers, venting — problems fester when hidden
- Stay positive when discussing complexity — negativity is contagious in long migrations
- Celebrate and praise wins explicitly — migrations are hard and teams need fuel
- Enough on-site time — remote-only migrations lose the informal alignment that keeps things on track
- Recurring check-ins: standups, planning, refinement, retrospectives
- Knowledge sharing: sprint demos, milestone demos, wiki reviews, code reviews, training sessions

---

## Definition of Done

A migration is complete when:
- New engine serves all production search traffic
- Relevance metrics meet or exceed baseline on agreed KPIs
- Client team can independently deploy, operate, tune, and maintain
- Documentation is complete and on the wiki
- Runbooks exist for operational scenarios
- Monitoring and alerting are active
- Rollback procedure is documented (even if Solr is decommissioned)
- Retrospective completed with OSC team
