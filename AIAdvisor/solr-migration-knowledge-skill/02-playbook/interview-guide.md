# Expert Interview Guide: Sessions 2–3
**Scope:** Expert-led discovery and design review — the sessions where OSC earns its fee by challenging assumptions, exposing hidden complexity, and presenting real choices.
**Audience:** OSC consultants leading migration engagements
**Companion to:** `intake-template.md` (Session 1: Foundation Intake)
**Source:** Derived from assessment kit source material + consulting-methodology.md session cadence
**Last reviewed:** 2026-03-19  |  **Reviewer:** AI draft — needs expert review

---

## How This Guide Connects to the Engagement

| Session | Guide | Goal | Duration |
|---------|-------|------|----------|
| **Session 1** | `intake-template.md` | Foundation intake: map content, queries, access control, team roster. Identify major risks. | 60–90 min |
| **Session 2** | This file, Part 1 | Gap-fill and assumption challenge: validate Session 1 answers, challenge unsupported claims, present architecture options. | 60 min |
| **Session 3** | This file, Part 2 | Design review and readiness decision: walk through proposed mapping, query translations, readiness gates. Go/no-go for implementation planning. | 60–90 min |
| **Ongoing** | Sprint check-ins | Build and validation phase check-ins. | 30 min |

Session 1 collects *facts*. Sessions 2–3 challenge *assumptions* and make *decisions*.

See `consulting-methodology.md` → Session Management for snapshot discipline, milestone tags, and open-item carry-forward protocol.

---

## Key Judgements

> **This is where OSC's value lives.** These are not neutral observations — they are opinionated positions earned from migration engagements.

1. **Session 2 is where the real work happens.** Session 1 is data collection — anyone with a checklist can do it. Session 2 is where you challenge assumptions, expose contradictions, and present choices. If Session 2 doesn't make the client slightly uncomfortable, you probably didn't push hard enough.

2. **Never proceed to design review without a relevance baseline or an approved baseline plan.** Designing a migration target without measurement is like tuning a piano without a tuning fork. You'll finish, and it will sound wrong, and you won't be able to explain why.

3. **"Full parity" is almost never achievable or desirable.** Reframe as "preserve what matters, improve what you can, drop what nobody actually uses." The client who insists on full parity is usually afraid of change, not attached to specific behaviors. Help them name the 5 behaviors that actually matter.

4. **The single biggest predictor of migration failure is unclear ownership, not technical complexity.** A team with clear ownership and simple technology will outperform a team with no ownership and brilliant architecture every time.

5. **Architecture option cards work better than open-ended discussions.** Presenting 2–3 concrete options with tradeoffs gets faster and better decisions than asking "what do you want?" Clients don't know what they want until they see the choices.

6. **Contradictions are findings, not side notes.** When the product owner says "relevance is critical" and the search lead says "nobody looks at search quality metrics," that's not a miscommunication — it's a risk. Record it, name it, and make both parties aware.

7. **If the client can't name their top 5 query patterns, they don't understand their search well enough to migrate it.** Run a query analysis sprint before design, not after.

---

## General Rules for Expert Interviews

Adapted from the assessment kit interview methodology:

- **Start from the intake findings, not a blank conversation.** You already have Session 1 data — use it. "In Session 1 you said X. Let's dig deeper."
- **Ask for examples, not abstractions.** "Show me a query that works well and one that doesn't" beats "describe your relevance strategy."
- **Separate facts from assumptions.** Label every claim as `Known`, `Estimated`, or `Unknown`. Estimated is fine — false confidence is not.
- **Name redesign areas explicitly.** Don't hint. Say "this feature will need to be redesigned, not ported."
- **Record contradictions as findings.** When two people give different answers to the same question, that's a discovery, not an error.
- **Present options only when enough context exists.** Premature option presentation overwhelms. Wait until you have enough background to make the options meaningful.
- **Use the prompting pattern** for questions involving tradeoffs or uncertainty:
  1. Ask the main question
  2. Offer a best-guess fallback ("not sure? choose the closest fit")
  3. Say what to do if the respondent is unsure ("label it Estimated")
  4. Provide one short reference if helpful (e.g., architecture option card)
  5. Invite a clarifying sub-question

---

## SESSION 2: Gap-Fill and Assumption Challenge (60 min)

### Pre-Session Preparation

Before Session 2, the consultant should:

