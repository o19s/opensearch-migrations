# Discovery Question Matrix: Solr 7 to OpenSearch Migration

**Project:** Enterprise Solr 7 to OpenSearch Migration
**Generated:** 2026-04-02
**Purpose:** Structured discovery checklist for intake sessions. 200 items across 20 risk groups.

**Team:**
- Project lead / search consultant (Sean)
- Solr expert
- OpenSearch expert
- Testing specialist
- Sys/network admin

---

## How To Use This Document

1. **Before the first stakeholder session:** Scan all 20 groups. Star the ones most relevant to your organization.
2. **During intake:** Use the "Why it matters" column to explain *why* you're asking. Stakeholders respond better when they understand the risk.
3. **After intake:** Mark each item as Answered / Open / Out-of-scope. Carry open items forward across sessions.
4. **Assignment:** Use the "Suggested owner" column to route questions to the right team member.

### Priority Guide

- **Groups 1-2 (Business & Scope):** Cover in Session 1 with stakeholders
- **Groups 3-5 (Product, Relevance, Parity):** Cover with search/product owners
- **Groups 6-7 (Data & Ingestion):** Assign to Solr expert + sys admin
- **Groups 8-10 (Tenancy, Cutover, Observability):** Assign to sys admin + OS expert
- **Groups 11-14 (Security, Service, Version, Cost):** Sys admin leads, all review
- **Groups 15-16 (Performance, UX):** Tester + OS expert
- **Groups 17-18 (Org, Testing):** Project lead drives
- **Groups 19-20 (DR, Gotchas):** Sys admin + OS expert

---

## 1) Business Intent and Migration Posture

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 1. | Primary business driver (cost, scale, etc.) | Determines where to prioritize effort (e.g., latency vs. cost). | Optimizing for the wrong KPI, leading to project "failure" despite technical success. | |
| 2. | Nature of move (Like-for-like vs. Reset) | Affects how much legacy behavior we are allowed to break. | Over-engineering a simple move or under-engineering a needed modernization. | |
| 3. | Definition of "Success" owner | Prevents "shifting goalposts" during the final cutover phase. | Late-stage rejection by a stakeholder who wasn't consulted on the criteria. | |
| 4. | Tolerated business regression | Sets the requirement for dual-run and shadow traffic intensity. | Business outage or severe revenue drop if "zero-regression" was assumed but not built. | |
| 5. | Target lifespan (Bridge vs. 3-year Platform) | Influences technical debt tolerance and automation level. | Throwing away high-effort automation on a bridge, or building a fragile long-term core. | |
| 6. | Stakeholder visibility expectations | Determines if we need "flashy" UX improvements early on. | Stakeholders lose interest or funding if they don't see "better" results, only "same" results. | |
| 7. | Truly valuable vs. merely familiar behavior | Identifies which "quirks" must be preserved at high cost. | Removing a "bug" that users actually relied on for their workflow. | |
| 8. | Political vs. Technical pain points | Migration won't fix political silos or bad data governance. | Engine change fails to improve search because the real bottleneck was organizational. | |
| 9. | Optimization goal: Speed vs. Correctness | Determines testing rigor and rollout duration. | Rushed cutover leads to silent data corruption or relevance drift. | |
| 10. | Final destination posture (AWS OS vs. Cloud-agnostic) | Influences use of AWS-proprietary features (SigV4, Serverless). | Unintended vendor lock-in or missing out on managed service efficiencies. | |

