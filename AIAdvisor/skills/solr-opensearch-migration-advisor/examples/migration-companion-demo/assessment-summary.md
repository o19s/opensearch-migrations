# Assessment Summary

**Engagement:** Northwind Commerce search migration
**Date:** 2026-03-20
**Prepared by:** Agent99 companion demo
**Status:** Ready for design and staged validation planning

## Scope

- Source: SolrCloud serving product search and autocomplete
- Target: AWS OpenSearch Service 2.x
- In scope:
  - catalog search
  - category browse
  - autocomplete
  - filter/facet navigation
- Out of scope:
  - recommendations
  - analytics and reporting queries
  - legacy back-office admin search

## Observed Source Characteristics

- 3 Solr collections with shared configset and collection-specific boost rules
- eDisMax query layer with `qf`, `pf`, `mm`, `bq`, and `fq` heavy usage
- synonym files managed manually outside normal application deploy flow
- 18M product documents, daily full feed plus near-real-time inventory deltas
- current team has no judged relevance set and no stable query regression harness

## Migration-Relevant Findings

- Query behavior is moderately customized but still translatable with a dedicated query abstraction layer.
- Relevance risk is high because boost rules are under-documented and current business acceptance is anecdotal.
- Operational risk is moderate because the team already mirrors traffic for observability in another subsystem.
- Data risk is moderate because inventory freshness matters within minutes during peak periods.

## Complexity Posture

**Overall complexity:** 3.5 / 5

Reasons:

- meaningful relevance tuning and merchandising rules
- no nested documents or parent/child structures
- moderate indexing freshness requirements
- multiple traffic patterns but one primary customer search experience

## Missing Evidence

- representative top-query set with volume and business priority
- explicit acceptance thresholds for search quality
- current p95/p99 latency baseline split by query class
- documented rollback owner and rollback authority

## Recommendation

Proceed to target design and validation planning, but do not approve cutover-oriented execution until:

- a judged query set exists
- traffic classes are baselined
- rollback ownership is assigned explicitly
