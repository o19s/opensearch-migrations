# Pre-Migration Assessment
**Scope:** Everything before writing a single line of migration code — deciding whether to migrate, what you're walking into, and whether the team is ready.
**Audience:** OSC engagement leads, search relevance strategists
**Source:** OSC Playbook slides 8–11 + expert annotation
**Last reviewed:** 2026-03-17  |  **Reviewer:** AI draft — needs expert review

---

## Key Judgements
<!-- 5-10 expert opinions. Hard-won. Opinionated. Not "it depends." -->

> ⚠️ **This section is the highest-value contribution gap.** The bullets below are extracted from the playbook deck and need senior O19s opinion added. Add your real take — especially where the slide bullet is too diplomatic.

- **"Don't do the migration" is a legitimate outcome of this assessment.** If the migration is like-for-like with no measurable customer benefit, say so clearly and in writing. It's better to lose the migration engagement than to watch a client spend a year and end up with equivalent-or-worse search.
- **Content access is the number-one schedule killer.** It always takes longer than anyone estimates. Get it on the critical path immediately — not in Week 3 when the team discovers the pipeline doesn't exist yet.
- **Vague "success" = guaranteed disappointment.** If stakeholders can't articulate success in measurable terms before kickoff, they'll define it retroactively in a way you can't win. Push hard for quantified goals (nDCG target, latency budget, cost ceiling) in the charter.
- **Analytics before judgements.** You need at least 2–4 weeks of real query data before you can build a useful judgement set. Starting judgements cold — from product owner intuition alone — produces a set that doesn't reflect actual customer behavior.
- **Knowledge transfer is the primary OSC deliverable, not the migration itself.** A migration OSC hands off that the client can't sustain is a failure regardless of technical quality. KT should be a first-class workstream, not a Phase 4 afterthought.

*[Add your Key Judgements here — 2–3 more bullets from your own experience]*

---

## When NOT to Migrate

This is the most important section in this file. Most engagements treat migration as a foregone conclusion. Push back early if any of these apply:

| Signal | What It Likely Means |
|---|---|
| "We want to migrate to reduce license costs" with no relevance goal | The client may be unaware that OpenSearch also costs real money at scale. Run a cost model first. |
| "We want Elasticsearch/OpenSearch because everyone uses it" | Not a reason. Ask: what does the customer get that they don't have today? |
| No analytics on the current system | You can't establish a baseline. You'll have no way to prove the migration improved anything. |
| Less than 2 months of runway before production deadline | This is almost always a recipe for a lift-and-shift that nobody's happy with. |
| The product owner can't describe the top 5 customer information needs | The search team doesn't have enough direction to make good relevance decisions. |
| The existing search is "good enough" by any objective measure | Migrations disrupt. If the status quo is acceptable, the disruption cost may exceed the benefit. |

