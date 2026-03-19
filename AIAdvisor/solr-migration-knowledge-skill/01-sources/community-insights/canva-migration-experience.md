# Canva's Migration from Solr to Elasticsearch: Production Insights

## Overview
Canva's engineering blog covers their production migration journey from Apache Solr to Elasticsearch, providing real-world lessons from migrating a large-scale search platform serving millions of users.

## Key Migration Challenges

### 1. Relevance Scoring Regressions
- Solr's default TF-IDF algorithm vs Elasticsearch's BM25 produced different relevance rankings
- Initial A/B testing revealed 3-5% relevance degradation on critical user-facing queries
- Required significant tuning of query weights and boost factors
- Solution involved building custom relevance evaluation framework to catch regressions early

### 2. Configuration and Mapping Differences
- Solr XML field configurations don't map 1:1 to Elasticsearch JSON mappings
- Field types, analyzers, and tokenization required careful translation
- Custom Solr analyzers needed equivalent implementations in Elasticsearch token filters and analyzers
- Dynamic fields and field name pattern matching differ between platforms

### 3. Query Syntax Translation
- Solr's Query Parser Syntax differs from Elasticsearch Query DSL
- Complex filter queries and faceting logic required rewriting
- DisMax parser behavior not directly equivalent to Elasticsearch's match_all and bool queries
- Testing coverage for query translation was critical—bugs only surfaced in production

### 4. Performance Under Load
- Canva used blue-green deployment approach for gradual traffic migration
- Initial Elasticsearch cluster sizing estimates were conservative; required tuning
- Shard allocation strategy, refresh rates, and merge behavior needed optimization
- Memory footprint and JVM tuning differed significantly between platforms

## Implementation Strategy

### Phased Rollout
1. **Shadow indexing**: Dual-write to both Solr and Elasticsearch during transition
2. **Read shadowing**: Route percentage of traffic to Elasticsearch while serving from Solr
3. **A/B testing**: Compare relevance quality, latency, and search quality metrics
4. **Gradual cutover**: Shift 10% → 25% → 50% → 100% traffic over 2-3 weeks

### Data Migration Pipeline
- Built ETL pipeline to reindex all documents into Elasticsearch
- Validation layer to confirm document counts, field content, and metadata integrity
- Rollback capability maintained for 72 hours post-migration
- Monitoring of indexing lag and replication status

## Operational Learnings

### Monitoring and Alerting
- Query latency p99 became more important metric than average (tail latency matters)
- Index size growth rate differed—Elasticsearch typically 10-15% larger than Solr
- JVM heap pressure required close monitoring; defaults too aggressive
- Slow query logs essential for identifying problematic queries

### Team Coordination
- Required training on Elasticsearch concepts vs Solr terminology
- Runbooks for common operational tasks (scaling, rebalancing, recovery)
- On-call procedures adapted for cluster state differences

## Key Takeaways
- **Migration is feasible but not trivial** for production Solr deployments
- **Relevance testing is non-negotiable**—user experience depends on search quality
- **Blue-green deployment** is the safest approach to minimize customer impact
- **Dual-write shadow period** allows validation before full cutover
- **Expect 2-4 week project** for medium-scale Solr deployments (100GB-1TB)

## Elasticsearch vs Solr Differences Highlighted
- **Query language**: DSL vs parser syntax
- **Scoring**: BM25 vs TF-IDF
- **Cluster management**: Different node roles and replica mechanics
- **Configuration**: JSON vs XML
- **Community**: Larger ES community but strong Solr expertise still valuable
