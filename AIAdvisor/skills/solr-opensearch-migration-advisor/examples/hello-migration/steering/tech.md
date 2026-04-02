# Technical Steering: `hello` Migration

## Source Stack

[ASSUMED: standard modern SolrCloud installation]

| Component | Version / Config | Notes |
|-----------|-----------------|-------|
| Solr | 8.11.x [ASSUMED: 8.x — Point fields, eDisMax default] | Verify with `solr version` or Admin UI |
| Deployment | SolrCloud + ZooKeeper [ASSUMED] | Check `solr.xml` for `<solrcloud>` element |
| Collections | 1 (`hello`) [ASSUMED: single collection] | Run `curl .../admin/collections?action=LIST` |
| Shards | 2 shards × 1 replica [ASSUMED: minimal config] | Verify in Collection Admin |
| Total docs | ~100K [ASSUMED: moderate; adjust sizing if off by 10×] | Run `curl .../hello/select?q=*:*&rows=0` |
| Index size | ~500 MB [ASSUMED: typical for 100K text docs] | Check `du -sh` on Solr data dir |
| Query pattern | eDisMax via `/select` handler [ASSUMED] | Check `solrconfig.xml` `<requestHandler name="/select">` |
| Similarity | ClassicSimilarity (TF-IDF) [ASSUMED: Solr default] | Check for `<similarity>` in schema.xml |
| Auth | None or BasicAuth [ASSUMED] | Will be replaced by SigV4 on target |

## Target Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| OpenSearch | AWS OpenSearch Service 2.17 [ASSUMED: latest supported] | Managed; no ZooKeeper; native snapshots to S3 |
| Deployment | Provisioned (not Serverless) | Predictable workload; cost-predictable |
| Instance type | `r6g.large.search` × 2 data nodes | Memory-optimized; 2 nodes minimum for replica co-location |
| AZ | 2-AZ (us-east-1a, us-east-1b) [ASSUMED] | Basic HA; upgrade to 3-AZ + dedicated masters for production SLA ≥ 99.9% |
| EBS | gp3, 100 GB per node [ASSUMED: ~3× source index size] | Right-size after actual index measurement |
| Auth | IAM + SigV4 | Service-to-service auth; no multi-tenant Dashboards |
| VPC | Private subnets [ASSUMED] | Always for production; never public endpoint |
| Application | Spring Boot 3.x / Kotlin [ASSUMED] | See `structure.md` for project layout |
| Client lib | `opensearch-java` 2.x | Direct replacement for SolrJ HTTP patterns |

## Compatibility Matrix

| Solr Concept | OpenSearch Equivalent | Migration Effort | Notes |
|-------------|----------------------|-----------------|-------|
| ZooKeeper coordination | Embedded Raft | Zero — AWS-managed | Biggest operational win |
| `schema.xml` fieldType | Index mapping JSON | Medium | Must rewrite; see design.md |
| `<copyField>` | `copy_to` in mapping | Low | Direct equivalent |
| `<dynamicField>` | `dynamic_templates` | Low | Pattern matching preserved |
| eDisMax `qf`/`pf`/`mm` | `multi_match` + `match_phrase` | Medium | Semantics differ at edges |
| `fq` filter queries | `bool.filter` clauses | Low | Direct conceptual equivalent |
| `facet.field` | `terms` aggregation | Low | Syntax change only |
| `facet.range` | `range` aggregation | Low | Syntax change only |
| `start`/`rows` pagination | `from`/`size` | Low | Identical semantics up to 10K |
| Deep pagination (>10K) | `search_after` | Medium | Required; `from/size` cliff at 10K |
| TF-IDF similarity | BM25 (OpenSearch default) | **High — tuning required** | Expect 30-40% ranking difference |
| SolrJ client | `opensearch-java` | Medium | Query builder API is different |
| configset XML | JSON mappings + index settings | High | Full rewrite; no converter |
| Collection Admin API | Index API | Low | Different endpoint, similar model |
| Soft commit | `refresh_interval` (default 1s) | Low | Functionally equivalent |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Relevance degradation (BM25 vs TF-IDF) | **High** [ASSUMED: not yet measured] | High | Build Quepid judgment set in Phase 1; baseline before any changes |
| Schema assumption is wrong (nested docs) | Low [ASSUMED] | **Critical** | Run must-verify checks in product.md before Phase 2 |
| Custom analyzer plugins missed | Low [ASSUMED] | High | Audit `schema.xml` for non-standard `class=` references |
| AWS version lag (feature not available) | Low | Medium | Verify OpenSearch 2.17 supports all features needed; check AWS release notes |
| `from/size` pagination cliff | **Medium** | Medium | Identify all pagination call sites; plan `search_after` migration |
| Dual-write lag causes stale reads | Medium | Medium | Monitor lag metrics; define acceptable staleness SLO |

## Success Metrics

| Metric | Target | How to measure |
|--------|--------|---------------|
| Schema field coverage | 100% | Compare `schema.xml` field count vs OpenSearch `_mapping` |
| Query result parity (top-5) | ≥ 90% identical [ASSUMED: threshold] | Quepid side-by-side comparison |
| P99 search latency | ≤ current Solr P99 + 20% [ASSUMED] | Load test with production traffic replay |
| Index throughput | ≥ current Solr indexing rate | Benchmark during Phase 3 dual-write |
| Error rate at cutover | < 0.1% [ASSUMED] | Monitor `_cat/indices` health during traffic shift |