*[Add more signals from your own experience — especially the ones clients don't want to hear]*

---

## Risk Register

Extracted from the OSC playbook (slide 8). Senior O19s annotation needed on each.

| Risk | Playbook Mitigation | Practical Notes |
|---|---|---|
| Content access is harder or slower than expected | Get content ASAP; put it on the critical path; revise timeline aggressively | *[How early have you seen this surface? What does "content access blocked for 3 weeks" look like in practice?]* |
| Client has vague understanding of customer information needs | Implement analytics on live product; gather query data for 2–4 weeks minimum before design decisions | *[What happens when the client refuses? What's the minimum viable analytics setup?]* |
| Migration timeline extends past OSC involvement window | Prioritize knowledge transfer as the #1 OSC goal from day one | *[How do you structure KT? What does a "client can sustain this" checklist look like?]* |
| Like-for-like migration with no known customer benefit | Don't do it. Improve search on the existing platform instead. | *[How do you deliver this recommendation without losing the relationship?]* |

---

## Prerequisites Checklist

Before kick-off, confirm all of the following are true. If any are missing, flag as a blocker:

- [ ] Stakeholder-defined success criteria exist and are measurable
- [ ] Project scope, team, and goals are documented and agreed
- [ ] Team understands the business and customer rationale for migration (not just the technical)
- [ ] Path to content access is identified — who owns it, how long it takes, what the blockers are
- [ ] Path to analytics access is identified — query logs, click data, engagement signals
- [ ] Key roles are formally assigned (see `team-and-process.md`)

If you are starting an engagement without analytics access, you are running blind. Flag this to stakeholders on Day 1, not Week 6.

---

## Preparation Checklist

Once prerequisites are met, before technical work begins:

- [ ] Engagement wiki / shared notes space created and accessible to full team
- [ ] Current system architecture documented (especially search integration points — what calls Solr, how, and with what query shapes)
- [ ] Functional capabilities of existing search platform inventoried — specifically anything that might not have a direct OpenSearch equivalent (DIH, custom UpdateChain, Carrot2 clustering, CDCR, etc.)
- [ ] Target OpenSearch version selected and documented with rationale
- [ ] AWS vs. self-managed decision made and documented (see `04-skills/.../references/aws-opensearch-service.md` for decision framework)
- [ ] Initial timeline and milestones proposed and reviewed with stakeholders

---

## Common Issues and Relief

Extracted from OSC playbook slide 9. The "Relief" column reflects what the deck says — add real-world texture in the Notes column.

| Issue | Playbook Relief | Notes |
|---|---|---|
| Not enough team members for all roles, or under-committed | Team wears multiple hats; flag under-commitment as critical if resources exist but aren't allocated | *[Which role gaps hurt the most? In your experience, what's the most commonly under-staffed role?]* |
| Content pipeline slower than estimated | Revise timeline, escalate to stakeholders immediately — they can unblock | *[What escalation path actually works? Who do you call?]* |
| Team in analysis-paralysis | Start a one-sprint micro-project: small content set → indexed → some queries → show people | *[What's the minimum viable "Hello Search" demo that unsticks a team?]* |
| Budget/infrastructure surprise | Declare a formal PoC; use it to better predict full production costs | *[What's the cheapest credible PoC setup for a Solr→OpenSearch migration?]* |
| Goalposts moved / leadership change | Pivot to search quality improvement on existing platform; buy time | *[How do you protect the team's morale and the client relationship simultaneously?]* |
| Migration is purely political (cost/license driven) | Bear with it; finish the contract; move on | *[Is there a way to inject customer benefit into a political migration? What's the argument?]* |
| Nobody agrees on what "relevant" means | Use data. Get human judgements. Visualize disagreement. Train the client on basic relevance methodology. | *[What's the fastest path from "no one agrees" to "we have a shared baseline"?]* |
| Relevance not meeting expectations on new engine | Document what you've tried; bring in other OSC members; Friday Share | *[What are the most common reasons relevance underperforms on OpenSearch vs. Solr specifically?]* |

---

## Decision Heuristics

- **If content access is unresolved at kickoff → treat it as a P0 blocker.** Do not start schema design until you have real documents to test with.
- **If the client can't name 5 specific customer information needs → run a query analysis sprint first.** Don't build a migration target state around invented use cases.
- **If the timeline is under 3 months to production → recommend a phased approach.** Dual-write with traffic percentage cutover is safer than a hard cutover for any timeline under 6 months.
- **If analytics don't exist → the first OSC deliverable is analytics setup, not migration planning.** Everything downstream depends on it.
- **If a manual process owner is departing → treat knowledge capture as P0, ahead of schema design.** You can design a schema later; you cannot recreate undocumented synonym entries, boost rules, or pipeline logic after the person leaves. Export first, automate second, migrate third. See "Knowledge Holder Departure" in `consulting-methodology.md` for the full pattern.

---

## Open Questions / Evolving Guidance

- How much weight should we give to Solr EOL/support-window arguments in the "when to migrate" framework? Solr 8.x is in maintenance mode; is that a strong enough forcing function?
- What's the right minimum analytics window before starting judgements? The playbook says 2 weeks to 1 month — does that hold for high-traffic vs. low-traffic products?
- How do we handle clients who want to migrate away from self-managed Elasticsearch (not Solr) — does this playbook apply directly, or does it need a separate branch?