## 2) Scope and Boundary Definition

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 11. | Feature scope (Search, Autocomplete, ML, etc.) | Prevents scope creep and helps size the target domain. | Half-migrated product where search works but autocomplete is broken/stale. | |
| 12. | Search role (Standalone vs. Pipeline-embedded) | Determines if we need to migrate the "feeder" systems too. | Inability to test search in isolation; breakages in upstream enrichment. | |
| 13. | Tenant model (Single vs. Multi-tenant) | Drastically changes security and scaling architecture. | Noisy neighbor problems or catastrophic data leakage between customers. | |
| 14. | Hidden dependencies (Reporting, Admin, SEO) | These "shadow" consumers often rely on Solr-specific XML/CSV formats. | Broken internal dashboards or SEO pages that no one knew were search-powered. | |
| 15. | Undocumented query behavior consumers | Some apps might rely on specific parser edge cases (e.g., local params). | Unexpected "Zero Results" for specific but critical user segments. | |
| 16. | Solr-as-a-DB usage | Batch jobs relying on `rows=1000000` will fail in OpenSearch. | Critical business reports stop functioning due to engine-level protection limits. | |
| 17. | Shadow search stacks | There might be another OS/ES cluster already in use. | Divergent search experiences and wasted infrastructure spend. | |
| 18. | Governance of rules (Synonyms, Boosts) | Determines where the "source of truth" for relevance lives. | "Lost" business logic that was manually applied to the old engine but never recorded. | |
| 19. | Operational ownership transfer | Defines who handles the pager after cutover. | Infrastructure is ready but no one knows how to tune it or fix it when it breaks. | |
| 20. | Replacement unit (Cluster vs. Operating Model) | Are we fixing the engine or the way we *do* search? | Replacing a "messy" Solr cluster with a "messy" OpenSearch domain. | |

## 3) Product Semantics and Search Behavior

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 21. | Identicality requirements (User POV) | Defines the "Parity" threshold. | Endless "it looks different" bugs that are actually just engine differences. | |
| 22. | Acceptable differences (Quality trade-offs) | Allows us to move to BM25 even if top-1 results shift. | Stalling the project trying to match a legacy ranking that was actually sub-optimal. | |
| 23. | Determinism vs. Heuristics | Solr results can feel more "stable" than distributed OS scores. | User complaints about results "shifting" between paginated clicks. | |
| 24. | Trained legacy quirks | Users might have learned to use specific "Solr-isms" in the search box. | Power users feel the new system is "broken" because their tricks no longer work. | |
| 25. | Narrow query parser dependencies | eDisMax and Query DSL handle boolean logic differently. | Complex queries (AND/OR/NOT) returning wildly different result counts. | |
| 26. | Zero-results strategy | Is this a search error or a merchandising opportunity? | Hard-coding Solr-specific "no result" logic into the app. | |
| 27. | Browse vs. Retrieval priority | Influences facet performance vs. keyword accuracy. | Fast keyword search but sluggish "category browse" pages. | |
| 28. | Relevance target (Revenue vs. Text) | Ecommerce needs revenue-aware ranking, not just BM25. | High relevance but lower conversion/revenue after migration. | |
| 29. | Trust/Explainability requirements | Can you explain to a stakeholder *why* a result is #1? | "Black box" search that stakeholders don't trust to handle business boosts. | |
| 30. | Scoring delta awareness | Stakeholders need to know that scores *will* change. | Panic during QA when scores don't match 1:1 with the legacy system. | |

## 4) Relevance Governance

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 31. | Ranking authority | Prevents conflicting boost rules. | "Ranking wars" where one team's boost breaks another's goal. | |
| 32. | Documented relevance strategy | Provides a baseline for "correctness." | Decisions made based on the loudest stakeholder's opinion. | |
| 33. | Boost governance (Artifact vs. Ad-hoc) | Ensures ranking changes are reproducible and auditable. | "Magic numbers" in code that no one understands or dares to change. | |
| 34. | "Better" vs "Different" distinction | Helps avoid "relevance paralysis" where any change is seen as a bug. | Stalling a superior engine because it doesn't match a legacy flaw. | |
| 35. | Agreed evaluation set (Gold queries) | Provides objective proof of migration success. | Subjective "vibes-based" QA that never reaches a "done" state. | |
| 36. | Optimization metric (CTR, Recall, etc.) | Aligns engineering effort with business value. | Perfecting text recall while the business actually needs conversion. | |
| 37. | Post-migration ranking drift | Ensures the engine stays tuned as content changes. | Relevance "rot" where search quality slowly degrades after go-live. | |
| 38. | Rules approval process (Synonyms, Bury) | Prevents "accidental" relevance regressions. | A single bad synonym crashing precision for a high-volume query. | |
| 39. | Relevance ownership model | Determines if search is a project or a product. | Search becomes "unowned" once the migration project ends. | |
| 40. | Ranking folklore reduction | Opportunity to clean up "haunted" legacy logic. | Carrying over 10 years of "just in case" boosts that no longer work. | |

