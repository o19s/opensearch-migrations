# Stakeholder Steering: Solr-to-OpenSearch Migration

## When NOT to Migrate

Treat these as red flags. Any single one warrants a hard conversation; two or more together mean "don't migrate."

| Signal | Why It Kills the Migration |
|---|---|
| Only goal is reducing license/infra costs | OpenSearch has real costs at scale too. Run a cost model first -- the savings may not justify the disruption. |
| No analytics on the current Solr system | You cannot establish a relevance baseline. You will have no way to prove the migration improved anything. |
| Less than 2 months to production deadline | Almost always produces a rushed lift-and-shift that degrades search quality and frustrates every stakeholder. |
| Product owner cannot name top 5 user information needs | The search team lacks direction to make good relevance decisions on either platform. |
| Existing search is "good enough" by measurable criteria | Migrations disrupt. If the status quo is acceptable, disruption cost likely exceeds benefit. |
| "Everyone uses Elasticsearch/OpenSearch" is the only rationale | Not a reason. Ask: what does the customer get that they don't have today? |
| Key knowledge holder is departing with no export plan | Undocumented synonyms, boost rules, and pipeline logic cannot be recreated after that person leaves. Capture first, migrate second. |

**"Don't migrate" is a legitimate assessment outcome.** Say so clearly and in writing.

## Pre-Migration Prerequisites

All must be true before kickoff. Missing items are blockers, not risks.

- [ ] Stakeholder-defined success criteria exist and are quantified (nDCG target, latency budget, cost ceiling)
- [ ] Project scope, team, and goals are documented and agreed
- [ ] Path to content access is identified with owner, timeline, and blockers
- [ ] Query analytics access is confirmed (query logs, click data, engagement signals)
- [ ] At least 2-4 weeks of real query data available for baseline and judgement sets
- [ ] Current system architecture documented -- every integration point that calls Solr
- [ ] Solr-specific capabilities inventoried, especially those without direct OpenSearch equivalents (custom UpdateProcessors, DIH, Carrot2 clustering, CDCR, function queries, join/graph queries)
- [ ] Target OpenSearch version selected; AWS managed vs. self-managed decision made
- [ ] Key roles formally assigned (search lead, infra engineer, app engineers, data engineer)

## Stakeholder Concerns and Priorities

### Search Engineer
- **Primary concern:** Relevance regression. Solr TF-IDF vs OpenSearch BM25 produces different rankings. Expect 3-5% initial degradation on critical queries.
- **Needs:** Relevance evaluation framework, side-by-side comparison tooling, offline testing of top 1000 queries before cutover.
- **Risk tolerance:** Low for relevance; moderate for operational change.
- **Watch for:** Analyzer chain translation gaps, dismax/edismax behavior differences, boost/bq/bf parity.

### Application Developer
- **Primary concern:** Will my app break? How much code do I rewrite?
- **Needs:** Clear client library migration path (SolrJ to OpenSearch client), per-app effort estimate (typically 1-2 days), runbooks, fallback plan.
- **Risk tolerance:** Low for breaking changes; wants fast, bounded migration windows.
- **Watch for:** Query syntax translation bugs that only surface in production, dynamic field mapping differences.

### DevOps / Platform Engineer
- **Primary concern:** Operational burden and on-call impact. Will this reduce toil?
- **Needs:** Managed service benefits quantified (eliminate ZooKeeper, manual shard rebalancing), new monitoring stack (CloudWatch, slow query logs), clear runbooks.
- **Risk tolerance:** Moderate if operational improvement is demonstrated.
- **Watch for:** JVM tuning differences, shard allocation strategy, index size growth (expect 10-15% larger than Solr).

### Data Engineer
- **Primary concern:** Data completeness during migration. Zero document loss.
- **Needs:** Bulk migration pipeline (Solr to S3 to OpenSearch), dual-write capability, consistency validation (document count match, field content integrity).
- **Risk tolerance:** Zero for data loss; moderate for timeline.
- **Watch for:** Writes to Solr during migration window, indexing lag, replication status gaps.

### Architect
- **Primary concern:** Risk clarity over sales-demo smoothness. Where are the hard problems?
- **Needs:** Feature gap analysis (especially custom plugins, function queries, join/graph queries), cutover/rollback/failover planning, multi-DC topology mapping.
- **Risk tolerance:** High for complexity if risks are surfaced honestly.
- **Watch for:** Features that require redesign rather than translation, operational topology changes, vendor lock-in implications.

### Product Manager
- **Primary concern:** User-facing impact and timeline predictability.
- **Needs:** Zero-downtime guarantee, gradual rollout plan (1% canary, then 10/25/50/100%), measurable success criteria tied to business outcomes.
- **Risk tolerance:** Zero for user-visible degradation; moderate for internal complexity.
- **Watch for:** Scope creep ("while we're migrating, let's also..."), timeline extensions that erode stakeholder confidence.

## Risk Categories and Mitigations

| Category | Key Risks | Mitigation |
|---|---|---|
| **Content Access** | Pipeline doesn't exist; access takes weeks longer than estimated | Put on critical path Day 1. Do not start schema design without real documents. |
| **Relevance** | Scoring algorithm differences; analyzer chain gaps; boost logic parity | Build evaluation framework pre-migration. Run offline comparison. A/B test before full cutover. |
| **Timeline** | Under-estimated effort; content delays; goalposts moved | Phased approach with go/no-go gates. Dual-write with percentage-based cutover. |
| **Knowledge** | Tribal knowledge in Solr config; undocumented synonyms/boosts | Export and document everything before migration begins. Knowledge transfer is a first-class workstream. |
| **Operational** | New monitoring stack; different failure modes; JVM tuning gaps | Training + runbooks before cutover. Shadow traffic period for operational learning. |
| **Feature Gap** | Custom plugins, DIH, function queries, graph queries have no 1:1 equivalent | Inventory all Solr capabilities early. Flag redesign-required items as separate workstreams. |

## Success Metrics by Stakeholder

| Stakeholder | Metric | Target |
|---|---|---|
| Search Engineer | Relevance (CTR, nDCG) | No degradation > 2% post-migration |
| Search Engineer | Query latency p50/p95/p99 | Meet or beat Solr baseline |
| App Developer | Migration effort per app | 1-2 days with runbook support |
| App Developer | Rollback capability | Instant revert available for 1 week post-cutover |
| DevOps | Monthly operational hours | < 5 hours (down from 15-20) |
| DevOps | MTTR | < 30 minutes (down from 2+ hours) |
| Data Engineer | Document completeness | 100% count match, zero data loss |
| Data Engineer | Index freshness | < 5 seconds from submission |
| Architect | Feature coverage | All critical Solr capabilities mapped or redesigned |
| Product Manager | User-visible downtime | Zero during migration |
| Product Manager | Search availability | 99.95% uptime post-migration |
| Finance | Year 1 net cost impact | Positive ROI after operational savings |
