# Product Steering: `hello` Migration

## Project Goal

Migrate the `hello` Solr collection from a self-managed SolrCloud cluster to
AWS OpenSearch Service 2.x, preserving search quality and reducing operational overhead.

[ASSUMED: The goal is operational simplification — moving from self-managed ZooKeeper +
SolrCloud to AWS-managed OpenSearch. The primary driver is reducing infra maintenance
burden, not a relevance improvement project.]

## Scope

### In Scope

- Migrate the single `hello` collection [ASSUMED: single collection; adjust if you have multiple]
- Translate all active query patterns (eDisMax + facets) to OpenSearch Query DSL
- Convert `schema.xml` field definitions to OpenSearch index mappings
- Build a dual-write indexing bridge for zero-downtime cutover
- Shadow-traffic comparison to validate search quality parity
- Spring Boot 3.x / Kotlin query service layer [ASSUMED: platform]
- AWS OpenSearch Service (provisioned, 2-node, us-east-1) [ASSUMED: region + topology]

### Out of Scope

- Relevance tuning beyond parity (that is a Phase 2 initiative after cutover)
- Migrating other Solr collections [ASSUMED: only `hello` collection]
- Building a new search UI — this migration is backend/API only
- Document parsing (Tika, Solr Cell) [ASSUMED: not in use; verify with `grep -r "ExtractingRequestHandler" solrconfig.xml`]
- Cross-datacenter replication (CDCR) [ASSUMED: not in use]
- Streaming expressions [ASSUMED: not in use]

### Must-Verify Items ⭐

Before treating this spec as executable, verify the following manually:

| Item | How to check | Risk if wrong |
|------|-------------|---------------|
| No nested documents | `grep -r "childFilter\|BlockJoin\|toParent" solrconfig.xml` | Invalidates entire mapping design |
| No custom analyzers | `grep -r "class=" schema.xml \| grep -v "solr.TextField\|solr.StrField\|solr.IntPointField\|solr.DatePointField"` | Requires manual analyzer port |
| No DIH | `grep -r "DataImportHandler" solrconfig.xml` | Hidden ingestion path needs migration |
| No atomic updates | `grep -r '"set"\|"add"\|"inc"\|"remove"' indexing-code/` | Semantic differences can corrupt documents |
| No streaming expressions | `grep -r "/stream\|StreamHandler" solrconfig.xml` | No OpenSearch equivalent — redesign needed |

## Success Criteria

A migration is **done** when all three of these are true:

1. **Schema fidelity** — every field in the Solr collection exists in OpenSearch with
   a semantically equivalent mapping (correct type, correct analysis, correct sortability)

2. **Query equivalence** — the top-5 results for the 20 most common queries are in the
   same order ± 1 position, measured with a Quepid judgment set against both systems in parallel

3. **Operational readiness** — the AWS OpenSearch cluster is running, monitored, has
   automated snapshots configured, and has been load-tested at 2× expected peak QPS

## Stakeholders

[ASSUMED: typical migration team shape]

| Role | Responsibility |
|------|---------------|
| Search Engineer | Schema translation, query migration, relevance validation |
| Backend Developer | Spring Boot service layer, indexing pipeline |
| DevOps / Platform | AWS provisioning, VPC, IAM, monitoring |
| Product Owner | Approve success criteria, sign off on go/no-go gates |

## Key Decisions Made (in this spec)

| Decision | Choice | Rationale |
|---------|--------|-----------|
| Target platform | AWS OpenSearch Service (provisioned) | Managed, no ZooKeeper ops, snapshot-native |
| Instance type | r6g.large.search × 2 | Memory-optimized for search workloads; 2 nodes = minimum for replica co-location rule |
| Auth | IAM + SigV4 | Service-to-service; no user-facing search console requiring FGAC |
| Cutover strategy | Dual-write + gradual traffic shift | Zero-downtime; rollback path preserved |
| Relevance goal | Parity with current Solr behavior | Lowest risk; improvements deferred to post-migration |

## Open Decisions (must be resolved before Phase 2)

1. **Relevance parity threshold** — what % of queries can have result-set differences
   before the go/no-go gate blocks cutover? (Suggested default: ≤10% of top-5 rankings differ)

2. **Dual-write ownership** — does the indexing pipeline live in the application, or in a
   separate Lambda/job? (This spec assumes in-application dual-write)

3. **Multi-AZ or single-AZ?** — this spec uses 2-AZ [ASSUMED]. For production SLA > 99.9%,
   consider 3-AZ with 3 dedicated master nodes.
