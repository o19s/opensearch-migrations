> I am preparing for solr7->Opensearch migration. I am managing the project with a team of 4 others:                                                                                                                        
1 solr expert,                                                                                                                                                                                                              
1 OS expert                                                                                                                                                                                                                 
1 testing                                                                                                                                                                                                                   
1 sys/network admin  
Can you get me started with enterprise level migration?

● Let me check what's already in the project to build on.

● Explore(Explore migration advisor skill)                                                                                                                                                                                  
⎿  Done (22 tool uses · 42.3k tokens · 1m 7s)                                                                                                     
(ctrl+o to expand)

Recalled 2 memories (ctrl+o to expand)                                                                                                                                                                                    
⎿  1 skill available

● You've got a solid team structure for this. Let me fire up the migration advisor skill — it has a full guided workflow designed for exactly this scenario.

● Skill(solr-to-opensearch-migration)                                                                                                                                                                                       
⎿  Successfully loaded skill

● Great — you've got the ideal team composition for this. Let me walk you through the structured 8-step workflow, starting where it matters most.

Step 0 — Stakeholder Identification (Done)

You're the project lead / search consultant, so I'll tailor this for an architect + PM hybrid perspective: migration strategy, risk assessment, phasing, decision points, and team task assignments.

Recommended Role Mapping Across Phases

Here's how your team maps to the 5-phase migration model:

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

We're now at Step 1 — Schema Acquisition. To kick off the audit, I need to start collecting from your Solr 7 environment. Here's what to gather (assign to your Solr expert):

Priority 1 (Unblocks everything else)

1. Schema — either:                                                                                                                                                                                                       
   - schema.xml (from ZooKeeper configset or server/solr/COLLECTION/conf/)            
   - Or Schema API output: curl http://SOLR_HOST:8983/solr/COLLECTION/schema
2. Collection list — curl http://SOLR_HOST:8983/solr/admin/collections?action=LIST

Priority 2 (Unblocks sizing & infra)

3. Cluster topology — node count, shard count, replica factor, total index size (GB)
4. Traffic profile — rough QPS, indexing rate, peak vs average

Priority 3 (Unblocks query translation)

5. Top 3-5 query patterns — the actual Solr request URLs or solrconfig.xml request handler configs (especially /select with DisMax/eDisMax params)
6. Custom features — any plugins, streaming expressions, custom request handlers, DIH, CDCR?

For the Sys/Network Admin

7. Target platform decision — AWS OpenSearch Service (managed) or self-managed?
8. Network constraints — VPC requirements, auth model, cross-region needs?

  ---                                                                                  
If you have live Solr access, I can inspect it directly with the inspection tools — just give me the Solr URL and a collection name and I'll pull schema, metrics, index stats, and system info automatically.

If you want to see the full picture now before gathering data, I can also show you:
- The migration checklist (all the things you'll need to address)
- The incompatibility catalog (30+ known Solr→OS breaking changes)
- The consulting concerns inventory (200-item discovery matrix)

What do you have available right now? Schema? Live Solr URL? Or would you prefer to start with the checklist/planning artifacts while your Solr expert gathers the technical inputs?

✻ Sautéed for 1m 49s

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
- No Content Owner on the client side — your Solr expert can audit the schema, but someone at the organization needs to own content access. This is the #1 cause of missed milestones.
- No Metadata Owner — who maintains synonyms, stopwords, business rules today? Find that person early. If they're leaving, treat knowledge capture as P0.

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

Score each 1-5. Don't average away a 5 — one severe unknown dominates risk:

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

Want me to also pull the full 200-item discovery question matrix or the intake interview template from the playbook? Those would be useful for your first stakeholder session.               