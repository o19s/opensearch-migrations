# Product Steering: Techproducts Demo Migration

## Project Goal

Migrate the Solr **techproducts demo collection** to **AWS OpenSearch Service 2.x** as a teaching example and proof-of-concept. The goal is **not production operation** but **learning and validation of the migration process**.

This demonstrates:
- How search parity is validated (same queries, measured results)
- What a complete migration spec looks like
- How to approach a real customer migration

## Scope

### In Scope

**Collection:** Solr techproducts demo
- 7 sample product documents
- Real-world schema (text, keyword, numeric, date, geo fields)
- Realistic queries (eDisMax, facets, filters, geo)
- Standard analyzers (tokenization, lowercasing, stop words, synonyms)

**Target:** AWS OpenSearch Service 2.x (managed, SigV4 auth)

**Features to migrate:**
1. **Keyword search** — multi-field search (name, features, category) with relevance ranking
2. **Faceted navigation** — category counts, inStock boolean, price range buckets
3. **Filtered search** — by price range, stock status, category, and location (geo)
4. **Geo search** — find products within N km of a point
5. **Bulk indexing** — load all documents efficiently
6. **Query equivalence** — verify each Solr query produces comparable results in OpenSearch

### Out of Scope

**These are intentionally excluded to keep scope manageable:**
- Document parsing (Tika demo fields like `content`, `author`, `resourcename`)
- Payload scoring
- Advanced spellcheck or suggester configuration
- Cross-datacenter replication (CDCR)
- Atomic updates
- Solr-specific features (streaming expressions, MLT handler complexity)
- Operational automation (rollback monitoring, circuit breakers)
- Multi-language support or complex custom analyzers
- A/B testing or relevance metrics tooling

**Why excluded:** These are valuable in production but orthogonal to the core migration pattern. Add them iteratively after the proof-of-concept succeeds.

## Success Criteria

The migration is successful when:

1. **Schema Fidelity** ✓
   - All fields present in OpenSearch with correct types
   - manu_exact (copyField pattern) implemented as .keyword sub-field
   - _text_ catchall reconstructed with copy_to
   - Dynamic field patterns (*_s, *_i, *_f, etc.) handled with dynamic_templates

2. **Query Equivalence** ✓
   - Keyword search (eDisMax pattern) → multi_match equivalent produces top-10 overlap > 80%
   - Faceted search (category, inStock, price range) returns same counts ±1%
   - Filter queries (price range, inStock) reduce result set correctly
   - Geo queries return products within specified distance

3. **Indexing** ✓
   - All 7 documents successfully indexed
   - Document count matches source: `count(OpenSearch) == 7`
   - Fields stored and retrievable

4. **No Regressions** ✓
   - Query response time < 100ms for all patterns
   - No errors or timeouts
   - All facet queries return non-empty results
   - Geo search returns expected products

## Key Decisions Made

1. **Single-pass indexing, no dual-write** — for a demo, export from Solr once, load to OpenSearch. No need to maintain both during migration.

2. **AWS OpenSearch Service (managed)** — uses SigV4 authentication; VPC deployment assumed; Dashboards included.

3. **Spring Boot 3.5 + Kotlin** — modern stack, leverages Spring Data OpenSearch, good for teaching integration patterns.

4. **No custom analyzers** — use OpenSearch standard analyzer with synonym graph filter (equivalent to Solr text_general).

5. **No data persistence concerns** — demo collection; can be re-indexed at will. Production migrations require snapshot strategies.

## Open Decisions (For Real Migrations)

These questions are decided *per-project*; documenting them for future migrations:

- **Shard count:** Techproducts uses 1 shard (demo). Real collections: estimate 20-40 GB per shard.
- **Replica count:** Techproducts uses 1 replica (HA demo). Production: 2-3 for resilience.
- **Index naming:** One index per collection here. Real systems: versioning (`products_v1`, `products_v2`) for zero-downtime reindexing.
- **Refresh interval:** Hardcoded to 1s for demo. Production: tune based on indexing volume and latency SLA.
- **BM25 parameters:** Using defaults. Real migrations: tune `k1` and `b` based on relevance baselines.

## Metrics to Measure

**Baseline (Solr):**
- Query response time (p50, p99)
- Top-10 result composition for each query pattern

**Post-Migration (OpenSearch):**
- Query response time (p50, p99) — should match ±10%
- Top-10 result composition — should match ±5%
- Document count — must match exactly
- Facet counts — must match exactly

**Definition of parity:**
- Same queries executed against both systems produce results with > 80% top-10 overlap
- Facet counts match within rounding error
- No query timeouts or errors

## Delivery

**Format:** All specifications below + Spring Boot/Kotlin reference implementation

**Deliverable checklist:**
- [ ] Steering docs (product, tech, structure)
- [ ] Requirements (EARS format, acceptance criteria)
- [ ] Design spec (mapping, queries, architecture)
- [ ] Task checklist (implementation phases)
- [ ] Reference code (Spring Boot app with example queries)
- [ ] Test data (7 products, representative queries)

---

**Owner:** Search Migration Team
**Status:** Planning
**Target Date:** 2026-04-14 (one sprint)