## 5) Functional Parity Illusions

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 41. | Implementation-shaped features | Some "requirements" are just how Solr happened to work. | Wasting months rebuilding a Solr quirk that has no business value. | |
| 42. | Parity as a stall tactic | Avoids making hard product decisions about search. | Carrying over "broken" product logic just to meet a "parity" goal. | |
| 43. | Analyzer chain dependencies | Complex Solr analysis might not map 1:1 to OS plugins. | Subtle text matching failures (e.g., stemming, compounding). | |
| 44. | UI-Response coupling | App might expect Solr's specific XML/JSON structure. | Frontend breakage even if the engine is returning the right data. | |
| 45. | "Lucene lineage" risk assumption | Similarity doesn't mean equality in high-level APIs. | Underestimating the effort needed to rewrite the query layer. | |
| 46. | Equivalent-on-paper features | Features like "Grouping" or "Faceting" differ in performance/edge cases. | Performance collapse in production because "it worked in the demo." | |
| 47. | Implicit commit/refresh semantics | Solr and OS handle visibility of new data differently. | Users seeing "stale" results or the app failing its own tests. | |
| 48. | "Same query, same result" realism | Scoring differences make literal 1:1 parity impossible. | Failing a contract because of a 0.001 difference in BM25 score. | |
| 49. | Deliberate non-survivors | Identifies what *shouldn't* be migrated. | Migrating technical debt and legacy baggage to a clean new cluster. | |
| 50. | Parity gaps as redesign | Reframes technical gaps as UX improvements. | Treating an engine improvement as a "defect" because it's different. | |

## 6) Data Ownership and Document Lifecycle

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 51. | Canonical document ownership | Defines who to blame when data is wrong. | Fixing data in search while the source remains broken. | |
| 52. | Indexing trigger (Event vs Batch) | Determines result freshness and system load. | Stale search results or overloading the engine with batch jobs. | |
| 53. | Source disagreement resolution | Prevents data corruption from conflicting inputs. | "Flickering" results where doc attributes jump between states. | |
| 54. | Delete reliability | Ensures "right to be forgotten" and catalog hygiene. | Users seeing "Out of Stock" or deleted items in search results. | |
| 55. | Partial update governance | Controls how field-level changes are merged. | Race conditions where a fast update overwrites a slow one. | |
| 56. | Multiple indexing paths | Identifies potential for race conditions. | Index corruption caused by competing ingestion pipelines. | |
| 57. | Reindexability from source | Critical for disaster recovery and schema changes. | Permanent data loss if the search engine is the only copy. | |
| 58. | Index rebuild capability | Ensures you can move to a new cluster without Solr. | Vendor lock-in to the current engine's internal state. | |
| 59. | Enrichment reproducibility | Ensures explainability of why a doc looks a certain way. | "Mystery fields" that no one knows how to recalculate. | |
| 60. | Stable document identity | Ensures analytics and bookmarks stay valid. | Broken links and lost user history during the cutover. | |

