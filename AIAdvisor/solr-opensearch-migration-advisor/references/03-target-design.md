# Target Design: OpenSearch Architecture

**Scope:** Index mapping strategy, sharding, replication, node sizing, and AWS service integration.
**Audience:** Architects, Platform Engineers.
**Last reviewed:** 2026-03-19 | **Reviewer:** [Initials]

---

## Key Judgements

- **Mapping is your schema.** In OpenSearch, the `mapping` IS your `schema.xml`. If you design a sloppy mapping, you will pay for it in storage and query latency for the life of the index.
- **Shard sizing is more important than node count.** Oversharding (too many small shards) is the #1 performance killer in OpenSearch. Aim for shard sizes between 10GB and 50GB.
- **Aliases are mandatory.** Never let an application write directly to an index name (e.g., `techproducts_v1`). Always write/read through an alias (`techproducts`). This is the only way to perform zero-downtime reindexing.
- **Avoid "The Blob".** Do not store large, unindexed fields in the document `_source` unless you absolutely need to. If you only need a field for display, consider storing it in a key-value store (like DynamoDB) and retrieving it by ID.
- **Consistency vs. Latency.** You must decide early if you need "Refresh" (NRT) or if you can tolerate a longer `refresh_interval` (which significantly boosts indexing throughput).

---

## Decision Heuristics: Architecture Planning

| Situation | Heuristic |
|:---|:---|
| **High Ingest Volume** | Set `refresh_interval` to `30s` or `-1` during bulk loads. Use `bulk` API with small batch sizes (5-10MB). |
| **Search-Heavy Load** | Use `r6g` or `r7g` instances. Prioritize `doc_values` for all sort/facet fields. |
| **Small Data (<50GB)** | 1 primary shard is plenty. Do not add shards just to "scale." |
| **Large Data (>100GB)** | Calculate shards based on target shard size (20-30GB). If you have 500GB, aim for 15-25 primary shards. |
| **New Version Upgrades** | Always plan for "Blue/Green" reindexing using an alias. Never perform in-place mapping updates. |

---

## Common Pitfalls: War Stories

- **The "Over-Sharding" Disaster:** A client with 200GB of data created 500 shards because they thought "more is faster." The cluster spent all its CPU on ZK-like internal coordination (cluster state updates) instead of searching. We reduced them to 10 shards, and latency dropped by 80%.
- **The "Dynamic Mapping" Trap:** A client relied on "Dynamic Mapping" for their new index. It worked until someone sent a malformed log file with a field name that was interpreted as a `float`, and then another log with a `string`. The index mapping "exploded," and they couldn't query the data. **Lesson:** Always use explicit, versioned mappings in production.

---

## Design Checklist (The "Golden Path")

1.  **Index Template:** Define an Index Template that covers all indices for your domain (e.g., `techproducts-*`).
2.  **Explicit Mappings:** Define every field type explicitly (`keyword`, `text`, `integer`, etc.). Use `keyword` for all facets/filters.
3.  **Analyzer Strategy:** Define your custom analyzers in the `settings` block of the template.
4.  **Alias Strategy:** Ensure the application connects to `techproducts_read` and `techproducts_write` aliases.
5.  **ISM Policy:** Define a policy that transitions data from `hot` to `warm` (if needed) or `delete` after X days.

---

## Next Steps

1.  **Map the Schema:** Translate your Solr `schema.xml` types to OpenSearch Mappings (see `schema-field-type-mapping.md`).
2.  **Define Shards:** Calculate primary shard count based on expected data volume (Target: 30GB per shard).
3.  **Draft the Template:** Create the JSON Index Template file and store it in `src/main/resources/opensearch/atlas-index.json`.
4.  **Validation:** Run `curl -X PUT` with your mapping against a test cluster to ensure the API accepts it before writing the Java/Kotlin code.
