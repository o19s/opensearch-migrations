# Northstar Atlas Knowledge Hub: Migration Intake Session 01

**Date:** 2026-03-19
**Consultant:** O19s Migration Practice (via skill)
**Client:** Nate (Seager), Search Lead, Northstar Industrial Systems
**Session type:** Foundation content gathering
**Status:** Phase 00 — Content Gather & Prep

---

## Team Roster

| Role | Name | Allocation |
|------|------|------------|
| Executive Sponsor | Erin | As needed |
| Product Manager | Paul | ~20% |
| Search Lead | Seager (Nate) | Primary contact |
| Solr Engineer | Sonny | ~20% |
| AWS Architect | Andrea | ~20% |
| Relevance Lead | Reese | ~20% |
| Integration Engineer | Ian | ~20% |
| Security Lead | Kilroy | ~20% |

**Staffing note:** Most team members are at ~20% allocation across multiple projects. OSC carries the bulk of migration work. Erin needs to confirm guaranteed response windows (24-48 hrs) for key dependencies.

---

## Content Sources & Indexing Pipeline

| Content type | Source system |
|--------------|-------------|
| Product | ERP |
| Part | ERP |
| Manual | CMS |
| Bulletin | CMS |
| Case | **UNKNOWN — action item** |

**Indexing pattern:**
- Nightly full-sync batch from source systems
- Hourly incremental updates (dozens to ~1000 docs per batch)
- Clean full rebuild from source is possible — no Solr-only data

**Enrichments in pipeline:**
- **PII redaction service** — replaces sensitive content with `[[redacted]]`. Applied during indexing. Must be available during reindex.
- **Popularity scoring API** — `http://ns.com/api/content/score?docId=1234`. Merges scores into documents at index time.

---

## Query Behavior & Relevance

**Analytics available:**
- Fusion click logs with session IDs (queries, shown doc IDs, sessions)
- Solr query logs

**Search profile:**
- 80% exploratory search / 20% known-item lookup (part numbers, model numbers, error codes)
- Average query length: ~2.8 tokens
- Shifted from 90% lookup / 10% search → 80% search / 20% lookup after Fusion deployment 5 years ago

**Performance targets:**
- p92 @ 300ms — nice-to-have
- 600ms hard ceiling — firm requirement
- Leadership prioritizes quality of results over speed

**Traffic pattern:**
- 2.7M queries/day average
- Predictable spikes at 12:15, 1:15, 2:15, 3:15 (~15 min each) — post-lunch return pattern
- Peak season: March, April, May ("Spring is our Christmas")

---

## Access Control & Entitlements

**Mechanism:** Enterprise SSO — details pending (Kilroy to provide)

**Filter dimensions (from schema):**
- `visibility_level`
- `region`
- `dealer_tier`
- `business_unit`

**Access profile granularity:** Unknown — question pending (role-based with ~5-10 profiles, or per-user?)

**Data leak history:** None to date.

**Note:** Entitlement validation during migration is non-negotiable regardless of clean history.

---

## Synonyms & Linguistics

**Synonym strategy (split application):**
- **Index-time:** Part-number cross-references, domain-specific terminology
- **Query-time:** General English synonyms, broader equivalences
- Synonym list is "extensive and possibly over-engineered" — audit recommended during migration

**Part-number cross-references:**
- 20% of catalog depends on old→new part-number rewrites/redirects
- Currently maintained manually by Milton (single person, departing)
- **Critical action:** Automate via ERP supersession data before knowledge is lost

**Stopwords:**
- No standard English stopword list in use
- Curse-word stoplist applied at query time only
- Separate offline process sanitizes indexed profanity
- Philosophy: "index everything, clean up after"
- Previous Lucidworks consultant advised ignoring standard stopwords — O19s recommendation: audit for domain-specific load-bearing stopwords rather than blanket enable/disable

---

## Field Collapsing & Grouping

**Status:** Known to be in use, details unknown.

**Action items:**
- Sonny to identify: which search flows use collapsing, what field is collapsed on
- Search solrconfig.xml or application code for `group=true`, `group.field`, `collapse`, `CollapsingQParserPlugin`
- This is a **redesign zone** — OpenSearch `collapse` exists but behaves differently from Solr's implementation

---

## Cutover & Rollback