## 7) Change Data Capture and Ingestion Architecture

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 61. | Ingestion-App coupling | Determines if you can update search without a full deploy. | Search is "frozen" because the app team is busy with other features. | |
| 62. | Indexing ecosystem scope | You're migrating the *pipeline*, not just the engine. | A fast new engine fed by a slow, legacy pipeline. | |
| 63. | Transition strategy (Dual-write/Replay) | Ensures data consistency during the move. | Large data gaps or "missing days" during the cutover window. | |
| 64. | Update ordering model | Prevents "stale-overwrites-fresh" bugs. | Search showing old prices/status because updates arrived out of order. | |
| 65. | Ingestion idempotency | Ensures retries don't double-count or corrupt docs. | Index bloat or incorrect counters after a retry. | |
| 66. | Backfill-Live traffic interaction | Ensures reindexing doesn't crash the production site. | Site outage during a routine catalog update. | |
| 67. | Enrichment failure policy | Defines if a "partially correct" doc is better than no doc. | Massive catalog drops because one external API was down. | |
| 68. | Pipeline error granularity | Helps diagnose where data went missing. | "Search is broken" tickets that take days to trace to an upstream bug. | |
| 69. | Cutover lag reasoning | Sets expectations for "eventual consistency" duration. | Panic during cutover because "docs aren't showing up yet." | |
| 70. | Hidden manual correction workflows | Identifies undocumented "emergency fix" scripts. | Lost ability to fix production data issues after the move. | |

## 8) Tenant and Domain Strategy

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 71. | Unit of isolation | Determines security and performance boundaries. | Security breach or "noisy neighbor" crashing the whole system. | |
| 72. | Infrastructure sharing | Optimizes cost vs. customizability. | One small tenant's tuning needs breaking the main production cluster. | |
| 73. | Isolation hardness | Sets the requirement for VPC/IAM vs. app-level filters. | Accidental data leakage between competitors. | |
| 74. | Workload homogeneity | Different workloads (log vs search) need different tuning. | Search latency spikes because of a heavy background analytic query. | |
| 75. | Domain count strategy | Multiple domains can reduce blast radius. | A single config error taking down search across the entire global enterprise. | |
| 76. | Noisy neighbor effects | Prevents one heavy user from starving others. | Unpredictable p99 latency for critical users. | |
| 77. | Governance fights | Shared schema/ranking creates political conflict. | Project stall because teams can't agree on a shared field type. | |
| 78. | Contractual data separation | Legal requirements for where data "lives." | Compliance failure and legal liability. | |
| 79. | Blast radius impact | Defines the "Worst Case Scenario." | Total business blackout from a single regional outage. | |
| 80. | Cost vs. Coupling trade-off | Consolidation saves money but increases risk. | Spending $1M to save $10k in infra costs. | |

## 9) Availability, Cutover, and Rollback

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 81. | "Zero Downtime" definition | Aligns expectations on what "success" looks like. | Stakeholders angry about "stale data" when you promised "up." | |
| 82. | Cutover reversibility | The "Safety Net" for the go-live. | Trapped on a broken system with no way to go back to Solr. | |
| 83. | Parallel run duration | Determines the budget for "Dual Run." | Running out of money before the new system is fully trusted. | |
| 84. | Traffic routing granularity | Allows for "Canary" rollouts. | 100% failure on day one instead of 1% manageable failure. | |
| 85. | Realism of rollback plan | Prevents "DNS hope" as a strategy. | Rollback fails because the data had already diverged too far. | |
| 86. | Data divergence limit | Defines the "Point of No Return." | Attempting a rollback that causes massive data corruption. | |
| 87. | Cutover state management | Defines how to handle writes during the flip. | Duplicate documents or missing orders during the DNS transition. | |
| 88. | Silent failure detection | Catches quality issues that don't throw 500 errors. | The site is "up" but search is returning gibberish for 24 hours. | |
| 89. | Rollback vs. Forward-fix | Sets the threshold for "hitting the abort button." | Wasting hours fixing a "fire" that should have been rolled back. | |
| 90. | Relevance rollback difficulty | Infrastructure is easy; ranking state is hard. | Rolling back to "stable" infra but "broken" search results. | |

