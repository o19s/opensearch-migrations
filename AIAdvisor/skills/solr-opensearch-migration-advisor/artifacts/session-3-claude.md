❯ Do you know about the OSC project `chorus`? That is my app (for this demo exercise), can you go by the project's documentation and/or what    
you have been trained on? We installed 3 years ago, and have not updated, so if you have any training, it should be current and relevant (i.e.  
chorus doc from memory is fine for now)

● Yes, I know Chorus well from training. Let me confirm what I recall and check if the migration skill already references it.

Searched for 1 pattern (ctrl+o to expand)

● No existing references in the skill. Here's what I know from training:

Chorus — o19s E-Commerce Search Reference Stack

Repo: querqy/chorus (originally o19s/chorus)

Chorus is a Docker Compose-based reference implementation for e-commerce search. It bundles a full search stack to demonstrate relevance
engineering best practices. Installed ~2023, you'd be on a version with:

Stack Components

- Solr 8.x (SolrCloud mode, with ZooKeeper)
- Quepid — relevance testing / judgment management
- SMUI (Search Management UI) — synonym and ranking rule management
- Blacklight or a lightweight storefront UI
- Data pipeline — loads the Icecat/Best Buy electronics product dataset (~20K-50K products)

Search Configuration (the migration-relevant parts)

- eDisMax query parser as the primary search handler
- Querqy — query rewriting library (common rewrite rules, synonyms, boosts, filters)
- Custom configset with:
    - Text fields with custom analyzer chains (product names, descriptions, specs)
    - Facet fields on brand, category, price, etc.
    - Dynamic fields for product attributes
    - Synonym files managed through SMUI
    - copyField directives to catch-all fields
- Product data — electronics: TVs, laptops, cameras, etc. with rich attributes (specs, features, images, categories)

Key eDisMax Config (typical Chorus /select handler)

- qf — weighted fields: title^10 description^3 features^2 attr_*
- pf — phrase boosting on title
- mm — minimum-should-match (often 75% or 2<75%)
- Facets on category, brand, price range
- Filter queries for in-stock, category navigation

What Makes This a Good Migration Exercise

┌───────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
│          Characteristic           │                        Migration relevance                        │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ eDisMax with qf/pf/mm             │ Core query translation challenge (DisMax → Query DSL multi_match) │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ Querqy rewrite rules              │ Need equivalent in OpenSearch (Querqy has an OS plugin)           │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ SMUI synonym management           │ Governance/tooling question — does SMUI support OS?               │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ Custom analyzer chains            │ Tokenizer/filter mapping exercise                                 │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ Faceted navigation                │ Solr facets → OpenSearch aggregations                             │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ Dynamic fields for attributes     │ → dynamic_templates in OS                                         │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ SolrCloud + ZooKeeper             │ → OpenSearch's embedded Raft (ZK goes away)                       │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ Quepid                            │ Already supports OpenSearch — relevance measurement survives      │
├───────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ ~20-50K docs, moderate complexity │ Complexity score ~2-3/5 — realistic but not overwhelming          │
└───────────────────────────────────┴───────────────────────────────────────────────────────────────────┘

What I'd Flag for Your Demo

1. Querqy is the biggest question mark. There is a Querqy OpenSearch plugin, but version compatibility with your target OS version needs
   verification.
2. SMUI integration — if you're using SMUI to manage synonyms/rules, the toolchain migration matters as much as the engine.
3. Scoring shift — Chorus is tuned with eDisMax boosts against TF-IDF (Solr 8 default). Moving to BM25 will shift top-10 rankings for product
   searches. Your team's tester should baseline with Quepid before touching anything.
4. The dataset is perfect for judgment-based testing — electronics products have clear relevance signals (search "4K TV" → expect TVs, not
   cables).

  ---
Does this match your Chorus install? A few things I'd want to confirm:

- Solr version — 8.x as I expect, or did you end up on 9.x?
- Querqy — are you using it, or just vanilla eDisMax?
- SMUI — active, or did you skip that component?

Once confirmed, I can start filling in migration artifacts with real Chorus-specific details rather than generic placeholders.

✻ Churned for 48s

