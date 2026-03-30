# Solr Metrics Interpretation for Migration Advisors

When a live Solr instance is available, use the inspection tools to gather metrics
and present findings tailored to the stakeholder role.

## Metric Sources

| Tool | Solr API | What It Provides |
|---|---|---|
| `inspect_solr_system` | `/admin/info/system` | Solr version, JVM version, heap size, CPU count |
| `inspect_solr_schema` | `/{collection}/schema` | Fields, field types, analyzers, copyFields |
| `inspect_solr_luke` | `/{collection}/admin/luke` | Document count, field cardinality, index size |
| `inspect_solr_metrics` | `/admin/metrics` | Cache hit rates, query/update rates, JVM heap usage |
| `inspect_solr_mbeans` | `/{collection}/admin/mbeans` | Per-handler request counts, latency, error rates |
| `inspect_solr_collections` | `/admin/collections` | Collection list, shard/replica topology |

## Traffic Thresholds

| Metric | Green | Yellow | Red |
|---|---|---|---|
| QPS (meanRate on /select) | < 100 | 100–500 | > 500 |
| Mean query latency | < 50ms | 50–200ms | > 200ms |
| Max query latency | < 1000ms | 1000–5000ms | > 5000ms |
| Error rate (errors/requests) | < 0.1% | 0.1–1% | > 1% |
| Filter cache hit ratio | > 0.9 | 0.7–0.9 | < 0.7 |
| JVM heap usage | < 70% | 70–85% | > 85% |

Green = straightforward migration. Yellow = review before migrating. Red = investigate and plan mitigation.

## How to Present Findings

### Search Engineer
- Show exact QPS, latency percentiles, and cache ratios.
- Highlight which query handlers are most active and their error rates.
- Flag any handler with latency > 200ms as needing query optimization.

### Application Developer
- Focus on which handlers are in use (maps to code paths to update).
- Show request counts per handler to help prioritize code changes.
- Flag custom handlers with the highest traffic.

### DevOps / Platform Engineer
- Lead with cluster topology: node count, shard distribution, heap sizing.
- Show JVM heap usage and CPU utilization.
- Provide concrete OpenSearch sizing recommendation (use sizing steering).
- Flag if heap is near 32GB limit.

### Data Engineer
- Focus on document count, index size, and update handler throughput.
- Show bulk indexing rate and error count.
- Estimate re-indexing time from current throughput.

### Architect
- Present aggregate risk summary: how many red/yellow/green metrics.
- Highlight any metrics that suggest the current Solr setup is under stress.
- Frame sizing recommendations as cost implications.

### Product Manager / Business Stakeholder
- Translate metrics to business terms: "Your search handles X queries per second with Y ms average response time."
- Flag risks as potential user-facing impact: "Search latency may increase during migration if not properly sized."
- Present sizing as cost estimate: "Based on current load, OpenSearch will need N nodes."

## What to Flag as Risks

- **JVM heap > 85%:** Solr is under memory pressure. OpenSearch sizing must account for this.
- **Error rate > 1%:** Existing errors may mask incompatibilities. Investigate before migration.
- **Custom handlers with > 10% of total traffic:** These are critical code paths that must be rebuilt.
- **Cache hit ratio < 0.7:** Query patterns may not benefit from caching. Review before relying on OpenSearch request cache.
- **QPS > 500:** High-traffic system requires careful cutover planning with traffic shaping.
- **Max latency > 5000ms:** Tail latency issues. May indicate problematic query patterns that should be optimized before migration.