## 10) Observability and Truth Detection

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 91. | Health proof metrics | Defines what "Green" actually means. | Dashboards say "Green" while users can't find products. | |
| 92. | Priority KPIs | Aligns monitoring with business outcomes. | Optimizing for 10ms latency when conversion is at 0%. | |
| 93. | Content vs. Engine issue separation | Helps route bugs to the right team (Data vs Search). | Search team wasting weeks fixing "bad results" caused by bad data. | |
| 94. | Query logging quality | Essential for replaying and comparing behavior. | Inability to prove *why* the old system was "better" for a specific user. | |
| 95. | Canary queries | Automated checks for critical business paths. | The "Black Friday" query breaks and no one notices until revenue drops. | |
| 96. | Silent corruption detection | Catches facet/autocomplete rot. | Users seeing "Category (0)" even when products exist. | |
| 97. | Outcome-aligned dashboards | Measures product value, not just CPU. | Measuring "Queries per second" instead of "Successful searches." | |
| 98. | Evidence-based incident review | Ensures post-mortems lead to fixes, not blame. | Fixing the same "search bug" three times because root cause was missed. | |
| 99. | Rank explainability requirements | Essential for debugging "Why is this #1?" | Business owners losing trust because "the computer just said so." | |
| 100. | Support self-service | Reduces the load on the search engineering team. | Search engineers spending 50% of their time answering "Where is my doc?" | |

## 11) Security, Privacy, and Compliance

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 101. | Security model translation | Engine move is a prime time to leak data. | Document-level security "holes" that expose private data to all users. | |
| 102. | Enforcement debt | Old Solr might have had "loose" security. | Suddenly breaking apps that relied on "security through obscurity." | |
| 103. | AWS-specific obligations | IAM and VPC add layers Solr users might not expect. | Cluster is "up" but no one has the IAM permissions to query it. | |
| 104. | App-side vs. Engine-side filtering | Centralizing logic improves security posture. | Relying on the app to "hide" docs that are still visible in the index. | |
| 105. | Access explainability | Essential for audits and compliance (GDPR/SOC2). | Inability to prove that "User X" cannot see "Data Y." | |
| 106. | Regulated field indexing | Prevents PII from entering the search index. | Legal liability from indexing SSNs/Credit Cards for "searchability." | |
| 107. | Leakage via snippets/auto | Snippets can expose data even if the doc is "hidden." | Restricted data showing up in the "Type-ahead" results. | |
| 108. | Role mapping burden | Determines the overhead of managing users. | Managing 5,000 individual users instead of 5 logical roles. | |
| 109. | Authz location decision | Decides if search engine or app "owns" the key. | "Double security" that makes search impossible to debug. | |
| 110. | Log regulation | Search queries often contain PII or secrets. | Creating a "security hole" in the logs of the "secure" search engine. | |

## 12) Managed-Service Constraints

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 111. | Controlled knob reduction | You can't tune what you don't own. | Attempting to fix a performance issue with a Solr setting that doesn't exist in AWS. | |
| 112. | Operational comfort zone | Sets expectations for "Shared Responsibility." | Team panic when they can't SSH into a "broken" node. | |
| 113. | Service vs. Customizable behavior | Some "standard" behaviors are non-negotiable. | Wasting weeks fighting "how AWS works" instead of adapting the app. | |
| 114. | Plugin assumptions | Custom Solr plugins don't just "port" over. | Missing critical business logic that was "hidden" in a Java JAR file. | |
| 115. | Troubleshooting culture | Defines the level of "Root Cause" you can reach. | Blaming AWS for an app bug because you can't see the internal logs. | |
| 116. | Upstream vs. AWS capability | OS has features that AWS might not support yet. | Designing an architecture around a feature that is "Coming Soon" forever. | |
| 117. | Feature availability lag | Ensures roadmap alignment. | Committing to a launch date for a feature that hasn't landed in your region. | |
| 118. | Provisioned vs. Serverless | Changes the cost and scaling model. | Serverless costs bankrupting the project or provisioned nodes sitting idle. | |
| 119. | Convenience vs. Freedom | Is the "Easy Button" worth the "Wall"? | Realizing too late that you need a custom Lucene Similarity that AWS blocks. | |
| 120. | Selection driver | Is this a search choice or a procurement choice? | Forcing a square-peg search engine into a round-hole business problem. | |