- [ ] Review Session 1 intake document — identify gaps, low-confidence answers, and contradictions
- [ ] Review received data artifacts against the artifact request list (see `assessment-kit/artifact-request-checklist.md`)
- [ ] Pre-score the readiness rubric based on Session 1 data (see Mid-Engagement Scoring Checkpoint below) — this reveals where to probe
- [ ] Prepare 2–3 architecture option cards relevant to known decision areas (see `assessment-kit/architecture-option-cards.md`)
- [ ] Review the open questions table from Session 1 — which were assigned, which came back answered?

### Topic A: Architecture and Integration Depth

**Goal:** Validate system boundaries, expose hidden dependencies, and frame target-state choices that the intake didn't reach.

**Questions:**

1. In Session 1 you described your content sources. Walk me through what happens to a document from the moment it changes in the source system to the moment it's searchable. Every step.
2. Are there any systems that *consume* search results besides the primary application? (Reporting, admin tools, SEO sitemaps, recommendations, email alerts?)
3. Where do transforms happen today — in the application, in Solr's update chain, or somewhere in between?
4. Are there any places where Solr is the source of truth — fields that exist in Solr but not in any upstream system?
5. How many index updates per second at peak? What is the acceptable lag between source change and searchability?
6. What happens if search is down for 5 minutes? 30 minutes? 4 hours? Who notices first — users, monitoring, or support tickets?
7. Are there any cross-collection joins, federated queries, or multi-core searches?

