# Technical Steering: Northstar Enterprise Demo

## Source Stack

- Solr 8.11
- Spring Boot search API
- in-house Kubernetes deployment
- one main collection: `atlas_search`
- schema-based indexing with `copyField`, dynamic fields, and eDisMax query construction

## Target Stack

- Amazon OpenSearch Service 2.x
- private VPC deployment
- IAM/SigV4 authentication for application access
- OpenSearch Dashboards for inspection and debugging
- Spring Boot application layer for the demo API and migration tooling

## Technical Decisions

1. Use a reduced demo corpus rather than a full-volume migration.
2. Model one OpenSearch index for the phase-one demo, with aliases from the start.
3. Preserve entitlement and region constraints using `bool.filter`.
4. Rebuild Solr `copyField` behavior with `copy_to` and selective multi-fields.
5. Reimplement freshness ranking with `function_score`, not index-time score hacks.
6. Treat any Solr collapse/grouping logic as a redesign area rather than a direct port.

## Target Non-Goals

- no attempt to mirror Solr internals exactly
- no unsupported OpenSearch feature workarounds solely for parity theater
- no production-scale shard tuning in the first demo pass

## Initial Target Topology

- 1 OpenSearch domain
- 2 data nodes for demo HA realism
- 1 dedicated index alias for reads
- 1 write alias reserved for future reindex/versioning pattern

## Risks To Manage

- undocumented query logic hidden in the application service
- overbroad field mapping from legacy Solr schema
- access-control mistakes during query translation
- relevance drift from TF-IDF to BM25 defaults

## Demo Verification Focus

- result overlap for the top sample queries
- correctness of entitlement filters
- facet correctness for product line, region, and document type
- reasonable end-to-end latency in the demo environment