## 13) Version and Roadmap Strategy

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 121. | Target version choice | Balances "Newest features" vs "Stability." | Landing on a version that goes End-of-Life 3 months after cutover. | |
| 122. | Upgrade appetite | Determines the "Maintenance" budget. | Search becoming a "legacy" system again within 18 months. | |
| 123. | Breaking change readiness | OS 3 is a major shift (Lucene 10). | Client libraries crashing after a "minor" cluster update. | |
| 124. | Version-gated features | Some features (e.g. Derived Source) need OS 3+. | Designing a schema that the target engine can't actually execute. | |
| 125. | AWS feature-version mapping | AWS adds features to specific versions only. | Realizing you need "Multi-tier" but it's not on the version you just deployed. | |
| 126. | Support policy ownership | Who tracks the EOL dates? | Unplanned "emergency" upgrades forced by AWS security policy. | |
| 127. | Dependent client compatibility | Ensures the rest of the stack is ready. | Upgrading the cluster and breaking the main Python/Java client library. | |
| 128. | Double-migration risk | Avoid "Migrate then immediately upgrade." | Fatigue and regression risk from constant engine churn. | |
| 129. | Behavior drift tolerance | Upgrades will change ranking slightly. | Stakeholders rejecting an upgrade because "results moved." | |
| 130. | Roadmap scorecard | Is the engine moving in the same direction as the business? | Investing in a text engine when the business is moving to Vector/AI. | |

## 14) Cost Model and Economic Surprises

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 131. | Hidden cost components | Infra is only 50% of the true cost. | Running out of budget because you forgot to account for Data Transfer. | |
| 132. | Retention tiering cost | Warm/Cold storage is a huge lever. | Overpaying for SSDs when data could live on cheaper S3-backed storage. | |
| 133. | Dual-run budget | The "Insurance Premium" for a safe cutover. | Forcing a "Big Bang" cutover because Finance won't pay for two weeks of overlap. | |
| 134. | Experimentation hardware | Tuning relevance needs its own capacity. | Relevance tests slowing down production search for real users. | |
| 135. | Consolidation "Tax" | Shared infra isn't always cheaper to manage. | Saving $5k in nodes but spending $50k in engineer coordination time. | |
| 136. | Isolation "Premium" | Security requirements drive up node counts. | Finance rejecting a "secure" architecture because it costs 3x the standard one. | |
| 137. | Data bloat planning | JSON indices are often larger than Solr ones. | Running out of disk space on day 2 because of field mapping bloat. | |
| 138. | Reindexing cost | "Just reindex it" can cost thousands in compute/IO. | A developer loop that costs the company $500 per execution. | |
| 139. | Serverless OCU economics | Serverless is only cheaper if you scale to zero. | A 24/7 workload costing 4x more on Serverless than Provisioned. | |
| 140. | Predictability vs. Low cost | Finance usually prefers a "Fixed" bill. | "Surprise" bills from auto-scaling during a traffic spike. | |

## 15) Performance and Workload Shape

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 141. | Workload mix | Ingest-heavy vs Search-heavy needs different nodes. | "Write-lock" starvation where queries wait for bulk updates to finish. | |
| 142. | Peak alignment | Do you search most when you ingest most? | System crashing every morning during the "Daily Data Load." | |
| 143. | Worst-hour design | Design for peak events, not averages. | Site collapse during the only time the business actually makes money. | |
| 144. | Latency vs. Throughput | Different queries have different speed goals. | Fast keyword search but the "Price Filter" takes 5 seconds. | |
| 145. | Accidental overprovisioning | Solr might be fast only because it's oversized. | Moving to a "right-sized" OS domain and seeing performance drop 50%. | |
| 146. | Toxic query patterns | A few bad queries can take down a whole node. | One user's "Global Regex" search crashing search for everyone else. | |
| 147. | Hidden performance debt | Legacy queries might be inefficient but "fast enough" on Solr. | Realizing your query logic is O(n^2) only after the move. | |
| 148. | Mixed-use estate | Don't mix user search with background logs. | Developers debugging logs and slowing down customer search. | |
| 149. | Freshness vs. Latency SLA | More frequent refreshes slow down queries. | Meeting freshness goals but missing the 200ms latency goal. | |
| 150. | Tuning authority | Who owns the index settings? | Platform teams making infra changes that break product behavior. | |

