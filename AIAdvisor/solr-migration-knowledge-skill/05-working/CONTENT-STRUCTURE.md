# Migration Advisor — Content Structure & Work Plan
**Version:** 0.1 draft — 2026-03-17
**Purpose:** Coordination doc for O19s consultants contributing to the knowledge base.
**Goal:** Produce a set of well-structured markdown files that collectively encode expert
migration guidance, usable as an agent skill, Kiro context, or standalone reference.

---

## How to Read This Document

The structure below defines **7 content chunks**, each a discrete, ownable work package.
Each chunk becomes one or more markdown files in a predictable location.

For each chunk you'll find:
- **What it covers** — scope boundary so chunks don't overlap
- **Source material** — what already exists to draw from
- **Gaps** — what still needs original expert content
- **Output spec** — what the finished file should look like
- **Status** — how complete it is today

A consultant taking a chunk should: read the sources, distill the strategic knowledge,
write original content from experience where sources are thin, and follow the output spec.

---

## Target Structure (End State)

```
04-skills/solr-to-opensearch-migration/
├── SKILL.md                          ← routing layer + quick-reference tables (done)
└── references/
    ├── 01-strategic-guidance.md      ← when/why/when-not-to migrate
    ├── 02-source-audit.md            ← inventorying a Solr deployment
    ├── 03-target-design.md           ← designing the OpenSearch solution
    ├── 04-migration-execution.md     ← dual-write, cutover, pipelines
    ├── 05-relevance-validation.md    ← measurement, tools, go/no-go
    ├── 06-operations.md              ← AWS ops, monitoring, ISM, DR
    ├── 07-platform-integration.md    ← Spring Boot/Kotlin (and other platforms)
    ├── consulting-methodology.md     ← OSC process, roles, risks (done ✓)
    ├── aws-opensearch-service.md     ← AWS service specifics (done ✓)
    ├── migration-strategy.md         ← strategy + dual-write detail (done ✓)
    ├── scenario-drupal.md            ← Drupal-specific scenario support
    └── solr-concepts-reference.md    ← Solr feature audit map (done ✓)
```

The five "done" files are first drafts generated from training knowledge.
They need **expert review and enrichment** more than they need to be written from scratch.
The seven numbered files are the primary work packages.

---

## Content Template (Use for Every Chunk)

Every reference file should follow this skeleton. Adapt sections as needed but keep the
opening metadata and the "Key Judgements" section — those are what make files useful to
an agent rather than just an index.

```markdown
# [Chunk Title]
**Scope:** [one sentence — what this file covers and what it deliberately excludes]
**Audience:** O19s consultants advising on Solr→OpenSearch migrations
**Last reviewed:** YYYY-MM-DD  |  **Reviewer:** [initials]

---

## Key Judgements
<!-- The most important things an expert knows that a non-expert wouldn't.
     Opinions, heuristics, rules of thumb, hard-won lessons.
     This section is the heart of the file — 5-10 bullet points. -->

---

## [Section 1]
...

## [Section N]
...

---

## Decision Heuristics
<!-- If X, then Y. Quick pattern-matching for common situations. -->

## Common Mistakes
<!-- What goes wrong when people don't follow the guidance above. -->

## Open Questions / Evolving Guidance
<!-- What we don't know yet, or where the field is changing. -->
```

---

## The 7 Work Packages

---

### Chunk 1 — Strategic Guidance
**Output file:** `references/01-strategic-guidance.md`
**Core question answered:** *Should we migrate? When is it worth it? How do we frame it?*

