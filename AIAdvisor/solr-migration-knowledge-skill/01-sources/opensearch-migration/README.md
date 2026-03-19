# Solr to OpenSearch Migration Documentation

This directory contains substantive, expert-level migration documentation designed to guide technical teams through migrating from Apache Solr to Amazon OpenSearch.

## Files in This Collection

### 1. aws-solr-migration-blog.md (617 lines)
**Source**: https://aws.amazon.com/blogs/big-data/migrate-from-apache-solr-to-opensearch/

Complete AWS-recommended migration strategy covering:
- Full refactor vs lift-and-shift approaches
- Dual-write with historical catchup architecture
- Architectural differences (ZooKeeper removal, clustering, configuration)
- Query migration from Solr parsers (Standard, DisMax, eDisMax) to OpenSearch Query DSL
- Schema migration from XML to JSON mappings
- Data migration approaches (source-of-truth reindex, Logstash, custom ETL)
- A/B testing and gradual traffic shifting (5% → 100%)
- Rollback procedures and risk mitigation

**Key Takeaway**: Treat OpenSearch as a new platform requiring intentional design, not a 1:1 port of Solr.

---

### 2. query-syntax-mapping.md (976 lines)
**Source**: https://bigdataboutique.com/blog/solr-to-opensearch-migration-deep-dive

Comprehensive query syntax reference with before/after examples:
- Solr Standard parser → OpenSearch match/bool queries
- DisMax → multi_match with field boosts
- eDisMax → complex bool with phrase slop
- Filter queries (fq) → bool.filter context
- Faceting: term/range/date facets → aggregations
- Boost queries and functions → function_score queries
- Highlighting, spellcheck/suggesters, MoreLikeThis
- Pagination: offset-based (from/size) vs cursor-based (search_after)
- Complex e-commerce and blog search examples
- Performance considerations per feature

**Key Takeaway**: Solr uses URL parameters; OpenSearch uses JSON Query DSL. Facets become aggregations.

---

### 3. schema-field-type-mapping.md (805 lines)
**Source**: https://bigdataboutique.com/blog/schema-migration-from-solr-to-elasticsearch-opensearch-a0072b

Detailed field type and analyzer reference:
- Primitive type mappings (string→keyword, int→integer, etc.)
- Text types with language-specific analyzers
- Complex analyzer chains: tokenizers, filters, character filters
- Dynamic fields (Solr *_s suffix) → dynamic templates
- CopyField → copy_to
- Field properties (indexed, stored, docValues)
- Nested documents and multivalue field handling
- Full e-commerce product schema example (Solr vs OpenSearch)
- Migration validation checklist

**Key Takeaway**: Schema is immutable in OpenSearch; plan carefully before index creation.

---

### 4. common-pitfalls.md (859 lines)
**Sources**: BigData Boutique, OpenSearch documentation, community experiences

Real-world migration pitfalls from production migrations:

1. **Shard collocation differences** - OpenSearch forbids primary+replica on same node
2. **Relevance scoring** - TF-IDF (Solr) vs BM25 (OpenSearch) produces different rankings
3. **Commit/refresh semantics** - Solr soft/hard commits vs OpenSearch refresh_interval
4. **Atomic updates** - Different versioning approaches (seq_no/primary_term)
5. **ZooKeeper removal** - Loss of external cluster state observability
6. **Schemaless defaults** - OpenSearch auto-maps differently than Solr
7. **Custom similarity classes** - Cannot be ported; must rewrite as function_score
8. **Function queries** - Limited equivalents; script-based alternatives are slower
9. **Leader election vs primary allocation** - Different replication semantics
10. **Monitoring differences** - Solr Admin UI vs OpenSearch Dashboards
11. **Connection pooling** - Default pool sizes insufficient for high concurrency
12. **JVM tuning** - OpenSearch uses more memory per shard than Solr

Each pitfall includes:
- Concrete symptom description
- Root cause explanation
- Remediation strategies with code examples
- Trade-off analysis

**Key Takeaway**: Plan for 2-4 weeks of shadow testing; expect 30-40% difference in top-10 search results.

---

## How to Use This Documentation

### Phase 1: Planning (Week 1)
1. Read **aws-solr-migration-blog.md** sections 1-3 (strategy, architecture overview)
2. Use **schema-field-type-mapping.md** to audit your current Solr schema
3. Identify your top 20 queries in **query-syntax-mapping.md** and plan translations

