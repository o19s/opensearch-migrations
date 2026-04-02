● You've got a solid team structure for this. Let me fire up the migration advisor skill — it has a full guided workflow designed for exactly
this scenario.

● Skill(solr-to-opensearch-migration)
⎿  Successfully loaded skill

● Great — you've got the ideal team composition for this. Let me walk you through the structured 8-step workflow, starting where it matters
most.

Step 0 — Stakeholder Identification (Done)

You're the project lead / search consultant, so I'll tailor this for an architect + PM hybrid perspective: migration strategy, risk
assessment, phasing, decision points, and team task assignments.

Recommended Role Mapping Across Phases

┌─────────────────────┬──────────┬──────────────────────┬──────────────────────────────────────────┐
│        Phase        │ Duration │         Lead         │                Supporting                │
├─────────────────────┼──────────┼──────────────────────┼──────────────────────────────────────────┤
│ 1. Audit & Design   │ 2–4 wks  │ You + Solr expert    │ OS expert (target design)                │
├─────────────────────┼──────────┼──────────────────────┼──────────────────────────────────────────┤
│ 2. Build & Validate │ 2–4 wks  │ OS expert            │ Solr expert (baseline), Tester (harness) │
├─────────────────────┼──────────┼──────────────────────┼──────────────────────────────────────────┤
│ 3. Dual-Write       │ 2–6 wks  │ Sys/network admin    │ OS expert, Tester (shadow comparison)    │
├─────────────────────┼──────────┼──────────────────────┼──────────────────────────────────────────┤
│ 4. Gradual Cutover  │ 1–2 wks  │ You (go/no-go gates) │ All hands                                │
├─────────────────────┼──────────┼──────────────────────┼──────────────────────────────────────────┤
│ 5. Cleanup          │ 2–4 wks  │ Sys/network admin    │ You (docs, handoff)                      │
└─────────────────────┴──────────┴──────────────────────┴──────────────────────────────────────────┘

What I Need From You to Proceed

We're now at Step 1 — Schema Acquisition. To kick off the audit, I need to start collecting from your Solr 7 environment. Here's what to
gather (assign to your Solr expert):

Priority 1 (Unblocks everything else)

1. Schema — either:
   - schema.xml (from ZooKeeper configset or server/solr/COLLECTION/conf/)
   - Or Schema API output: curl http://SOLR_HOST:8983/solr/COLLECTION/schema
2. Collection list — curl http://SOLR_HOST:8983/solr/admin/collections?action=LIST

Priority 2 (Unblocks sizing & infra)

3. Cluster topology — node count, shard count, replica factor, total index size (GB)
4. Traffic profile — rough QPS, indexing rate, peak vs average

Priority 3 (Unblocks query translation)

5. Top 3-5 query patterns — the actual Solr request URLs or solrconfig.xml request handler configs (especially /select with DisMax/eDisMax
   params)
6. Custom features — any plugins, streaming expressions, custom request handlers, DIH, CDCR?

For the Sys/Network Admin

7. Target platform decision — AWS OpenSearch Service (managed) or self-managed?
8. Network constraints — VPC requirements, auth model, cross-region needs?

  ---
If you have live Solr access, I can inspect it directly with the inspection tools — just give me the Solr URL and a collection name and I'll
pull schema, metrics, index stats, and system info automatically.