❯ yes, solr 8, love querqy and smui both. they will be important to migrate or replace.

● Good — that crystallizes the migration scope. Querqy + SMUI are load-bearing components, not optional add-ons. Let me save this project
context and then update the artifacts with Chorus-specific details.

Recalled 2 memories, wrote 2 memories (ctrl+o to expand)

● Now here's what Chorus-specific context means for your migration plan:

Three Migration Tracks (Not Just One)

Most Solr→OS migrations are about the engine. Yours has three interdependent systems:

┌───────────┬───────────────────────────────────────────────┬─────────────────────────┬───────────────────────────────────────────────────┐
│   Track   │                     What                      │          Owner          │                       Risk                        │
├───────────┼───────────────────────────────────────────────┼─────────────────────────┼───────────────────────────────────────────────────┤
│ 1. Engine │ Solr 8 SolrCloud → OpenSearch                 │ OS expert + Solr expert │ Medium — well-understood path                     │
├───────────┼───────────────────────────────────────────────┼─────────────────────────┼───────────────────────────────────────────────────┤
│ 2. Querqy │ Querqy Solr plugin → Querqy OpenSearch plugin │ Solr expert + OS expert │ High — plugin version compat is the unknown       │
├───────────┼───────────────────────────────────────────────┼─────────────────────────┼───────────────────────────────────────────────────┤
│ 3. SMUI   │ SMUI → SMUI-on-OS or replacement              │ You + OS expert         │ High — SMUI's OS support maturity is the question │
└───────────┴───────────────────────────────────────────────┴─────────────────────────┴───────────────────────────────────────────────────┘

These can't be migrated independently — Querqy rules feed from SMUI, and the engine executes them. If Querqy's OS plugin doesn't support your
rule set, SMUI's output is orphaned.

Querqy: What Your Team Needs To Verify

The Querqy OpenSearch plugin exists (querqy/querqy-opensearch), but:

1. Version matrix — which OpenSearch versions does it support? Your target OS version must be on the list.
2. Rule parity — do all your Querqy rule types (synonyms, boosts, filters, decorations) work identically on OS? Most do, but edge cases exist.
3. Rewriter compatibility — if you're using CommonRulesRewriter, ReplaceRewriter, or WordBreakRewriter, verify each one.
4. Performance — Querqy on Solr is mature; Querqy on OS is newer. Benchmark with your rule set size.

Assign to: Solr expert (extracts current rules) + OS expert (tests on target)

SMUI: The Governance Question

SMUI manages Querqy rules through a UI. Two paths:

┌───────────────────────────────────────────────────┬─────────────────────────────────┬──────────────────────────────────────────────────┐
│                      Option                       │              Pros               │                       Cons                       │
├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
│ SMUI with OS backend                              │ Familiar workflow, no           │ SMUI's OS support needs verification; may lag    │
│                                                   │ retraining                      │                                                  │
├───────────────────────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────┤
│ Replace with OpenSearch Dashboards + custom       │ Native OS ecosystem             │ Rebuilds the rule management workflow from       │
│ tooling                                           │                                 │ scratch                                          │
└───────────────────────────────────────────────────┴─────────────────────────────────┴──────────────────────────────────────────────────┘

Recommendation: Verify SMUI's OS compatibility first. If it works, migrate it. If not, that's a significant scope addition — flag it early.

Updated Phase 1 Priorities

Given Chorus, here's what your Solr expert should pull first:

1. Querqy rules export — the full rules file(s) from SMUI/Querqy config
2. solrconfig.xml — the /select handler with eDisMax params (qf, pf, mm, boosts)
3. schema.xml — the Chorus configset
4. SMUI rule count — how many rules are managed? (synonyms, boosts, filters, deletes)
5. Querqy rewriter config — which rewriters are active and how they chain

If you can get me the schema.xml and solrconfig.xml from your Chorus install, I'll generate P1-03 and P1-04 with real field names, real query
patterns, and Querqy-aware incompatibility flags.

Want to pull those configs now, or should we map out the Querqy/SMUI investigation track in more detail first?

✻ Cooked for 53s