## 16) User Experience and Trust

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 151. | Change absorption | Too much change at once looks like "broken." | Users leaving the site because they "can't find their usual stuff." | |
| 152. | "Better" as "Inconsistent" | Users value stability over "Smartness." | Improving ranking but losing user trust because results moved. | |
| 153. | Familiarity preservation | Keeps users comfortable during the transition. | Removing the "Sort by X" because it was hard to map even if users love it. | |
| 154. | Side-by-side tools | Essential for stakeholder "Buy-in." | Executives rejecting the move because they can't "see" the difference. | |
| 155. | Content owner confidence | If facets change, they'll think the data is missing. | Merchandisers complaining that products are gone because ranking shifted. | |
| 156. | Support communication | Helpdesk needs to know how to answer "Why is this different?" | Support agents telling users "search is broken" because they weren't briefed. | |
| 157. | Behavior change plan | Proactive vs. Reactive communication. | Getting "Search is broken" tickets for intentional, documented changes. | |
| 158. | High-stakes journeys | Some searches (e.g. Login Help) cannot fail. | Perfecting "T-shirts" but breaking the Password Reset search. | |
| 159. | Trust measurement | Measure "Did they find it?" not just "Did it return 200?" | Low technical errors but high user abandonment. | |
| 160. | Search as Product | Reframe infra move as Product Upgrade. | Treating the move as a backend task and missing UX opportunities. | |

## 17) Organizational Design and Ownership

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 161. | Long-term ownership | Prevents "Orphaned" technology. | The cluster stays on version 1.0 forever because the team disbanded. | |
| 162. | Staffing model | Search is a specialized skill. | Generalists misconfiguring the engine because they didn't know about OS internals. | |
| 163. | Decision vs. Operation split | Prevents Architectural Ivory Towers. | Designers picking a schema that is impossible for Ops to maintain. | |
| 164. | Business levers | Empowers non-engineers to manage relevance. | Developers being interrupted for every synonym or boost change. | |
| 165. | Governance alignment | Defines who says "Yes" to a schema change. | Inconsistent data types across indices because of fragmented ownership. | |
| 166. | Steering group | Aligns search with the broader company roadmap. | Building a Text engine when the company is buying an Image AI. | |
| 167. | "Retrieval + Business" bridge | People who speak both Lucene and Profit. | Perfect technical search that doesn't actually help people buy things. | |
| 168. | Vendor/Consultant lock-in | Ensures the client can survive without you. | The client being scared to touch the system after the consultants leave. | |
| 169. | Internal training | Institutionalizes the new knowledge. | One "Search Expert" quitting and taking all the knowledge with them. | |
| 170. | Deliverable governance | Documentation is part of the Code. | A working cluster with no documentation on how the aliases are managed. | |