**Target date:** April 1, 2026 (already passed)

**Recommended reframe — phased program:**

| Phase | Deliverable | Timing |
|-------|------------|--------|
| Foundation | Spec complete, gold query set, domain provisioned | Now → 2-3 weeks |
| Hello Search | Working demo, sample corpus, top queries running | +2 weeks |
| Dual-write | Both engines receiving production data, shadow comparison | +2-4 weeks |
| Validation | Relevance measured, entitlements verified, performance confirmed | +2-3 weeks |
| Cutover | Gradual traffic shift — after peak season | June+ |

**Dual-write:** Leadership supports running both systems. No budget concern for parallel infrastructure.

**Failback requirement:** Minutes. Existing routing infrastructure may already support this — **needs investigation** (Andrea / infra team).

**Blackout periods:** March-April-May (current peak season). **Do not cut over during Spring peak.**

---

## Monitoring & Observability

**Current state:**
- Fusion built-in monitoring (team is unhappy with it)
- Grafana + Prometheus available in-house
- AWS monitoring capabilities available
- Open to Datadog but not recommended yet

**Failback routing:** Unknown mechanism — assumed to exist based on other apps. Needs verification of layer (LB/mesh/DNS), ownership, and switch speed.

**Zero-result rate / search abandonment:** Unknown — question pending.

**Recommendation:** Use existing Grafana + Prometheus stack. OpenSearch APIs are Prometheus-scrapable. Define dashboard specs during build phase.

---

## Open Questions (Carry to Next Session)

| # | Question | Assigned to | Priority |
|---|----------|-------------|----------|
| — | Where do case documents originate? | Nate / Ian | High |
| 9 | How many access profiles (role-based or per-user)? | Kilroy | High |
| 16 | Part supersession — ERP-driven or manual only? | Ian / ERP team | High |
| 17 | Which search flows use field collapsing? | Sonny | Medium |
| 18 | What field is collapsed on? | Sonny | Medium |
| 19 | Can collapsing be temporarily removed during migration? | Nate / Paul | Medium |
| 20 | Other bus-factor-of-1 risks besides Milton? | Nate | Medium |
| 33 | Zero-result rate / search abandonment tracking? | Reese | Medium |
| — | SSO details for entitlement filtering | Kilroy | High |
| — | Failback routing mechanism and ownership | Andrea / infra | High |

---

## Data Artifacts Needed

| Artifact | From | Priority | Status |
|----------|------|----------|--------|
| Current synonym file (full export) | Sonny / Milton's files | High | Not started |
| Top 200 queries by volume (Fusion) | Reese | High | Not started |
| Zero-result query report | Reese | High | Not started |
| Query reformulation chains (session-based) | Reese | Medium | Not started |
| Solr slow query log (>500ms) | Sonny | Medium | Not started |
| Facet usage data | Fusion analytics | Low | Not started |
| Part-number supersession table from ERP | Ian | High | Not started |
| Profanity/curse-word stoplist | Sonny | Low | Not started |

---

## Key Risks Identified This Session

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Milton departing — part-number synonym maintenance lost | **Critical** | Automate via ERP supersession table before knowledge leaves |
| Team at 20% allocation — dependency bottlenecks | **High** | Erin to guarantee 24-48hr response windows for key people |
| Peak season overlap with migration timeline | **High** | Do not cut over during March-May; use dual-write for safety |
| April 1 target already passed — expectation management | **Medium** | Reframe as phased program with Erin |
| Failback routing assumed but unverified | **High** | Andrea to investigate and document actual mechanism |
| Undocumented collapsing behavior | **Medium** | Sonny to audit before migration design |
| Synonym list "possibly over-engineered" | **Medium** | Audit against gold query set during build phase |

---

## Consultant Notes

- Client team is pragmatic, leadership prioritizes quality over speed — good engagement posture
- Fusion click logs with session IDs are a strong asset — better than typical starting position
- The 80/20 search-vs-lookup shift means BM25 scoring changes will be user-visible — needs careful relevance measurement
- PII redaction and popularity scoring API are pipeline dependencies that must survive migration
- "Index everything, clean up after" philosophy is pragmatic and compatible with OpenSearch patterns
- Recommend "Hello Search" milestone early to build team confidence and demonstrate progress