❯ can you take your best guess on all 5? Assume we stuck close to the original install and all 'base assumptions' are good for now. We will     
update the exact information (confirming or overwriting your guesses).

● I'll generate a best-guess source audit based on my training knowledge of the Chorus stack, with every assumption clearly marked so your team
can confirm or correct. Let me also pull the Chorus GitHub docs to cross-check.

● Agent(Fetch Chorus GitHub repo details)
⎿  Done (16 tool uses · 35.6k tokens · 3m 26s)
(ctrl+o to expand)

● Got detailed data from the Chorus repo. The current repo is actually on Solr 9.1.1, but since you installed ~2023 and confirmed Solr 8, I'll
adjust for that vintage (no vector fields, older Querqy/SMUI versions). Let me build the source audit.

● Write(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/P1-03_chorus-source-audit.md)
⎿  Wrote 411 lines to AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/P1-03_chorus-source-audit.md
1 # P1-03: Chorus Source Configuration Audit
2
3 **Project:** Enterprise Solr 8 (Chorus) to OpenSearch Migration
4 **Generated:** 2026-04-02
5 **Status:** ASSUMED — awaiting team confirmation
6 **Source:** Reconstructed from Chorus GitHub repo (querqy/chorus), adjusted for ~2023 Solr 8.x install
7
8 > **Every item marked `[ASSUMED]` needs confirmation or correction by the team.**
9 > Search this doc for `[ASSUMED]` to find all guesses. There are approximately 30.
10 >
… +401 lines (ctrl+o to expand)

● Now update the INDEX.

Read 1 file (ctrl+o to expand)

