# Team Structure and Process
**Scope:** Engagement team roles (who does what), communication patterns, meeting cadence. How to structure an O19s migration engagement from a people and process perspective.
**Audience:** OSC engagement leads, project managers, anyone standing up a new migration engagement
**Source:** OSC Playbook slides 6–7, 13, 26–27 + expert annotation
**Last reviewed:** 2026-03-17  |  **Reviewer:** AI draft — needs expert review

---

## Key Judgements

> These bullets are a starting scaffold. Add O19s opinion — especially on which roles are hardest to fill at clients and what breaks when they're missing.

- **Under-staffing is the norm, not the exception.** Clients rarely have one person per role. The question is *which roles can be merged without damage* and *which gaps are blockers*. A missing Search Relevance Engineer is a blocker. A missing dedicated Project Manager usually isn't.
- **The Search Relevance Strategist and Engineer are the roles clients most consistently undervalue — and the ones most critical to a successful migration.** Without them, "migration" becomes a technical lift-and-shift with no relevance improvement, and stakeholders declare it a failure 6 months later.
- **The Content Owner is the most commonly forgotten role.** Everyone assumes content acquisition will be easy. It never is. Name this person on Day 1 and put their deliverables on the critical path.
- **If the Stakeholder can't define success, you don't have a project yet.** No amount of good technical work resolves a missing business goal. Push for a written success definition before the first sprint.
- **Engagement lead (OSC) ≠ Project Manager (client).** OSC's job is direction and quality. The client PM owns timeline, resourcing, and stakeholder management. Conflating these creates confusion about who's responsible for what.

