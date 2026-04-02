# Migration Intake Worksheet

**Session:** {session_id}
**Generated:** {timestamp}
**Status:** {intake_status}

---

## Quick Facts

| Item | Value |
|------|-------|
| Solr version | {solr_version} |
| Collection(s) | {solr_collection} |
| Document count | {solr_num_docs} |
| Cluster topology | {node_count} nodes, {shard_count} shards, {replica_factor}x replicas |
| Target platform | {target_platform} |
| Migration driver | {migration_driver} |

## Content Sources

| Content type | Source system | Indexing method | Enrichments | Rebuild possible? |
|--------------|-------------|-----------------|-------------|-------------------|
| {row per content type discovered} | | | | |

## Schema Summary

| Metric | Count |
|--------|-------|
| Field types | {field_type_count} |
| Fields | {field_count} |
| Dynamic fields | {dynamic_field_count} |
| Copy fields | {copy_field_count} |
| Custom analyzers | {analyzer_count} |

**Schema source:** {schema_source}
**Conversion status:** {schema_migrated}

## Query Profile

| Metric | Value |
|--------|-------|
| Query types in use | {query_types} |
| Queries translated | {queries_translated} |
| Query incompatibilities | {query_incompatibility_count} |

## Customizations Inventory

| Feature | In use? | OpenSearch equivalent | Redesign needed? |
|---------|---------|---------------------|-----------------|
| Custom request handlers | {yes/no} | {equivalent} | {yes/no} |
| Custom plugins (Java) | {yes/no} | {equivalent} | {yes/no} |
| Streaming expressions | {yes/no} | No equivalent | Yes |
| CDCR | {yes/no} | Cross-cluster replication | Partial |
| Data Import Handler | {yes/no} | Logstash / custom pipeline | Yes |
| Atomic updates | {yes/no} | Partial update API | Partial |
| Field collapsing | {yes/no} | Collapse search | Partial |

## Security & Access Control

| Item | Value |
|------|-------|
| Auth method | {auth_method} |
| Document-level security | {dls_in_use} |
| Field-level security | {fls_in_use} |

## Open Questions

| # | Question | Owner | Priority | Status |
|---|----------|-------|----------|--------|
| {auto-numbered from session gaps} | | | | |

---

*This worksheet is auto-generated from session state.  Missing values indicate
information not yet gathered.  Re-run the advisor to refresh.*