**Scope:** Migration motivation, business case, when NOT to migrate, how to run the
"should we migrate?" conversation with a client, success definition, scope setting.
Deliberately excludes technical how-to (that's Chunks 2–4).

**Source material to draw from:**
- `references/consulting-methodology.md` — "When NOT to Migrate" section, goals, prerequisites
- `01-sources/community-insights/herodevs-should-you-migrate.md`
- `02-playbook/pre-migration-assessment.md` — current in-repo source for risk framing and migration prerequisites
- `01-sources/opensearch-migration/solrcloud-practitioners-guide.md`

**Gaps (needs original expert content):**
- O19s framing of the "should we migrate?" client conversation — what do you actually say?
- The real business drivers you've seen (license cost, EOL, talent pipeline, cloud-native alignment)
- How to quantify "relevance improvement" as a business case, not just a technical metric
- War stories: migrations that shouldn't have happened, and why

**Output spec:** ~200–300 lines. Heavy on Key Judgements and Decision Heuristics.
Minimal code. Maximum opinion and hard-won perspective.

**Status:** 🔴 Not started — no file yet. Highest % original expert content needed.

---

### Chunk 2 — Source Audit (Solr)
**Output file:** `references/02-source-audit.md`
**Core question answered:** *How do we take stock of what we have in Solr before starting?*

**Scope:** Methodology for auditing an existing Solr deployment. Schema analysis,
query pattern analysis, feature inventory, traffic characterisation, complexity scoring.
Output of this chunk is a structured audit approach, not a list of Solr concepts
(that's `solr-concepts-reference.md`).

**Source material to draw from:**
- `references/solr-concepts-reference.md` — "Pre-migration audit checklist", complexity scoring
- `01-sources/solr-reference/solr-architecture-concepts.md`
- `01-sources/solr-reference/solr-query-features-reference.md`
- `01-sources/solr-reference/solr-schema-concepts.md`
- `01-sources/opensearch-migration/aws-solr-migration-blog.md` — "Understand source state" section

**Gaps (needs original expert content):**
- The actual audit interview questions you ask a client ("walk me through your collections")
- How to pull and read the Solr Schema API, Luke handler, /admin/metrics output
  *(even though live Solr is a future phase, the analysis methodology is relevant now)*
- How to classify collections by migration complexity (quick win vs. months of work)
- Red flags that indicate hidden complexity (undocumented custom plugins, decade-old schema, etc.)

**Output spec:** ~250–350 lines. Should include an audit checklist in a copy-paste-ready
format. A scoring rubric (1–5) for complexity per dimension is especially useful.

**Status:** 🟡 Partial — `solr-concepts-reference.md` covers the feature map.
Audit methodology still needs original content.

---

### Chunk 3 — Target Design (OpenSearch)
**Output file:** `references/03-target-design.md`
**Core question answered:** *How do we design the OpenSearch solution before touching any code?*

**Scope:** Index architecture decisions, mapping design approach, query architecture,
analyzer strategy, relevance strategy (boost/scoring approach), shard topology decisions.
This is the design phase before implementation — "what should it look like?" not "how do we build it?"

**Source material to draw from:**
- `01-sources/opensearch-migration/schema-field-type-mapping.md` — field type decisions
- `01-sources/opensearch-migration/query-syntax-mapping.md` — query design patterns
- `01-sources/opensearch-best-practices/cluster-sizing-and-design.md`
- `01-sources/opensearch-fundamentals/mappings.md`
- `01-sources/opensearch-fundamentals/create-index-api.md`
- `01-sources/community-insights/` — `.htm` files with real-world schema decisions

**Gaps (needs original expert content):**
- Design review checklist: what to verify before any data goes in
- How to handle the "we don't know our query patterns yet" situation (common)
- Alias strategy: why always use aliases, never index names directly
- Multi-index vs single-index vs datastream — decision framework
- When to use nested vs flattened vs join field for document relationships
- Common over-engineering traps (too many shards, too many fields, over-analyzed)

**Output spec:** ~300–400 lines. Decision tables and heuristics more valuable than
code examples here (code is in Chunk 7 / platform files).

**Status:** 🟡 Partial — field mapping and query syntax covered in existing refs.
Architecture decision layer needs original content.

---

### Chunk 4 — Migration Execution
**Output file:** `references/04-migration-execution.md`
**Core question answered:** *How do we actually move the data and switch traffic?*

**Scope:** Data migration patterns (reindex, ETL pipeline choices), dual-write
implementation, historical catchup, cutover sequencing, rollback procedures.
Excludes: infrastructure setup (Chunk 6), relevance measurement (Chunk 5).

**Source material to draw from:**
- `references/migration-strategy.md` — dual-write pattern, traffic shift, rollback
- `01-sources/aws-opensearch-service/aws-opensearch-migration-service.md`
- `01-sources/opensearch-migration/bigdata-boutique-deep-dive.md`
- `01-sources/opensearch-migration/tecracer-migration-2024.md`
- `01-sources/community-insights/Migration of Solr to Opensearch...Medium.htm` — 100M doc migration

**Gaps (needs original expert content):**
- The "historical catchup" problem: how to reindex without blocking production writes
- The sequence_number / document ID strategy: avoiding duplication and missed docs
- How to handle schema changes mid-migration (the pipeline doesn't stop for refactors)
- War stories: data migrations that went wrong and why (duplicate docs, missing docs,
  timezone issues, encoding problems)
- The "dark launch" period: running OpenSearch in shadow mode before anyone trusts it
- Checklist for the day-of-cutover (not theoretical — what do you actually do)

**Output spec:** ~300–350 lines. Should include a day-of-cutover checklist and a
decision tree for pipeline tool selection (Logstash vs Glue vs custom ETL vs reindex API).

**Status:** 🟡 Partial — `migration-strategy.md` has the dual-write pattern.
Execution-level detail and war stories need original content.

---

### Chunk 5 — Relevance Validation
**Output file:** `references/05-relevance-validation.md`
**Core question answered:** *How do we prove the new engine is as good or better?*

**Scope:** Relevance measurement methodology, judgment set construction, tool configuration
(Quepid, RRE, Search-Collector), go/no-go criteria, regression testing, A/B framing.
This is the O19s core competency — probably the highest-value chunk in the whole skill.

**Source material to draw from:**
- `references/consulting-methodology.md` — "Relevance Measurement Framework", baseline/tune loop
- `01-sources/opensearch-best-practices/search-relevance-tuning.md`
- `01-sources/opensearch-best-practices/performance-testing.md`
- `01-sources/community-insights/relevance-scoring-differences.md`
- `01-sources/community-insights/canva-migration-experience.md` — relevance regression section
- `02-playbook/OSC Playbook` — Judgements/Ratings, Baseline, Tuning, Reporting slides

**Gaps (needs original expert content):**
- O19s-specific methodology: how you actually set up a Quepid case for a migration
- How to construct a judgment set when the client has no existing judgments
- How to explain nDCG to a non-technical stakeholder ("your search got 12% better" — but what does that mean?)
- The minimum viable measurement setup: what's the least you can do and still have defensible evidence?
- BM25 vs TF-IDF in practice: what the scoring change actually looks like in results, and how to tune back
- How to frame relevance regressions to clients without losing confidence

**Output spec:** ~350–450 lines. This chunk should be denser than others because it's O19s'
differentiated expertise. Include concrete Quepid configuration steps and judgment methodology.

**Status:** 🔴 Not started as a standalone chunk. Most strategically important to fill.

---

### Chunk 6 — Operations
**Output file:** `references/06-operations.md`
**Core question answered:** *How do we run this thing reliably in production?*

**Scope:** AWS OpenSearch Service operational patterns — monitoring, alerting, ISM policies,
snapshot/backup, scaling, performance tuning, upgrade path. Also covers the handoff from
"migration project" to "steady-state ops team."

**Source material to draw from:**
- `references/aws-opensearch-service.md` — sizing, auth, networking
- `01-sources/opensearch-best-practices/aws-operational-best-practices.md`
- `01-sources/opensearch-best-practices/cluster-sizing-and-design.md`
- `01-sources/opensearch-best-practices/ism-lifecycle-management.md`
- `01-sources/opensearch-best-practices/indexing-speed-tuning.md`
- `01-sources/aws-opensearch-service/` — `.htm` files (AWS official docs)

**Gaps (needs original expert content):**
- What monitoring setup O19s recommends on day one (not the full mature setup — the minimum)
- How to size a cluster when you genuinely don't know the query volume yet
- The "cluster went yellow/red" playbook — what do you check first?
- ISM policies for a typical migration project: what lifecycle rules make sense
- Knowledge transfer checklist: what does the client ops team need to know before you leave?

**Output spec:** ~250–300 lines. Operational runbooks and checklists more valuable
than conceptual explanation here. The AWS docs cover the "what"; focus on the "when" and "why."

**Status:** 🟡 Partial — `aws-opensearch-service.md` has service-level guidance.
Operational runbooks and knowledge-transfer content need original work.

---

### Chunk 7 — Platform Integration
**Output file:** `references/07-platform-integration.md`
**Core question answered:** *How do we wire OpenSearch into the application layer?*

**Scope:** Client library choices and setup across platforms. Spring Boot/Kotlin is the
primary focus given O19s current work, but the structure should explicitly accommodate
other platforms (Rails, Python, Node) as stub sections to be filled later.

**Source material to draw from:**
- `01-sources/opensearch-fundamentals/spring-boot-kotlin-opensearch-client.md`
- `01-sources/opensearch-fundamentals/opensearch-query-dsl-kotlin-examples.md`
- `01-sources/community-insights/client-library-landscape.md`

**Gaps (needs original expert content):**
- Pattern for abstracting OpenSearch behind a SearchService interface
  (so the app layer isn't coupled to the OpenSearch client — important for testing and future migrations)
- Spring Boot config for dual-write: routing writes to both Solr and OpenSearch in parallel
- Error handling strategy: what to do when OpenSearch write fails but Solr write succeeds
- SolrJ → opensearch-java migration: specific class/method equivalences for Java devs
- Stub sections for: Python (opensearch-py), Ruby/Rails (opensearch-ruby), Node.js

**Output spec:** ~300–400 lines. Heavy on code patterns. The Spring Boot/Kotlin section
should lean on the source material in `01-sources/opensearch-fundamentals/`; this file is
about architecture patterns, not boilerplate.

**Status:** 🟡 Partial — Kotlin internals covered. Platform abstraction patterns needed.

---

## Existing Files Needing Review (Not Just Writing)

These files exist as first drafts from AI generation. They need expert review:

| File | Main review task |
|------|-----------------|
| `references/consulting-methodology.md` | Verify OSC playbook was distilled accurately; add any missing heuristics |
| `references/migration-strategy.md` | Check dual-write pattern against real experience; add war stories |
| `references/solr-concepts-reference.md` | Verify complexity scoring rubric against actual migrations |
| `references/aws-opensearch-service.md` | Verify AWS version numbers and pricing are current |
| `references/scenario-drupal.md` | Verify scenario guidance and decide whether it should stay scenario-specific or be generalized |
| `00-project/product.md` | Update to reflect actual O19s framing, not generic |
| `00-project/tech.md` | Update to reflect actual stack decisions |
| `00-project/structure.md` | Update to reflect actual project structure |

---

## Source Material Still Unread

These `.htm` files were saved directly from the web but haven't been distilled into
`.md` yet. Each is assigned to the chunk it's most relevant to:

| File | Chunk |
|------|-------|
| `community-insights/Migrate from Apache Solr to OpenSearch _ AWS Big Data Blog.htm` | 4 |
| `community-insights/Migration of Solr to Opensearch...Medium.htm` (100M docs) | 4 |
| `community-insights/Schema migration from Solr...BigData Boutique.htm` | 3 |
| `community-insights/Solr to OpenSearch Migration Deep Dive...BigData Boutique.htm` | 3, 4 |
| `opensearch-best-practices/Operational best practices...AWS.htm` | 6 |
| `opensearch-best-practices/Indexing data in Amazon OpenSearch Service.htm` | 6 |
| `opensearch-best-practices/Creating index snapshots...htm` | 6 |
| `opensearch-best-practices/Migrate from Apache Solr to OpenSearch _ AWS Big Data Blog.htm` | 4 |
| `opensearch-fundamentals/Creating a cluster - OpenSearch Documentation.htm` | 6 |
| `opensearch-fundamentals/Policies - OpenSearch Documentation.htm` | 6 |
| `opensearch-fundamentals/Query DSL - OpenSearch Documentation.htm` | 3, 7 |
| `opensearch-fundamentals/Text analysis - OpenSearch Documentation.htm` | 3 |

When working a chunk, read the relevant `.htm` files and extract useful content.
Don't summarize them mechanically — pull the insights that change or enrich the guidance.

---

## Suggested Work Assignments

Rough allocation by expertise area:

| Chunk | Expertise needed | Effort estimate |
|-------|-----------------|-----------------|
| 1 — Strategic Guidance | Senior consultant, client-facing experience | 2–3 hrs |
| 2 — Source Audit | Solr-deep; someone who's audited production clusters | 2–3 hrs |
| 3 — Target Design | OpenSearch/ES design experience | 2–3 hrs |
| 4 — Migration Execution | Has run a migration end-to-end | 3–4 hrs |
| **5 — Relevance Validation** | **O19s core — anyone + relevance background** | **4–6 hrs** |
| 6 — Operations | AWS + ops experience | 2–3 hrs |
| 7 — Platform Integration | Spring Boot/Kotlin primary, or whoever knows SolrJ best | 2–3 hrs |
| Review existing files | Distributed — whoever owns the nearest chunk | 30 min each |

---

## Quality Bar

A chunk is done when:
- [ ] Key Judgements section has 5–10 genuine expert opinions (not just facts)
- [ ] Decision Heuristics section has at least 3 "if X, then Y" patterns
- [ ] Common Mistakes section reflects real things that actually go wrong
- [ ] At least one war story or concrete example grounds the guidance
- [ ] The file can be read in 10 minutes and acted on without needing the sources

A chunk is NOT done when:
- It's a summary of what the sources say (that's not expert knowledge, that's indexing)
- The Key Judgements are neutral / both-sides ("it depends on your situation")
- There are no opinions, only descriptions

---

## Process Suggestion

1. Pick a chunk. Claim it in this doc (add your name/initials to the Status field).
2. Read the source files listed under "Source material to draw from."
3. Skim the relevant `.htm` files for anything the `.md` sources missed.
4. Open a new file at the output path.
5. Write the Key Judgements section first — from memory, without looking at sources.
   This surfaces your actual expert knowledge and prevents the file from becoming a summary.
6. Fill in the rest, drawing on sources for detail.
7. Update the Status field in this doc when done.

---

## Status Summary

| Chunk | File | Status | Owner |
|-------|------|--------|-------|
| — | `consulting-methodology.md` | ✅ Draft exists | — |
| — | `aws-opensearch-service.md` | ✅ Draft exists | — |
| — | `migration-strategy.md` | ✅ Draft exists | — |
| — | `solr-concepts-reference.md` | ✅ Draft exists | — |
| — | `scenario-drupal.md` | ✅ Draft exists | — |
| 1 | `01-strategic-guidance.md` | 🔴 Not started | — |
| 2 | `02-source-audit.md` | 🟡 Partial coverage | — |
| 3 | `03-target-design.md` | 🟡 Partial coverage | — |
| 4 | `04-migration-execution.md` | 🟡 Partial coverage | — |
| 5 | `05-relevance-validation.md` | 🔴 Not started | — |
| 6 | `06-operations.md` | 🟡 Partial coverage | — |
| 7 | `07-platform-integration.md` | 🟡 Partial coverage | — |
