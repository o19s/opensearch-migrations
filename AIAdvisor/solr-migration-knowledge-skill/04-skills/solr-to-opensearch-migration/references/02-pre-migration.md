# Pre-Migration Assessment: The "Go/No-Go" Audit

**Scope:** Source Solr audit, performance baseline, organizational readiness, and data volume/shape assessment.
**Audience:** Engagement Leads, Solution Architects.
**Last reviewed:** 2026-03-19 | **Reviewer:** [Initials]

---

## Key Judgements

- **Don't touch a production cluster without a "Read-Only" assessment first.** Use the Solr `/export` handler or a simple log-analysis script to map the "Workload Shape" before moving a single byte of data.
- **The "Data Archaeology" phase is mandatory.** If the client doesn't know what's in their `schema.xml` or why certain custom jars exist, the migration *will* fail. You must allocate 1 week to just "learn the mess."
- **Relevance is measured, not guessed.** You cannot move from Solr to OpenSearch without a baseline relevance metric (NDCG/Precision@K). If the client says "we don't have time," they are choosing to fly blind.
- **Infrastructure ≠ Relevance.** An AWS-optimized cluster is a success of IT, not a success of Search. The assessment must distinguish between "Platform Upgrades" and "Relevance Improvements."

---

## Assessment Checklist (The "Baseline")

1.  **Workload Inventory**:
    - [ ] Search query volume (QPS) and patterns (Head vs. Long Tail).
    - [ ] Ingestion throughput (docs/sec, batch vs. streaming).
    - [ ] Document complexity (size, depth, presence of large blobs/blobs).
2.  **Schema Audit**:
    - [ ] Field type inventory (What is `text`, `string`, `int`, `float`, `date`, `geo`?).
    - [ ] Analyzer chain replication (Can we recreate these in OpenSearch?).
    - [ ] CopyField mapping (What derived fields exist?).
3.  **Governance Baseline**:
    - [ ] Who owns the "Synonym List"?
    - [ ] Who owns the "Boost/Ranking Rules"?
    - [ ] Are these rules artifacts (files/configs) or hardcoded in Java/Scala?
4.  **Performance Baseline**:
    - [ ] p99 Latency (Search and Indexing).
    - [ ] Current infrastructure cost and utilization.

---

## Decision Heuristics: "The Assessment Scorecard"

| Condition | Assessment | Recommendation |
|:---|:---|:---|
| **Unknown Schema** | "We have no schema.xml, we just use dynamic fields." | **Red Flag**: Requires 2 weeks of schema discovery before planning. |
| **No Query Logs** | "We only see 500 errors in our monitoring." | **Red Flag**: Must implement structured query logging before migration can start. |
| **High Stakeholder Fear** | "If results move, my boss will fire us." | **Yellow Flag**: Requires a longer "Shadow Traffic" testing period (4+ weeks). |
| **Solr as a DB** | "We query everything by ID, not keyword." | **Red Flag**: You are misusing a search engine. Evaluate if DynamoDB/RDS is a better target. |

---

## Next Steps

1.  **Run `solr-schema-audit.py`**: Execute this against the live cluster to dump the schema to JSON.
2.  **Analyze Top 100 Queries**: Extract from logs. If logs are missing, create a temporary log-capture filter.
3.  **Conduct "Relevance Interviews"**: Ask the Product Owner: "How do you define a 'good' search result for query X?"