If you want to see the full picture now before gathering data, I can also show you:
- The migration checklist (all the things you'll need to address)
- The incompatibility catalog (30+ known Solr→OS breaking changes)
- The consulting concerns inventory (200-item discovery matrix)

What do you have available right now? Schema? Live Solr URL? Or would you prefer to start with the checklist/planning artifacts while your
Solr expert gathers the technical inputs?



✻ Cogitated for 1m 49s

❯ checklist/planning

● Let me pull the checklist and the key planning references for your team.

Read 4 files (ctrl+o to expand)
⎿  Loaded 1 skill from AIAdvisor/skills/solr-opensearch-migration-advisor/.claude/skills/solr-to-opensearch-migration/.claude/skills

● Here's your planning package, tailored to your 5-person team.

  ---
Your Team → Role Mapping

Your team is a Tier 2-3 team (5 people). Here's how canonical migration roles map:

┌───────────────────────┬─────────────────────────────────────────────────────────┬────────────────────────────────────┐
│        Person         │                      Primary Roles                      │          Secondary Roles           │
├───────────────────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ You (lead/consultant) │ Project Manager, Relevance Strategist, Architect        │ Product Owner, Stakeholder liaison │
├───────────────────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ Solr expert           │ Content Owner, Schema Auditor, Legacy Plugin Specialist │ Metadata Owner                     │
├───────────────────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ OS expert             │ Target Design, Software Engineer, Platform Ops          │ Relevance Engineer                 │
├───────────────────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ Tester                │ QA / Acceptance Lead, Relevance Engineer (measurement)  │ Data Analyst                       │
├───────────────────────┼─────────────────────────────────────────────────────────┼────────────────────────────────────┤
│ Sys/network admin     │ Platform Ops / SRE, Security / Compliance Owner         │ DR Architect                       │
└───────────────────────┴─────────────────────────────────────────────────────────┴────────────────────────────────────┘

Gaps to Watch

Your team has good technical coverage but watch for these:
- No dedicated Product Owner — who defines "better search" from the customer's perspective? You'll need a stakeholder from the client side.
- No Content Owner on the client side — your Solr expert can audit the schema, but someone at the organization needs to own content access.
  This is the #1 cause of missed milestones.
- No Metadata Owner — who maintains synonyms, stopwords, business rules today? Find that person early. If they're leaving, treat knowledge
  capture as P0.

  ---
Phase 1 Checklist: Audit & Design (Weeks 1-4)

Week 1-2: Discovery (assign by role)

Solr Expert — Source Audit:
- Export schema.xml or Schema API JSON for each collection
- Export solrconfig.xml (request handlers, update processors)
- Inventory all collections: name, purpose, doc count, shard/replica topology
- Identify custom plugins, JARs, analyzers
- Document dynamic field patterns and copyField usage
- Catalog synonym files, stopword lists, metadata assets
- Capture atomic update patterns and delete semantics

You — Query & Application Audit:
- Identify top query families from logs (or instrument if no logs exist)
- Catalog request handlers and parser types (DisMax, eDisMax, Lucene)
- Document facets, filters, sorts, boosts, grouping, suggest usage
- Identify all applications/services calling Solr
- Identify client libraries (SolrJ, pysolr, Spring Data Solr, etc.)
- Flag hardcoded query patterns or boosts in application code

Sys/Network Admin — Infrastructure Baseline:
- Document node count, instance types, JVM heap, disk
- Capture current QPS, indexing rate, peak/average ratio
- Document network topology, auth model, security constraints
- Capture latency and throughput baselines
- Assess monitoring and alerting maturity
- Determine target platform (AWS managed vs self-managed)

Tester — Measurement Setup:
- Determine if query logs exist (if not, instrument NOW — need 2-4 weeks of data)
- Begin building candidate gold query set
- Set up relevance testing tooling (Quepid recommended)
- Capture current search quality baseline on Solr
- Define acceptance criteria with stakeholders

Week 3-4: Design

OS Expert — Target Design:
- Convert schema (I can help with this — paste your schema.xml)
- Design OpenSearch index mappings with analyzer chains
- Translate top query patterns to Query DSL
- Size the OpenSearch cluster (rule of thumb: OS data nodes = max(solr_nodes × 2, 3))
- Design auth model (IAM + SigV4 for AWS)

You — Risk Assessment & Planning:
- Score complexity (1-5) across 6 dimensions (schema, query, data movement, app, ops, org readiness)
- Build risk register with named owners
- Identify non-survivor features (streaming expressions, CDCR, DIH, custom similarity)
- Produce source audit summary
- Define migration posture: simple reindex, dual-write, or shadow-first

  ---
Complexity Scoring (Do This Early)

┌───────────────┬───────────────────────────────┬────────────────────────────┬─────────────────────────────────────────┐
│   Dimension   │           1 (Easy)            │        3 (Moderate)        │                5 (Hard)                 │
├───────────────┼───────────────────────────────┼────────────────────────────┼─────────────────────────────────────────┤
│ Schema        │ Standard fields/analyzers     │ Dynamic fields, copyField  │ Custom analyzers, plugins               │
├───────────────┼───────────────────────────────┼────────────────────────────┼─────────────────────────────────────────┤
│ Query         │ Basic keyword + facets        │ Mixed types with boosts    │ Custom parsing, grouping, geo           │
├───────────────┼───────────────────────────────┼────────────────────────────┼─────────────────────────────────────────┤
│ Data movement │ Simple backfill OK            │ Some freshness constraints │ CDC, atomic updates, strict consistency │
├───────────────┼───────────────────────────────┼────────────────────────────┼─────────────────────────────────────────┤
│ Application   │ One app, clean abstraction    │ Multiple services          │ Many apps, hardcoded Solr behavior      │
├───────────────┼───────────────────────────────┼────────────────────────────┼─────────────────────────────────────────┤
│ Operations    │ Small, well-understood        │ Moderate scale, some gaps  │ Large/brittle, weak observability       │
├───────────────┼───────────────────────────────┼────────────────────────────┼─────────────────────────────────────────┤
│ Org readiness │ Named owners, clear approvals │ Some gaps                  │ No content/relevance/cutover owners     │
└───────────────┴───────────────────────────────┴────────────────────────────┴─────────────────────────────────────────┘

  ---
Red Flags That Should Slow You Down

If you hit any two of these, shift into discovery-heavy mode before committing timelines:

- No query logs
- No one can explain ranking behavior
- Undocumented custom JARs
- Schema differs across environments
- "We think the app just sends a few simple queries"
- No named content or acceptance owner
- Migration motivation is purely political

  ---
Prerequisites Gate (Don't Start Build Without These)

- Stakeholders have communicated a measurable definition of success
- Team understands the benefits and reasons for migration
- Clear path to access the content being migrated
- Clear path to search analytics (existing, or plan to instrument)
- Project wiki stood up for documentation

  ---
Next Steps

Once your Solr expert has the schema and configs gathered, bring them here and I'll:

1. Convert the schema to OpenSearch mappings and flag incompatibilities
2. Translate your top queries to Query DSL
3. Run the incompatibility catalog against your specific setup
4. Generate a sizing recommendation from your infrastructure numbers
5. Produce a full migration report with effort estimates

Want me to also pull the full 200-item discovery question matrix or the intake interview template from the playbook? Those would be useful for
your first stakeholder session.



✻ Baked for 48s

❯ discovery question matrix please. will that be saved as a 'sharable' file for convenient access and review?

Read 1 file (ctrl+o to expand)

● That's the full 200-item matrix across 20 risk groups. Let me save it as a shareable file your team can review and work through together.

● That's a comprehensive 200-item matrix. Let me save it as a standalone shareable file your team can use for intake sessions.

Read 1 file, listed 1 directory (ctrl+o to expand)

● Write(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/discovery-question-matrix.md)
⎿  Wrote 346 lines to AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/discovery-question-matrix.md
1 # Discovery Question Matrix: Solr 7 to OpenSearch Migration
2
3 **Project:** Enterprise Solr 7 to OpenSearch Migration
4 **Generated:** 2026-04-02
5 **Purpose:** Structured discovery checklist for intake sessions. 200 items across 20 risk groups.
6
7 **Team:**
8 - Project lead / search consultant (Sean)
9 - Solr expert
10 - OpenSearch expert
… +336 lines (ctrl+o to expand)

● Saved to:

AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/discovery-question-matrix.md

Yes, it's a standalone markdown file your team can share and use independently. I added a few things on top of the raw inventory:

- "How To Use This Document" section with instructions for intake sessions
- Priority guide mapping the 20 groups to your team roles (Solr expert, OS expert, tester, sys admin)
- Status column on every row so you can track Answered / Open / Out-of-scope as you work through sessions
- Session pacing recommendations (which groups to cover in Session 1 vs later)

The file is in the artifacts/ directory alongside any other migration outputs. It's plain markdown so it works in any wiki, GitHub,
Confluence, or just email it around.

Want me to also generate the intake interview template (the 59-question structured discovery format from the playbook)? That's more focused on
running the actual meeting, while this matrix is the comprehensive risk reference.

✻ Sautéed for 10m 57s

❯ yes, and can/should we add some sort of numbering or similar to help someone short on time 'grok' what they see more easily? I imagine the    
artifacts folder will end up with a few dozen artifacts, so making this 'overly obvious' would be a terrific starting point.

● Good call. Let me grab the intake template, and let's establish a naming convention that scales to dozens of files.

● Explore(Find intake template in playbook)
⎿  Done (16 tool uses · 42.4k tokens · 31s)
(ctrl+o to expand)

● Good — there's a rich set of templates to draw from. Let me read the key ones and then create both artifacts with a proper naming convention.

Read 3 files (ctrl+o to expand)

● Now I have all the source material. Let me set up a naming convention that'll stay clear at 50+ files, rename the existing artifact, create
the intake template, and add an index.

Listed 1 directory (ctrl+o to expand)

● Bash(mv /opt/work/OSC/o19s-opensearch-migrations/AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/discovery-question-matrix.md
/opt/work/OSC/o19s-opensea…)
⎿  Done

● Now let me create the intake template and the index file.

● Write(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/P1-02_intake-interview-template.md)
⎿  Wrote 456 lines to AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/P1-02_intake-interview-template.md
1 # P1-02: Intake Interview Template — Solr 7 to OpenSearch Migration
2
3 **Project:** Enterprise Solr 7 to OpenSearch Migration
4 **Generated:** 2026-04-02
5 **Purpose:** Run your first 1-2 stakeholder sessions with this guide. Produces a foundation document with enough detail to begin
6 **Time estimate:** 60-90 minutes per session
7
8 **Team:**
9 - Project lead / search consultant (Sean)
10 - Solr expert
… +446 lines (ctrl+o to expand)


● Now let me create the index file that explains the convention and ties everything together.

● Write(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Wrote 117 lines to AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md
1 # Migration Artifacts Index
2
3 **Project:** Enterprise Solr 7 to OpenSearch Migration
4 **Created:** 2026-04-02
5
6 ---
7
8 ## Naming Convention
9
10 ```
… +107 lines (ctrl+o to expand)

Listed 1 directory (ctrl+o to expand)

● Here's what you've got:

artifacts/
INDEX.md                          — Registry, naming convention, full artifact roadmap
P1-01_discovery-question-matrix.md — 200-item risk matrix (20 groups, status tracking)
P1-02_intake-interview-template.md — 66-question session guide (10 blocks, fill-in-live)

The Naming Convention: P{phase}-{seq}_{description}.md

┌────────┬─────────────────────┬─────────────┐
│ Prefix │        Phase        │    When     │
├────────┼─────────────────────┼─────────────┤
│ P1     │ Audit & Design      │ Weeks 1-4   │
├────────┼─────────────────────┼─────────────┤
│ P2     │ Build & Validate    │ Weeks 5-8   │
├────────┼─────────────────────┼─────────────┤
│ P3     │ Dual-Write & Shadow │ Weeks 9-14  │
├────────┼─────────────────────┼─────────────┤
│ P4     │ Cutover             │ Weeks 15-16 │
├────────┼─────────────────────┼─────────────┤
│ P5     │ Cleanup & Handoff   │ Weeks 17-20 │
└────────┴─────────────────────┴─────────────┘

When someone runs ls on the artifacts folder with 30+ files, they'll see everything sorted by migration phase and sequence — immediately
obvious where in the project each artifact belongs. The INDEX.md has the full expected artifact list (20+ items across all 5 phases) with
checkboxes so you can track what's been produced.

What's different about the intake template vs. the discovery matrix

- P1-01 (discovery matrix) = comprehensive 200-item risk reference. Scan before sessions, star what's relevant, assign by team role.
- P1-02 (intake template) = focused 66-question session guide. Fill in live during meetings. Has answer + confidence columns, output
  checklists, and a session-close section for homework tracking.

Next step: When your Solr expert brings back a schema.xml, I'll generate P1-03_schema-conversion-report.md and
P1-05_incompatibility-register.md automatically.

✻ Cooked for 3m 58s