### Phase 2: Design (Week 2-3)
1. Create OpenSearch index mappings using **schema-field-type-mapping.md** examples
2. Translate all queries using **query-syntax-mapping.md** reference
3. Read **common-pitfalls.md** to identify issues specific to your workload
4. Plan dual-write architecture per **aws-solr-migration-blog.md** (Dual-Write section)

### Phase 3: Testing (Week 4-8)
1. Implement shadow read phase per **aws-solr-migration-blog.md**
2. Compare result sets using metrics from **common-pitfalls.md** (Relevance scoring section)
3. Verify A/B testing metrics (top-10 overlap target: 75-85%)
4. Test rollback procedures documented in **aws-solr-migration-blog.md**

### Phase 4: Execution (Week 9-12)
1. Execute gradual traffic shift per **aws-solr-migration-blog.md** (5% → 100%)
2. Monitor using OpenSearch Dashboards per **common-pitfalls.md** (Monitoring section)
3. Maintain Solr as fallback for 30+ days
4. Decommission Solr after validation period

---

## Quick Reference: Most Critical Differences

| Aspect | Solr | OpenSearch | Action Required |
|--------|------|-----------|-----------------|
| **Query Language** | URL parameters (q=, defType=) | JSON Query DSL | Rewrite all queries |
| **Clustering** | ZooKeeper external | Embedded consensus | Remove dependency; add observability |
| **Relevance** | TF-IDF by default | BM25 by default | A/B test 2-4 weeks; may accept difference |
| **Shards** | Can co-locate primary+replica | Cannot co-locate | Provision 2x more nodes |
| **Schema** | Mutable, live updates | Immutable after creation | Plan carefully before index creation |
| **Commits** | Soft/hard commits explicit | Refresh_interval (seconds) | Configure per use case |
| **Facets** | Special facet API | Aggregations API | Rewrite all faceted queries |
| **Monitoring** | Built-in Admin UI | Requires Dashboards | Set up additional infrastructure |

---

## Estimated Migration Timeline

- **Planning & Design**: 2-3 weeks
- **Query Translation & Schema Design**: 2-3 weeks
- **Shadow Testing (dual-write)**: 3-4 weeks
- **Gradual Traffic Shift**: 2-4 weeks
- **Validation & Fallback Window**: 4-8 weeks

**Total**: 3-4 months for production migration with safety margins.

---

## Success Criteria

- [ ] All queries translated to OpenSearch Query DSL
- [ ] Schema designed and validated with sample data
- [ ] 75-85% top-10 result overlap between Solr and OpenSearch
- [ ] Query latency (p95) within 10% of Solr baseline
- [ ] Zero data loss during cutover
- [ ] Rollback procedures tested and documented
- [ ] Monitoring/alerting in place before traffic shift
- [ ] On-call team trained on OpenSearch operations

---

## Troubleshooting Quick Links

- **Relevance Issues**: See common-pitfalls.md, Pitfall 2 (BM25 vs TF-IDF)
- **Cluster Sizing**: See common-pitfalls.md, Pitfall 1 (Shard Collocation)
- **Query Translation**: See query-syntax-mapping.md (each parser type)
- **Schema Errors**: See schema-field-type-mapping.md (field properties)
- **Connection Failures**: See common-pitfalls.md, Pitfall 11 (Connection Pooling)
- **Performance Issues**: See common-pitfalls.md, Pitfall 12 (JVM Tuning)

---

## References & Further Reading

### Official Documentation
- OpenSearch: https://opensearch.org/docs/latest/
- Apache Solr: https://solr.apache.org/guide/

### Migration Guides
- AWS Big Data Blog: https://aws.amazon.com/blogs/big-data/
- BigData Boutique: https://bigdataboutique.com/
- Elastic Migration Guide: https://www.elastic.co/blog/how-to-migrate-from-solr-to-elasticsearch

### Tools
- OpenSearch Dashboards: https://opensearch.org/docs/latest/dashboards/
- Query DSL Validator: https://opensearch.org/docs/latest/query-dsl/
- Logstash: https://www.elastic.co/logstash

---

**Last Updated**: March 2024
**Expertise Level**: Expert-level technical reference for architects and senior engineers
**Audience**: Technical teams executing multi-month production migrations
