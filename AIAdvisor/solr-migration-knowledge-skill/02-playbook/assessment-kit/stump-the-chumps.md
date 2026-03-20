# Stump-the-Chumps: Solr to OpenSearch Migration

Use this as a red-team checklist during migration planning, vendor reviews, design reviews, or cutover readiness checks.

## Foundation and Schema

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Field type mismatch | Solr types do not map cleanly to OpenSearch mappings. | Which fields need separate `text` and `keyword` representations, and how was that decided? | “We converted types mechanically.” | High |
| Analyzer drift | Analyzer behavior changes recall and ranking. | Which analyzers were audited, and where do behaviors differ? | “Standard analyzer should be close enough.” | High |
| `copyField` dependency | Hidden search behavior often lives in schema composition. | What replaces `copyField`, and where is that logic implemented now? | “We dropped it because OpenSearch doesn’t need it.” | High |
| Dynamic field explosion | Uncontrolled mappings can destabilize the cluster. | How are you preventing dynamic-field usage from becoming mapping sprawl? | “We left dynamic mapping on.” | High |
| Exact vs analyzed confusion | Search, sort, filter, and facet require different field shapes. | Which fields are used for query, sort, facet, and filter separately? | “We use the same field for everything.” | High |
| Date/range mismatch | Boundaries and timezone behavior create silent correctness bugs. | How did you validate inclusive/exclusive bounds and timezone-sensitive queries? | “Dates looked fine in spot checks.” | Medium |
| Schema evolution plan | Mapping mistakes are inevitable. | What is the safe reindex/alias strategy for schema changes after go-live? | “We’ll update the mapping in place.” | High |

## Query Semantics and Relevance

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Filter query translation | Incorrect translation hurts both performance and semantics. | How did you confirm old `fq` logic now runs in filter context? | “We put everything in `must`.” | Medium |
| Query parser dependency | User query behavior is often parser-dependent. | Which eDisMax or local-param behaviors were preserved, redesigned, or dropped? | “We pass the raw string through.” | High |
| Boosting rewrite | Solr boosting syntax does not port directly. | How were `qf`, `pf`, `bq`, `bf`, and function boosts re-expressed? | “We copied the same boosts conceptually.” | High |
| TF-IDF to BM25 drift | Default ranking changes materially. | What benchmark shows ranking drift is acceptable? | “The engines are both Lucene.” | High |
| Phrase/slop mismatch | Precision logic is often hidden in phrase boosts. | Which phrase-sensitive queries were tested before and after? | “We didn’t isolate phrase queries.” | Medium |
| No relevance benchmark | Parity needs evidence, not intuition. | What judged query set defines pass/fail? | “Stakeholders will know it when they see it.” | High |
| Deterministic ordering assumption | Distributed tie-breaking can shift. | How do you stabilize sort order across pages and repeated queries? | “The order should be basically the same.” | Medium |
| Parity absolutism | Some legacy behaviors should be dropped intentionally. | Which behaviors were explicitly de-scoped or redesigned with stakeholder signoff? | “We expect full parity.” | High |
| Lucene-underneath fallacy | Shared lineage hides major behavioral differences. | Where did you account for parser, scoring, and operational differences? | “Lucene is Lucene.” | Critical |

## Features and Product Behavior

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Facet parity illusion | Aggregations are similar, not identical. | How did you validate facet counts, ordering, and performance on key pages? | “Facets are just aggregations, so they match.” | High |
| Grouping/collapse gap | Solr grouping has reduced equivalents. | Which grouped-result experiences were redesigned vs preserved? | “Collapse should handle it.” | High |
| Highlighting differences | Snippets affect user trust and CTR. | How were highlight quality and leakage risks validated? | “Snippets aren’t core functionality.” | Medium |
| Autocomplete/suggester redesign | Suggest features usually need dedicated design. | What is the data/update strategy for autocomplete and spell suggestions? | “We’ll query the main index for typeahead.” | High |
| MLT/related content gap | Related-content features are often under-specified. | Which related-content experiences were benchmarked separately? | “That’s basically search too.” | Medium |
| Nested/parent-child remodel | Block joins require intentional redesign. | Where did you choose `nested`, `join`, or denormalization, and why? | “We’ll figure that out after ingestion.” | High |
| No equivalent for core workload | Some Solr-heavy patterns simply do not survive intact. | Which features require redesign because no direct OpenSearch equivalent exists? | “We’ll emulate everything later.” | Critical |