*[Add your own Key Judgements here — particularly about role gaps you've seen sink migrations]*

---

## Canonical Core Roles

Defined in the OSC playbook and normalized here for current use. Each role should be formally assigned and documented at project kickoff. For the compact canonical version with tier guidance and specialist add-on roles, see [`../skills/solr-to-opensearch-migration/references/roles-and-escalation-patterns.md`](/opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/roles-and-escalation-patterns.md).

| Role | Responsibility | Typically Client or OSC? | Risk if Missing |
|---|---|---|---|
| **Stakeholder** | Aligns search improvements with financial/corporate benefit; defines success | Client | No agreed success criteria; goalposts shift post-launch |
| **Product Owner** | Ensures search meets customer information needs; prioritizes stories | Client | Relevance tuning is directionless; no customer context |
| **Project Manager** | Plans and prioritizes; translates information needs into features | Client | Timeline slips; cross-workstream alignment breaks down |
| **Product Developer** | Design and UX for the search experience | Client | Search UI changes blocked or delayed |
| **Content Owner** | Defines the content set; coordinates pipeline access | Client | Content access delayed (the #1 schedule killer) |
| **Metadata Owner** | Manages synonyms, stop words, lemmatization, taxonomies | Client (often missing) | Relevance tuning limited to field weights; metadata assets not leveraged |
| **Architect** | Integration strategy; cross-system technical decisions | Client / OSC | Blind spots in integration complexity; scope surprises |
| **Search Relevance Strategist** | Solution strategy; planning relevance improvements across the system | OSC | Migration devolves into technical lift-and-shift |
| **Search Relevance Engineer** | Search engine tuning; measurements and experiments | OSC | No relevance feedback loop; no way to prove improvement |
| **Software Engineer** | Feature implementation; application-layer changes | Client | Pipeline, API, and integration work stalls |
| **Data Analyst** | Analytics access; identifying customer trends; judgement data | Client (often part-time) | No query analytics; judgement set built from intuition not data |
| **Platform Ops / SRE** | Monitoring, runbooks, capacity, HA/DR, on-call readiness | Client / Platform | Production readiness assumed but unproven |
| **Security / Compliance Owner** | Access control, IAM/SSO, privacy, auditability, review sign-off | Client / Security | Late enterprise blockers or access-control defects |
| **QA / Acceptance Lead** | UAT evidence, regression criteria, acceptance sign-off | Client / QA | Final validation becomes anecdotal and political |

*Note: this is a role model, not a headcount requirement. Small teams commonly merge: Product Owner + Project Manager, Architect + Software Engineer, Strategist + Engineer. Document which person owns which role explicitly — ambiguity is expensive later.*

---

## Kick-off Checklist

Before the first sprint begins:

- [ ] All core roles formally assigned to named individuals (some may share roles)
- [ ] Success criteria documented and signed off by Stakeholder
- [ ] Project scope and timeline proposed and reviewed
- [ ] Project wiki / shared workspace created
- [ ] Communication channels established (see Communication section below)
- [ ] First set of workstreams identified (see Workstreams section below)

---

## Workstreams

A migration is too large to run as a single track. The OSC playbook (slide 13) defines these standard workstreams. Add or remove based on the engagement.

| Workstream | Lead Role | Key Deliverables |
|---|---|---|
| **Content** | Content Owner | Content set defined; pipeline scoped; reindexer plan |
| **Pipeline** | Software Engineer | Extract → Enrich → Transform → Load implementation |
| **Analytics** | Data Analyst | Query logs access; information needs analysis; judgement query set |
| **Offline Testing** | Search Relevance Engineer | Quepid case; judgement set; baseline measurement |
| **Operations / Performance** | Architect + DevOps | Cluster sizing; HA/DR; monitoring; alerting |
| **Search Experience** | Product Developer + PO | Query interface; facets; autocomplete; UX |
| **Search Relevance** | Relevance Strategist + Engineer | Baseline → tune loop; schema; field weights; analyzers |

Cross-workstream alignment meeting (weekly or bi-weekly) is critical — dependencies between workstreams are where schedule surprises hide.

---

## Communication

From the OSC playbook (slide 26). The principle: open channels, no festering problems.

**Standing practices:**
- Recurring OSC check-in (not optional — this is where you catch problems before they become crises)
- Client-facing chat channel (Slack, Teams) — searchable, async, keeps stakeholders visible
- An explicit "this is a blocker" norm — anyone on the team can flag a blocker without ceremony
- On-site time scheduled and protected — especially in early sprints

**When things go wrong:** Don't let problems fester. Surface them openly. The playbook is direct on this: "open the channels and right the ship." Quietly managing a bad situation is how migrations go off the rails in week 8 with no warning.

---

## Meeting Cadence

From the OSC playbook (slide 27). Adapt to the client's existing process — don't impose a new process on top of theirs.

| Meeting | Frequency | Purpose |
|---|---|---|
| **Standup** | Daily | Blockers, yesterday/today, quick coordination |
| **Sprint Planning** | Per sprint | Prioritize stories; assign; estimate |
| **Refinement** | Per sprint | Break down stories; clarify acceptance criteria |
| **Retrospective** | Per sprint | What's working; what isn't; process adjustments |
| **OSC Check-in** | Recurring (weekly or bi-weekly) | Internal OSC alignment; surface issues before they hit the client |
| **Sprint Demo** | Per sprint | Show progress to stakeholders; validate direction |
| **Milestone Demo** | Per milestone | Broader stakeholder review; alignment check |
| **Wiki / Knowledge Sharing** | Ad hoc | Code reviews, training sessions, architecture walk-throughs |

**Knowledge sharing meetings are not optional.** Knowledge transfer is a primary OSC deliverable. If KT sessions keep getting pushed for "more important" things, flag it.

---

## Decision Heuristics

- **If the Content Owner isn't named at kickoff → delay sprint 1.** Don't start without knowing who owns content access. You'll spend week 3 blocked.
- **If a client wants to skip standups → keep the OSC check-in regardless.** You need a regular pulse check even if the client prefers async.
- **If the Stakeholder is unresponsive → escalate in writing.** Success criteria drift is expensive to fix retroactively.
- **If team size < 4 → explicitly document who owns which merged roles.** Ambiguity about who's the "Search Relevance Engineer" on a 3-person team causes gaps that surface in month 3.
- **If the client has a Project Manager but no Product Owner → the PM will fill the PO gap, poorly.** Raise this as a risk explicitly. It means relevance decisions will be made by timeline considerations, not customer needs.

---

## Open Questions / Evolving Guidance

- Is the canonical core-role model still the right framing for smaller engagements (2–3 person client teams)? What's the minimum viable role set?
- How do you handle distributed / async teams that can't do daily standups? What communication practices actually work?
- What's the right OSC-to-client ratio for a healthy engagement? 1 OSC Strategist + 1 OSC Engineer for how large a client team?