## 18) Testing, Acceptance, and Evidence

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 171. | Acceptance criteria | Defines the "Finish Line." | Endless "one more thing" requests that prevent the project from closing. | |
| 172. | Representative data | You can't test on clean data if prod is dirty. | "It worked in staging" but prod data crashes the parser. | |
| 173. | Failure mode testing | What happens when AWS has an incident? | Discovering your HA doesn't work during a real outage. | |
| 174. | Shadow traffic feasibility | The Gold Standard for quality testing. | Discovering a p99 latency spike only after the first 10k users arrive. | |
| 175. | Acceptance thresholds | Defines "Good Enough" to go live. | Delaying go-live for a 0.1% edge case that doesn't affect revenue. | |
| 176. | Skeptic-proof evidence | Data to win the "It looks different" argument. | Losing a political fight about search quality because you didn't have metrics. | |
| 177. | Pre-cutover judgments | Capturing Truth while the old system is still up. | Forgetting how Solr used to rank things and having no baseline to compare. | |
| 178. | Relevance-as-Subjective | Prevents "QA by Opinion." | Search quality being judged by the CEO's favorite query that morning. | |
| 179. | Long-tail evaluation | The tail is where search is won. | Perfecting head queries but losing all revenue from complex, specific searches. | |
| 180. | Load test vs. Readiness | Speed is not the same as Quality. | A lightning-fast engine that returns zero results for every search. | |

## 19) Data Recovery, DR, and Resilience

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 181. | Recovery scope | You need more than just documents. | Restoring the data but realizing synonyms and boosts are gone. | |
| 182. | Snapshot distinction | Auto snapshots can't be restored to a new domain. | Discovering you can't migrate via snapshot because you only have Auto ones. | |
| 183. | Source-rebuild speed | The ultimate recovery path. | A 48-hour search outage while you reindex 100M docs. | |
| 184. | DR design goal | Is it for AWS failure or Operator error? | A Multi-AZ cluster that still loses data because of a DELETE command. | |
| 185. | Accidental mass-delete protection | The Operator Error guardrail. | One fat-finger command taking down the company's primary revenue driver. | |
| 186. | Restore rehearsal | A Plan is not a Reality. | Discovering your Restore script has a syntax error during a real fire. | |
| 187. | Config push blast radius | How much can one synonym file break? | A bad regex in a synonym file crashing the whole cluster. | |
| 188. | Resilience vs. Business tiering | High-tier search needs high-tier resilience. | Over-engineering the internal blog while under-engineering the checkout. | |
| 189. | Cross-region/account strategy | Protects against total region failure. | Realizing your global site depends on a single AWS region. | |
| 190. | Legal retention compatibility | Backups must follow the same rules as live data. | Holding onto deleted user data in a backup and violating privacy laws. | |

## 20) "New to me" Gotchas That Surprise Solr Teams

| ID | Concern | Why it matters | Risk if ignored | Status |
|:---|:---|:---|:---|:---|
| 191. | Blue/Green configuration impact | Small changes can trigger full cluster rebuilds. | Changing a setting and realizing search is slow during the flip. | |
| 192. | Required update cadence | AWS forces service software updates. | Cluster being auto-rebooted by AWS during a peak traffic window. | |
| 193. | Version vs. Service level | Feature availability isn't just about the OS version. | Wasting time debugging a missing feature that just needs a service patch. | |
| 194. | Serverless choice illusion | You still have to pick OCU and shard limits. | Assuming Serverless means magic and ignoring capacity planning. | |
| 195. | Workload separation | Ingest vs Search vs Logs. | One team's log analytics crashing the company's main search. | |
| 196. | Aliases as Contracts | App should never point to a raw index name. | Massive downtime during reindexing because the app name was hardcoded. | |
| 197. | Managed Service as Product | It's a bundle of Engine + IAM + Network. | Solving a search problem when it's actually an IAM policy problem. | |
| 198. | Governance exposure | Migration reveals who has been winging it. | Realizing no one actually knows the source of truth for your configuration. | |
| 199. | Organizational hard decisions | Technology is the easy part. | Project stalling for 6 months because of internal political misalignment. | |
| 200. | Search Operating Model | Use the move to fix the culture of search. | Building a state-of-the-art cluster but keeping a legacy mindset. | |

---

## Consultant Summary

The top mistake is treating Solr-to-OpenSearch as a parser/mapping exercise.
The real work is deciding:
- what search means to the business,
- where governance belongs,
- how much platform control you are giving up or gaining,
- what "same enough" means,
- and who will own relevance, resilience, and security after go-live.