## Data Flow and Migration Execution

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Refresh/commit misunderstanding | Freshness guarantees differ across engines. | What indexing visibility SLA do you support now? | “Documents show up eventually.” | Medium |
| Atomic update assumption | Partial updates differ semantically. | Which write patterns were retested for update correctness? | “Partial update is partial update.” | High |
| Undocumented query producers | Search estates usually have hidden consumers. | How did you inventory all producers of search traffic and Solr APIs? | “We covered the main app.” | High |
| Solr-as-database usage | Scan/export workloads often break post-migration. | Which jobs relied on giant result windows or export-like behavior? | “No one should be doing that.” | High |
| Dual-write inconsistency | Without convergence, validation is meaningless. | How are write failures, retries, and ordering mismatches detected? | “If one side fails we’ll retry later.” | High |
| Reindex replay gaps | Historical backfill plus live writes must converge. | How did you prove no gaps or duplicates after reindex plus CDC catch-up? | “Document counts were close.” | High |
| Delete/tombstone handling | Deletes are easy to miss in CDC. | How are deletes represented, replayed, and audited? | “We mostly care about inserts and updates.” | High |
| Shadow traffic evidence gap | Replay only helps if instrumented well. | What exact comparison artifacts exist for query/result/facet diffs? | “People manually compared a few searches.” | High |

## Performance and Scale

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Deep pagination assumption | Solr pagination patterns do not scale the same way. | Which endpoints relied on large offsets, and what replaced them? | “We increased the result window.” | High |
| Facet correctness not monitored | Broken browse can hide behind green latency charts. | What monitors detect wrong counts and empty-category regressions? | “We monitor cluster health.” | Medium |
| Shard topology mis-sizing | Bad shard math creates long-term pain. | How were shard counts, replica counts, and growth projections chosen? | “We copied the Solr layout.” | High |
| Primary/replica placement assumption | Placement rules differ and affect node count. | How did placement constraints change your capacity plan? | “We’ll use the same node count as today.” | High |
| Cost model fantasy | Infra savings are often overstated. | What cost model includes dual-run, reindex, storage growth, and transfer? | “Managed service should be cheaper overall.” | High |

## Security and Compliance

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Security model translation | Access control mistakes are catastrophic. | Where is authorization enforced now, and how was it penetration-tested? | “The app already filters results.” | Critical |
| PII/regulatory indexing risk | Migration can replicate bad patterns at scale. | Which sensitive fields are excluded, masked, or separately governed? | “We indexed everything for flexibility.” | Critical |

## Managed Service and Platform Constraints

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Managed-service knob loss | AWS-managed search reduces operational control. | Which Solr tuning/debugging capabilities are no longer available? | “Managed means we won’t need tuning.” | High |
| Plugin/custom handler dependency | Hidden business logic often lives in engine extensions. | Which custom Solr components were found, and what replaced each one? | “We didn’t think any were important.” | Critical |
| Version/feature mismatch | Design may depend on unavailable features. | Which target version/tier/region constraints were validated up front? | “We assumed the service supports OpenSearch features generally.” | High |
| Mechanical translation fantasy | This is not config conversion work. | Which parts were redesigned rather than translated? | “Most of it ports directly.” | Critical |

## Cutover and Governance

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Rollback plan not real | Rollback is meaningless without clean mechanics. | What exact steps restore traffic and data trust if cutover fails? | “We can always point back to Solr.” | Critical |
| Operational ownership gap | A new platform without an owner becomes unstable. | Who owns performance, incidents, schema changes, and relevance after cutover? | “The team will work it out.” | High |
| Success criteria undefined | Without signed criteria, migration never finishes. | What are the go/no-go gates and who approved them? | “We’ll decide near launch.” | High |
| No go/no-go authority | Mixed evidence needs a decision owner. | Who can stop the launch if search quality is not acceptable? | “Leadership wants the date held.” | Critical |

## Troubleshooting and Truth Detection

This is a cross-cutting section rather than a standalone migration phase. Use it during incidents, parity reviews, and late-stage cutover rehearsals.

| Issue | Why it matters | What to ask | Red flag answer | Severity |
|---|---|---|---|---|
| Data vs query diagnosis gap | Teams waste time if they cannot separate bad data from bad query logic. | What evidence tells you whether a failure is in ingestion, mapping, or query translation? | “We usually just inspect the query first.” | High |
| Missing vs stale vs leaked docs | Different failure modes need different debugging paths. | How do you prove whether a document is missing, stale, duplicated, or improperly visible? | “If search looks wrong, we reindex.” | Critical |
| Rank explainability gap | You cannot fix relevance regressions you cannot explain. | What tools or artifacts show why a document ranked where it did before and after migration? | “We compare the top 10 manually.” | High |
| Managed-service observability gap | AWS-managed platforms reduce direct node-level introspection. | Which diagnostic signals do you still have, and which old Solr troubleshooting habits are no longer available? | “We’ll open a support ticket if needed.” | High |
| Evidence pack missing | Troubleshooting needs repeatable comparison artifacts. | What are the first five artifacts you collect during a parity incident? | “Logs and screenshots.” | High |