● Update(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Added 1 line, removed 1 line
1  # Migration Artifacts Index
2  
3 -**Project:** Enterprise Solr 7 to OpenSearch Migration                                                                          
3 +**Project:** Enterprise Solr 8 (Chorus) to OpenSearch Migration                                                                 
4  **Created:** 2026-04-02
5  
6  ---

● Update(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Added 1 line
43  |------|-------------|----------|--------|
44  | [P1-01_discovery-question-matrix.md](P1-01_discovery-question-matrix.md) | 200-item risk discovery matrix across 20 groups. U
se as comprehensive reference during intake. | All team | Ready |
45  | [P1-02_intake-interview-template.md](P1-02_intake-interview-template.md) | 66-question structured interview guide for stakeho
lder sessions. Fill in live during meetings. | Project lead | Ready |
46 +| [P1-03_chorus-source-audit.md](P1-03_chorus-source-audit.md) | Best-guess source config audit: schema, solrconfig, Querqy, SM
+UI, dataset. ~30 assumptions to verify. | Solr expert + OS expert | Assumed — needs verification |                             
47  
48  ### P2: Build & Validate
49

● Update(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Added 4 lines, removed 4 lines
78  ### P1: Audit & Design
79  - [x] P1-01 — Discovery question matrix (200-item risk reference)
80  - [x] P1-02 — Intake interview template (66-question session guide)
81 -- [ ] P1-03 — Schema conversion report (after schema.xml is provided)                                                          
82 -- [ ] P1-04 — Query translation report (after top queries are provided)                                                        
83 -- [ ] P1-05 — Incompatibility register (auto-generated from schema + query analysis)                                           
84 -- [ ] P1-06 — Complexity scorecard (6-dimension scoring)                                                                       
81 +- [x] P1-03 — Chorus source audit (schema, solrconfig, Querqy, SMUI, dataset — assumed, awaiting verification)                 
82 +- [ ] P1-04 — Query translation report (after top queries are confirmed)                                                       
83 +- [ ] P1-05 — Incompatibility register (preliminary in P1-03 §8, full version after verification)                              
84 +- [ ] P1-06 — Complexity scorecard (preliminary in P1-03 §7, full version after verification)                                  
85  - [ ] P1-07 — Infrastructure sizing recommendation
86  - [ ] P1-08 — Client integration inventory
87  - [ ] P1-09 — Risk register

● Update(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Added 4 lines, removed 3 lines
113  ## Quick Start
114  
115  **New to this project?** Read these in order:
116 -1. `P1-01` — Scan the 20 risk groups to understand what we're watching for                                                    
117 -2. `P1-02` — Use this to run your first stakeholder session                                                                   
118 -3. `INDEX.md` — Come back here to find anything else                                                                          
116 +1. `P1-03` — Start here: what we think we're migrating (Chorus source audit)                                                  
117 +2. `P1-01` — Scan the 20 risk groups to understand what we're watching for                                                    
118 +3. `P1-02` — Use this to run your first stakeholder session                                                                   
119 +4. `INDEX.md` — Come back here to find anything else

● Done. Here's what you've got:

artifacts/
INDEX.md                              — Updated registry + quick start
P1-01_discovery-question-matrix.md    — 200-item risk matrix
P1-02_intake-interview-template.md    — 66-question session guide
P1-03_chorus-source-audit.md          — NEW: full source config audit

P1-03 Summary: What I Assumed

The source audit covers all 5 items with ~30 [ASSUMED] markers your team can grep for:

1. Schema (~20 explicit fields, 5 dynamic patterns, 14 copyField directives)

- text_stemmed_en as primary text type (StandardTokenizer → LowerCase → EnglishMinimalStem)
- Dual-field pattern: brand (searchable) + filter_brand (facetable keyword)
- Dynamic attr_t_* → filter_t* + search_attributes catch-all
- No vector fields (those are post-2023 additions to Chorus)

2. solrconfig.xml (/select, /blacklight, /suggest)

- defType=querqy (not edismax) — Querqy wraps eDisMax
- qf: id, name, title, product_type, short_description, ean, search_attributes
- ParamSets for algorithm switching (production vs. prelive vs. vanilla eDisMax)

3. Querqy (3 active rewriters)

- replace → query normalization/spelling
- common_rules → synonyms, boosts, filters, deletes
- regex_screen_protectors → regex-based filtering
- Chain order: replace → common_rules → regex

4. SMUI (~90-245 rules estimated)

- Deploys rules.txt + replace-rules.txt to ZooKeeper
- Prelive staging rules for preview before production deploy
- Suggested fields: product_type, title, brand

5. Querqy rewriter config

- QuerqyDismaxQParserPlugin + QuerqyQueryComponent
- skipUnknownRewriters=true
- Info logging via ResponseSink for rule debugging

Top 3 Things That Surprised Me

1. The current Chorus repo is on Solr 9.1.1 with vector embeddings and kNN search. Your Solr 8 install is significantly simpler — which is
   actually good for migration.
2. Chorus has a 125-query judgment set with 3 judges already baked in. That's a massive head start for relevance baseline work — your tester
   should find Broad_Query_Set_rated.csv and load it into Quepid immediately.
3. The regex_screen_protectors rewriter — this is a Chorus-specific demo rule that may or may not be in your install. Low risk either way, but
   the querqy-opensearch plugin's regex support should be verified.

The verification commands are at the bottom of the audit (Section 9) — ready for your Solr expert to run against the live Chorus instance.
Want to proceed with anything else, or let the team verify first?


--- 
let's map out the Querqy/SMUI investigation track in more detail

● 2 agents finished (ctrl+o to expand)
├─ Research querqy-opensearch compatibility · 11 tool uses · 18.3k tokens
│  ⎿  Done
└─ Research SMUI OpenSearch support · 28 tool uses · 34.9k tokens
⎿  Done

● Excellent research. This is really clear now — both are viable but need specific integration work. Let me build the investigation track
artifact.

● Write(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/P1-04_querqy-smui-migration-track.md)
⎿  Wrote 361 lines to AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/P1-04_querqy-smui-migration-track.md
1 # P1-04: Querqy & SMUI Migration Track
2
3 **Project:** Enterprise Solr 8 (Chorus) to OpenSearch Migration
4 **Generated:** 2026-04-02
5 **Status:** Investigation plan — research complete, execution pending
6 **Critical path:** Yes — Querqy plugin availability gates the entire migration
7
8 ---
9
10 ## Executive Summary
… +351 lines (ctrl+o to expand)

● Update(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Added 1 line
44  | [P1-01_discovery-question-matrix.md](P1-01_discovery-question-matrix.md) | 200-item risk discovery matrix across 20 groups. U
se as comprehensive reference during intake. | All team | Ready |
45  | [P1-02_intake-interview-template.md](P1-02_intake-interview-template.md) | 66-question structured interview guide for stakeho
lder sessions. Fill in live during meetings. | Project lead | Ready |
46  | [P1-03_chorus-source-audit.md](P1-03_chorus-source-audit.md) | Best-guess source config audit: schema, solrconfig, Querqy, SM
UI, dataset. ~30 assumptions to verify. | Solr expert + OS expert | Assumed — needs verification |
47 +| [P1-04_querqy-smui-migration-track.md](P1-04_querqy-smui-migration-track.md) | Querqy + SMUI investigation: plugin compat, SM
+UI deploy script, AWS constraints, decision tree, 15-task execution plan. | OS expert + Sys admin | Ready |                    
48  
49  ### P2: Build & Validate
50

● Update(AIAdvisor/skills/solr-opensearch-migration-advisor/artifacts/INDEX.md)
⎿  Added 2 lines, removed 1 line
80  - [x] P1-01 — Discovery question matrix (200-item risk reference)
81  - [x] P1-02 — Intake interview template (66-question session guide)
82  - [x] P1-03 — Chorus source audit (schema, solrconfig, Querqy, SMUI, dataset — assumed, awaiting verification)
83 -- [ ] P1-04 — Query translation report (after top queries are confirmed)                                                       
83 +- [x] P1-04 — Querqy + SMUI migration track (plugin compat, deploy script, AWS decision tree, execution plan)                  
84 +- [ ] P1-04b — Query translation report (after top queries are confirmed)                                                      
85  - [ ] P1-05 — Incompatibility register (preliminary in P1-03 §8, full version after verification)
86  - [ ] P1-06 — Complexity scorecard (preliminary in P1-03 §7, full version after verification)
87  - [ ] P1-07 — Infrastructure sizing recommendation

● Here's what the research found and what your team needs to do:

The Good News

- querqy-opensearch exists and is actively maintained — last release was 2 days ago (2026-03-31)
- SMUI's rule format is engine-agnostic — same rules.txt works for Solr and OpenSearch
- CommonRulesRewriter + ReplaceRewriter are both supported — your two primary rewriters migrate cleanly
- The SMUI→OS integration is a ~50-line bash script, not a rewrite

The Three Decisions That Gate Everything

1. Target OpenSearch Version (OS expert + Sys admin)

Only 3 plugin releases exist: OS 2.3, 2.19, and 3.1. No intermediate versions. You must target one of these.

2. AWS Managed vs. Self-Managed (Sys admin)

AWS managed OpenSearch may block custom plugin installation. If it does:
- Self-managed on EC2/EKS = full plugin control, more ops work
- Redesign without Querqy = native OS query features only — major scope increase, flag immediately if this is the path

3. Regex Rewriter (OS expert)

The regex_screen_protectors rewriter isn't confirmed in querqy-opensearch. Low risk — easy fallback to CommonRules.

What's in P1-04

The artifact has 6 sections:

┌────────────────────────┬────────────────────────────────────────────────────────────────────────────────┐
│        Section         │                                 What it covers                                 │
├────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 1. querqy-opensearch   │ Version matrix, supported rewriters, rule deployment API (REST, not ZK)        │
├────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 2. SMUI                │ Deploy architecture diagram, custom script code (ready to use), config changes │
├────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 3. AWS constraints     │ Decision tree: managed → self-managed → no-Querqy paths                        │
├────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 4. Regex investigation │ Check steps + fallback options                                                 │
├────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 5. Migration sequence  │ 15 tasks across 3 phases, assigned by role                                     │
├────────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ 6. Risk register       │ 7 Querqy/SMUI-specific risks with mitigations                                  │
└────────────────────────┴────────────────────────────────────────────────────────────────────────────────┘

The first thing to unblock: your sys admin checking whether AWS OpenSearch Service supports custom query parser plugins. That single answer
determines whether you're on the happy path (managed + Querqy) or need to make a harder choice.