**Options to present when relevant:**
- Dual-write vs. batch cutover (see option card #3/4)
- Application-side transforms vs. ingest pipeline transforms (see option card #7/8)
- Denormalization vs. nested/relationship modeling (see option card #5/6)

**Watch for:**
- **Hidden consumers** — "Oh, the BI team also queries Solr directly." Every unknown consumer is a migration surprise.
- **Solr-as-database patterns** — If Solr is the source of truth for any data, migration complexity doubles. Flag as critical.
- **Unsupported plugin assumptions** — Custom UpdateProcessors, QParsers, or RequestHandlers need redesign, not porting.
- **"It just works"** — Code nobody understands is code nobody can migrate. Investigate before migrating.

**Output:**

| System boundary | Direction | Dependency type | Migration impact |
|----------------|-----------|-----------------|-----------------|
| (fill per discovery) | | | |

**Decision heuristics:**
- If Solr is the source of truth for any fields → **P0 risk.** You need a data recovery/reconciliation plan before migration design.
- If custom update processors exist → treat as **redesign items** until replacement design is reviewed and approved.
- If there are more than 3 direct query consumers → inventory all of them before writing a single line of migration code. Hidden consumers are the #1 source of post-cutover incidents.

---

### Topic B: Search and Relevance Depth

**Goal:** Understand ranking behavior, schema complexity, and tuning maturity well enough to predict where BM25 migration will surprise people.

**Questions:**

8. Can you show me 3 queries where search works well today, and 3 where it doesn't? (Get specific examples, not descriptions.)
9. Which query parsers are in use? (LuceneQP, DisMax, eDisMax, custom?) Where in the code are they configured?
10. What boost rules, function queries, or business ranking logic exist? Who owns them? Are they documented?
11. Do you track zero-result rate? What is it?
12. How will the team evaluate whether BM25 scoring produces acceptable results compared to current TF-IDF behavior?
13. Are there function queries or custom scoring functions (`bf`, `bq`, custom `FunctionQuery`)? What business logic do they encode?
14. How do you handle multi-language content, if applicable?
15. Which query behaviors are actually important to preserve vs. merely familiar? Can you rank them?

**Options to present when relevant:**
- Parity-first vs. redesign-first migration posture (see option card #1/2)
- "Better than current" vs. "same as current" acceptance model
- Offline relevance baseline before planning vs. parallel baseline workstream

**Watch for:**
- **No relevance benchmark** — This is the biggest red flag. Without measurement, "search got worse" is unfalsifiable. Escalate immediately.
- **Undocumented boost logic owned by one person** — Bus-factor risk. Capture before migration, not during.
- **"The engines are both Lucene, so ranking should be similar"** — This is the most dangerous assumption in the migration. BM25 vs. TF-IDF produces 30–40% ranking differences in top-10 results. Name this risk explicitly.
- **Assumption that shared Lucene lineage means ranking parity** — It doesn't. Say so clearly.

**Output:**

- Ranked list of query patterns by business criticality
- Boost/ranking logic inventory with owners
- Relevance measurement plan (or gap flag)
- Expected BM25 impact areas

**Decision heuristics:**
- If no relevance baseline exists → **require a measurement plan before implementation planning begins.** This is non-negotiable.
- If the team expects exact ranking parity → require explicit signoff on where parity is realistic and where redesign is required. Document what they signed off on.
- If undocumented boost rules are owned by a single person → treat as a "Knowledge Holder Departure" risk (see consulting-methodology.md). Capture the logic now.

---

### Topic C: Operations and Security Depth

**Goal:** Assess production readiness expectations, understand what operational capabilities will change, and surface compliance constraints that affect design.

**Questions:**

16. What are your current RTO and RPO for search? (Recovery Time Objective / Recovery Point Objective)
17. Do you have canary queries or synthetic monitoring for search today?
18. What compliance frameworks apply? (SOC2, HIPAA, PCI, GDPR, industry-specific?)
19. Who gets paged when search breaks at 2am? What skills do they have?
20. Which operational tuning knobs does the team rely on today that will disappear in managed OpenSearch? (JMX, direct config editing, custom logging, etc.)
21. What signals tell you the difference between bad data, bad query logic, and a platform failure? Can you distinguish them today?
22. Are snippets, autocomplete results, and search logs reviewed for data leakage risk?

**Options to present when relevant:**
- Provisioned vs. serverless OpenSearch (see option card #9/10)
- Application-side authorization vs. engine-enforced filtering (see option card #11/12)
- Snapshot-driven DR vs. higher-cost near-real-time alternatives

**Watch for:**
- **"The application handles filtering"** — Dig deeper. Is it building filter queries (good) or post-filtering result sets (data leak risk)? Check whether snippets, autocomplete, and logs can bypass the filter.
- **No incident owner** — If nobody owns search incidents after cutover, the migration is orphaned the day it ships.
- **No rollback strategy** — "We can always point back to Solr" is not a rollback plan. What are the exact steps?
- **Managed-service knob loss** — Teams accustomed to SSH'ing into Solr nodes and tweaking configs will feel blind on managed OpenSearch. Surface this early so they can plan.

**Output:**

- RTO/RPO requirements
- Compliance constraints affecting index design
- Operational capability delta (what you lose going to managed)
- Security model validation status
- Incident ownership map

**Decision heuristics:**
- If app-side filtering is the only access control → **require explicit review of leakage risk** through snippets, autocomplete, logs, and aggregation results before proceeding.
- If no incident owner is named → escalate as a **delivery risk.** A platform without an owner degrades.
- If the team relies on direct node access for troubleshooting → plan a "managed-service orientation" session before build phase.

---

### Mid-Engagement Scoring Checkpoint

After Session 2, score the engagement's readiness using the rubric below. This is directional — it supports discussion and prioritization, not false precision.

**Score each category 0–3:**

| Score | Meaning |
|-------|---------|
| 0 | Unknown, missing, or unowned |
| 1 | Weak understanding, partial evidence, or inconsistent ownership |
| 2 | Mostly understood with some material gaps |
| 3 | Strong evidence, clear ownership, aligned understanding |

**Categories to score:**

| Category | Score | Notes |
|----------|-------|-------|
| Business clarity | | |
| Success criteria | | |
| Content access | | |
| Feature inventory completeness | | |
| Query/relevance maturity | | |
| Operational readiness | | |
| Security/compliance clarity | | |
| Target platform clarity | | |
| Ownership/governance | | |
| Evidence quality | | |
| **Total** | **/30** | |

**Interpretation:**

| Range | Assessment | Next step |
|-------|-----------|-----------|
| 0–12 | Discovery only. Not ready for strategic planning. | Extend discovery. Do not proceed to Session 3. |
| 13–20 | Partial readiness. Major gaps remain. | Proceed with strategic planning only. Name the gaps explicitly. |
| 21–26 | Viable for strategic planning. Not yet implementation-ready. | Proceed to Session 3 with gap list. |
| 27–30 | Strong planning readiness. | Proceed to Session 3 and gated implementation roadmap. |

**Automatic High-Risk overrides** — mark as High or Critical regardless of total score if:
- Success criteria are undefined
- Content access is blocked or unclear
- Active custom plugins/processors are not yet understood
- No query evidence or analytics exist
- Security model is unclear
- Unsupported parity assumptions remain unchallenged
- No owner can make rollout tradeoff decisions

**Gate recommendation language** (use one):
- `Do not begin implementation planning yet. Continue discovery.`
- `Proceed with strategic planning only. Major readiness gaps remain.`
- `Proceed with gated implementation planning after resolving listed gaps.`
- `Ready for implementation planning with explicit risk controls.`

---

### Common Mistakes Between Session 1 and Session 2

These are real things that go wrong in the gap between intake and expert discovery:

1. **Accepting "we have analytics" without seeing the data.** The client says they have query logs. You arrive at Session 2 and discover the logs are unstructured text files with no session IDs. Require artifact delivery before Session 2, not during.

2. **Not challenging parity expectations early.** By Session 2, the client team has often internally committed to "same as today but on OpenSearch." If you wait until design review to say "that's not realistic," you've wasted a session and damaged trust. Challenge in Session 2.

3. **Skipping the artifact review.** Going straight to questions without reviewing what was delivered (and what wasn't) means you'll re-ask questions that artifacts already answer, and miss gaps that artifacts would have revealed.

4. **Treating "Unknown" answers as blockers instead of findings.** An honest "Unknown" is more valuable than a confident wrong answer. Record it, assign an owner, and move on. Don't let the session stall.

5. **Failing to present options when the context is ripe.** If you've learned enough about the client's write patterns to discuss dual-write vs. batch cutover, present the option card. Don't wait for a "perfect moment" — it won't come.

6. **Not recording contradictions.** When the product owner says "search quality is critical" and the engineering lead says "we don't have any relevance metrics," that contradiction is a finding. Write it down in those exact terms.

---

## SESSION 3: Design Review and Readiness Decision (60–90 min)

### Pre-Session Preparation

Before Session 3, the consultant should:

- [ ] Prepare proposed schema mapping summary (field-by-field, with incompatibility flags)
- [ ] Prepare query translation examples for top 3–5 query patterns (Solr → OpenSearch Query DSL side-by-side)
- [ ] Prepare architecture option cards for any unresolved decision areas from Session 2
- [ ] Update readiness rubric with Session 2 findings
- [ ] Review the open questions table — what's still unanswered?
- [ ] Draft a phased migration timeline based on what you know

### Topic D: Design Walkthrough

**Goal:** Walk the client through the proposed migration design. This is not a rubber-stamp — it's a collaborative review where the client validates that the design reflects their reality.

**Cover:**

1. **Index mapping review** — walk through key field translations. Call out:
   - Fields that change type (e.g., Solr `TextField` → OpenSearch `text` + `keyword` multi-field)
   - `copyField` replacements using `copy_to`
   - Dynamic field strategy (recommend `"dynamic": "strict"` for production)
   - Analyzer chain mapping (where do token filters differ?)

2. **Query translation review** — show side-by-side translations for the top query patterns:
   - DisMax/eDisMax → `multi_match` + `match_phrase` in `bool`
   - Filter queries (`fq`) → `bool.filter` context
   - Boost functions (`bf`/`bq`) → `function_score`
   - Facets → aggregations
   - Any pattern flagged as a redesign zone

3. **Ingestion pipeline review** — how documents flow from source to OpenSearch:
   - Enrichment pipeline design (PII redaction, scoring APIs, etc.)
   - Synonym strategy (index-time vs. query-time split and rationale)
   - Refresh interval strategy for bulk vs. incremental loads

4. **Redesign zones** — features that need rethinking, not translating:
   - Field collapsing/grouping behavior changes
   - Streaming expressions (no equivalent)
   - Custom plugins → application-layer or ingest pipeline replacement
   - Block join → `nested` type migration

**Watch for:**
- **"That looks fine" without engagement** — if the client isn't asking questions about the design, they're either not reading it or not invested. Push for specific feedback.
- **Surprise features** — "Oh, we also use X" discoveries in Session 3 mean Sessions 1–2 missed something. Log it, don't ignore it.
- **Enthusiasm without measurement** — "This is going to be so much better!" is not a go/no-go criterion. Redirect to measurable outcomes.

---

### Topic E: Migration Strategy Selection

**Goal:** Confirm the migration approach and cutover strategy with explicit client buy-in.

**Decisions to confirm:**

| Decision | Options | Recommendation basis |
|----------|---------|---------------------|
| Migration posture | Parity-first vs. redesign-first | Current search quality + team capability |
| Cutover model | Dual-write vs. batch | Risk tolerance + traffic volume |
| Data model | Denormalize vs. nested | Query patterns + update frequency |
| Transform location | Application vs. ingest pipeline | Existing code ownership |
| Platform | Provisioned vs. serverless | Workload predictability |
| Authorization | App-side vs. engine-enforced | Compliance requirements |

For each decision, use the architecture option cards format:
- What are the options?
- When does each fit?
- What are the tradeoffs?
- What does OSC recommend, and why?

**Decision heuristics:**
- If document volume > 50M or traffic > 1M queries/day → **dual-write is strongly recommended.** The risk of a batch cutover at this scale is too high.
- If relevance baseline score doesn't exist → **parity-first is the only defensible posture** until measurement exists. You can't redesign toward "better" without defining "good."
- If the client has < 3 months to production deadline → **recommend phased approach.** A single-sprint migration at this scale is almost always a lift-and-shift that nobody's happy with.

---

### Topic F: Readiness Gate Review

**Goal:** Explicitly walk through each readiness gate with the client. This is the go/no-go decision for implementation planning.

**Readiness gates — implementation planning should not begin until these are reviewed:**

- [ ] Success criteria are documented and approved by sponsor
- [ ] Product owner and architecture owner are named
- [ ] Source content access is confirmed and tested
- [ ] Solr feature inventory is complete (including custom plugins)
- [ ] Top query patterns are known and documented
- [ ] Relevance baseline exists OR a baseline plan is approved with timeline
- [ ] Target platform constraints are validated (AWS region, VPC, version, tier)
- [ ] Security model is documented and leakage risks reviewed
- [ ] Rollback posture is defined at the strategic level
- [ ] Major unsupported assumptions are called out explicitly

For each gate:
- **Status:** Met / Partially met / Not met
- **Evidence:** What artifact or answer confirms it?
- **Owner:** Who is responsible?
- **Next action:** What closes the gap?

If gates are not met:
> `Do not begin implementation planning yet. Continue discovery.`

---

### War Story: The Parity Illusion

> A mid-size e-commerce client migrated from Solr 7 to OpenSearch 2.x. The team assumed that because both engines used Lucene under the hood, ranking would be "basically the same." They did not establish a relevance baseline on Solr before migration.
>
> After cutover, the product team reported that "search got worse" — specific high-value product queries returned different top-5 results. The engineering team couldn't quantify the difference because there was no baseline to compare against. Six weeks were spent in reactive firefighting: manually comparing queries, arguing about whether results were "better" or "worse" based on individual opinions, and escalating to leadership.
>
> The root cause was straightforward: Solr's default TF-IDF scoring and OpenSearch's default BM25 scoring weight term frequency differently. For their catalog (short product titles, long descriptions), this produced roughly 35% difference in top-10 ranking. The fix was relatively simple — adjust BM25 parameters and field boosts — but without a baseline, every change was a guess.
>
> **Lesson:** Measure before you migrate. A 200-query judgment set with Quepid takes 2–3 days to build. The six weeks of post-cutover chaos cost more than the entire migration budget.
>
> **Applied rule:** If the client does not have a relevance baseline or an approved plan to create one, do not proceed past Session 3. This is the one gate that, if skipped, reliably produces engagement failure.

---

## End-of-Session Capture

At the end of each session (2 or 3), capture:

1. **Confirmed facts** — claims that moved from Estimated/Unknown to Known
2. **Challenged assumptions** — beliefs that were tested and found unsupported
3. **Contradictions** — places where different stakeholders gave different answers
4. **New risks** — with severity (Low / Medium / High / Critical)
5. **Decision candidates** — choices that are ready to be made, with the option set
6. **Architecture option areas** — decisions that need option cards prepared
7. **Required follow-up evidence** — specific artifacts, with owners and deadlines
8. **Named decision owners** — who can approve tradeoffs and de-scoping
9. **Updated readiness score** — re-score any categories that changed

Write these into the session document at `03-specs/[client]/intake/session-NN-[topic].md` and commit with tag `v0.0-intake-session-NN`.

---

## Open Questions / Evolving Guidance

- How do we handle clients who want a "migration assessment" but aren't ready to commit to Sessions 2–3? Is there a lighter-weight "migration readiness check" that's a single session?
- What's the right balance between challenging assumptions (which can feel adversarial) and maintaining client trust? The best consultants do both — how do we teach that?
- Should the readiness rubric be shared with the client, or is it an internal OSC tool? Sharing increases transparency but can create score-chasing behavior.
