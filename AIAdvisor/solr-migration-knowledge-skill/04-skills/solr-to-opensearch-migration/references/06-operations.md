# Operational Readiness: The Search Operating Model

**Scope:** Cluster tuning, workload shaping, ingestion lifecycle, security, and relevance governance.
**Audience:** Platform Engineers, SREs, Search Relevance Leads.
**Last reviewed:** 2026-03-19 | **Reviewer:** [Initials]

---

## Key Judgements

- **Don't treat OpenSearch like a black box.** It is a distributed system that requires you to know your "Workload Shape" (ingest vs. search ratio) or you will face constant latency spikes.
- **Infrastructure is Code, Relevance is Data.** You can automate your infrastructure (Terraform/CloudFormation), but your relevance (synonyms, boosts, analyzers) is living data that requires its own deployment pipeline and rollback strategy.
- **"Managed" does not mean "Zero-Touch."** You don't manage the kernel, but you *must* manage your shard density. An over-sharded cluster is a slow cluster, regardless of how much you pay AWS.
- **Highlighting is a performance lever, not just a UI preference.** Using fragments instead of returning full-body fields is the single easiest way to reduce p99 latency under high concurrent load.
- **Relevance is a "Search Product," not an IT ticket.** If the relevance feedback loop isn't owned by a human (PO/Strategist), the engine will rot within 6 months of go-live.

---

## Decision Heuristics: The Search Operating Model

| Area | Fusion/Solr Wisdom | OpenSearch Translation |
|:---|:---|:---|
| **Content** | Patterns, Lang, Syns | Map to `analyzers` and `field-types`. If you don't map `keyword` vs `text` explicitly, you will lose precision. |
| **Resources** | OS/Linux tuning, Heap | Focus on **Instance Type (r6g)** and **EBS GP3 IOPS**. Offload heavy work to `doc_values`. |
| **Updates** | Blue/Green Collection Swapping | Use **Alias-based cutover**. The app points to an alias; you point the alias to the new index version. |
| **Highlighting** | Use fragments | Use `_source` filtering or `highlight` fragments. **Never** return the full multi-megabyte `body` field in search results. |
| **Relevance** | Automated Testing | Use the "Gold Query Set" loop (Quepid/RRE). Governance > Tuning. |

---

## Common Pitfalls: War Stories

- **The "High-Cardinality" Facet Crash:** A client had a `user_id` field and tried to facet on it across 100M documents. Solr's `fieldCache` masked this initially, but OpenSearch tried to load the field into memory and crashed the node. **Lesson:** Always use `keyword` fields for facets and be wary of high-cardinality fields.
- **The "Refresh Interval" Trap:** A client was indexing thousands of small documents per second and set `refresh_interval` to `1s`. The cluster was busy merging segments every second. We bumped it to `30s` (or `-1` during bulk), and cluster CPU utilization dropped by 40% instantly.

---

## Operational Checklist (Pre-Go-Live)

1.  **Workload Profile:** Do you know your ingest vs. search throughput? (e.g., 80% search, 20% ingest). *Size your cluster accordingly.*
2.  **Highlighting Review:** Are your search results returning full-body fields? *Refactor to use fragments.*
3.  **ISM Policy:** Is your "Cold" data being moved to a cheaper tier, or are you paying for "Hot" SSDs for 3-year-old logs? *Enable ISM.*
4.  **Baseline Metrics:** Do you have CloudWatch dashboards for `p99 Latency` and `Thread Pool Rejection`? *If no, do not cut over.*
5.  **Relevance Governance:** Who is the person responsible for the Synonym list? *If there is no named owner, the relevance will drift.*
