# Technical Steering: Techproducts Demo Migration

## Source Stack

**Solr Instance:** Apache Solr 9.x (or 8.x—compatible)

**Collection:** `techproducts` (bundled demo)

**Indexing:**
- SchemaAPI (schema.xml) defines 15 explicit fields + 7 dynamic field patterns
- Analyzers: standard (tokenizer + stopwords + lowercase + synonym graph)
- CopyFields: name, features, manu, cat → _text_ (catchall)
- CopyFields: manu → manu_exact (to preserve before stemming)

**Querying:**
- Request handler: /select (eDisMax, defType=edismax)
- Query fields (qf): name^2, features^1, cat^0.5
- Facets: facet.field=cat, facet.field=inStock, facet.range=price
- Filters: fq=inStock:true, fq=price:[0 TO 400], fq=cat:electronics
- Geo: fq={!geofilt sfield=store pt=37.77,-122.41 d=10}

**Client:** SolrJ 9.x (for data export)

## Target Stack

**AWS OpenSearch Service:** Version 2.x (managed, SigV4)

**Deployment:** Single AZ (dev/demo), VPC, IAM authentication

**Index:** Single index `techproducts` with:
- Mapping JSON (replaces schema.xml)
- Dynamic templates (replaces dynamic field definitions)
- Custom analyzer (synonym graph, equivalent to Solr text_general)
- One shard, one replica (minimal HA)

**Querying:** Query DSL (JSON) — no DisMax/eDisMax parser

**Client:** OpenSearch Java Client 2.10+

**Application Framework:** Spring Boot 3.5 + Spring Data OpenSearch 1.3+

**Language:** Kotlin (on JVM 21+)

## Key Decisions Already Made

| Decision | Rationale |
|----------|-----------|
| AWS managed service, not self-hosted | Eliminates ZooKeeper, cluster management; SigV4 auth fits AWS ecosystem |
| Spring Boot 3.5 | LTS release, modern baseline for cloud deployments |
| Kotlin | Type safety, interop with Spring ecosystem, coroutine support for async indexing |
| Query DSL instead of attempting DisMax emulation | DisMax has no 1:1 equivalent; redesigning queries teaches proper migration approach |
| Single index, not multiple (no aliasing) | Demo scope doesn't require versioning or A/B traffic splitting |
| No data versioning or dual-write | Single-pass migration: export Solr → transform → load OpenSearch |

## Open Technical Decisions

**For this project:**
- [ ] AWS OpenSearch endpoint (to be provided by infrastructure team)
- [ ] SigV4 signing credentials (IAM role or explicit keys)
- [ ] VPC/security group rules (allow Spring Boot app to reach OpenSearch)
- [ ] Deployment target for Spring Boot app (ECS, EC2, Fargate, local)

**Architectural trade-offs for real migrations:**
- **Shard count:** Techproducts uses 1 (optimal). Real migration: measure data size → shard_count = total_GB / 40
- **Replica count:** Techproducts uses 1 (HA). Real: 2-3 for production SLA
- **Refresh interval:** Fixed to 1s. Real: tune based on indexing volume vs. query freshness requirements
- **BM25 parameters:** Using OpenSearch defaults. Real: establish baseline on Solr, tune k1/b to approximate if needed
- **Index lifecycle (ISM):** Not used (demo). Real: auto-rollover for time-series, delete policies for retention

## Stack Compatibility Matrix

| Layer | Solr | OpenSearch | Migration Note |
|-------|------|-----------|----------------|
| Cluster coordination | ZooKeeper | Embedded Raft | Operational model simplification |
| Config format | XML (schema.xml, solrconfig.xml) | JSON (mappings + settings) | Full rewrite |
| Query language | DisMax/eDisMax/LuceneQP | Query DSL | Redesign required |
| Relevance scoring | TF-IDF (default) | BM25 | Expect 30-40% ranking change |
| Index format | Lucene 9.x | Lucene 9.x | Binary incompatible due to OpenSearch extensions |
| Client API | SolrJ | opensearch-java | Full reimplementation |
| Field types | FieldType classes | JSON type definitions | Mechanical translation mostly sufficient |
| Analyzers | Java plugin classes | Built-in filters + custom plugins | Stock filters available; custom → plugin if needed |

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Query results diverge significantly | Medium | High | Baseline Solr results before migration; measure top-10 overlap |
| BM25 relevance inferior to TF-IDF out of box | High | Medium | Re-tune BM25 params post-migration; accept some tuning time |
| SigV4 auth complications | Low | Medium | Test AWS credential chain locally first; use managed IAM role in app |
| Mapping type errors on first indexing | Medium | Low | Use strict dynamic mapping to catch type mismatches early |
| Query timeout due to index config | Low | Low | Start conservative (refresh_interval=1s), monitor latency, adjust if slow |

## Success Metrics (Technical)

- Query response time: Solr baseline vs. OpenSearch within ±15%
- Error rate: < 0.1% across all query types
- Document count: `count(OpenSearch) == 7` exactly
- Facet counts: all match source within rounding error
- Top-10 overlap: > 80% across representative query set

---

**Tech Lead:** Search Platform Team
**Last Updated:** 2026-03-17
**Ready for Design Phase:** Yes
