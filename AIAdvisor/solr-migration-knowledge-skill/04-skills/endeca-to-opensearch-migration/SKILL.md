---
name: endeca-to-opensearch-migration
description: >
  Expert guidance for migrating Oracle Commerce Guided Search (Endeca) deployments to AWS OpenSearch Service.
  Use this skill whenever someone is working on: Endeca-to-OpenSearch migration planning; translating Endeca 
  Forge/CAS pipelines to OpenSearch indexing; mapping Dimension/Property schemas to OpenSearch mappings; 
  re-implementing Experience Manager (XMGR) / Page Builder logic in OpenSearch; and handling Endeca-specific 
  features like Multi-Select OR facets, Dynamic Ranking (Thesauraus/Stopwords), and Guided Navigation.
---

# Endeca → OpenSearch Migration Skill

## How to Use This Skill

Read the relevant reference file when the user's question falls in that domain.

| User needs | Read |
|------------|------|
| Endeca Architecture Audit (MDEX, Forge, CAS, Dgraph) | `references/endeca-architecture-audit.md` |
| Pipeline Translation (Forge/CAS → ETL/OpenSearch) | `references/pipeline-translation.md` |
| Dimension/Property Mapping (Schema.xml equivalents) | `references/dimension-mapping.md` |
| Experience Manager (XMGR) → Rule Engine Mapping | `references/experience-manager-transition.md` |
| Multi-Select OR / Guided Navigation in OpenSearch | `references/query-syntax-mapping.md` |

---

## Core Mental Model

Endeca is a **C++/Proprietary** system built for high-performance guided navigation. OpenSearch is a **Java/Lucene-based** system built for search relevance and scale.

**Full refactor is mandatory** because:
- **No 1:1 Pipeline:** Endeca's "Forge" uses a sequential, file-based pipeline (XML/JavaScript). OpenSearch needs a modern ETL (Spark, Glue, or Custom API).
- **The "Dimension" vs "Field":** Endeca's guided navigation (Dimensions) is far more rigid and powerful than OpenSearch "Facets." You must re-design your "Navigation Tree."
- **MDEX vs Dgraph:** Endeca's Dgraph is an in-memory index. OpenSearch stores on disk (with OS cache). Expect different performance and scaling profiles.
- **Rules Engine:** Endeca's "Thesaurus" and "One-way Synonyms" have strict behaviors that OpenSearch handles through its own Analyzers and Query DSL.

---

## Critical Differences Quick Reference

| Concept | Endeca | OpenSearch | Migration note |
|---------|--------|-----------|----------------|
| Ingest Tool | Forge / CAS | Glue / Spark / API | Endeca's file-based XML ingest is dead. |
| Record Store | Record Store (CAS) | Document / Index | OpenSearch "Documents" are more flexible. |
| Navigation | Dimensions | Facets / Aggregations | Multi-Select OR is natively harder in OpenSearch. |
| Index Unit | MDEX (Dgraph) | Shard / Replica | Scaling is horizontal in OpenSearch. |
| Page Config | Experience Manager (XMGR) | Custom Logic / CMS | OpenSearch doesn't have a built-in "Page Builder." |
| Relevance | Dynamic Ranking (Relevance Ranking) | Query DSL + Function Score | Endeca's "FirstMatch" strategy is unique. |

---

## Migration Phase Overview

```
Phase 1: Pipeline Audit (2–4 wks)
  ├─ Audit: Forge XML pipelines, CAS Record Stores, Property/Dimension definitions
  └─ Design: New ETL pipeline (e.g., Python/Glue) and OpenSearch Mappings

Phase 2: Navigation Redesign (2–4 wks)
  ├─ Map Endeca Dimensions to OpenSearch Aggregations
  └─ Implement "Multi-Select OR" logic (requires complex Bool filter/should)

Phase 3: Experience Manager (XMGR) Port (4–8 wks)
  ├─ Inventory XMGR rules, triggers, and content zones
  └─ Re-implement as "Search Rules" or Custom Middleware (e.g., Quepid/Search-Collector)

Phase 4: Dual-Write & Baseline (2–4 wks)
  ├─ Index to both Endeca (via CAS) and OpenSearch
  └─ Compare relevance: Endeca's "FirstMatch" vs OpenSearch "BM25"

Phase 5: Cutover (1–2 wks)
  └─ Traffic shift, decommission MDEX/Forge, cleanup XML configs
```

> For full architectural audit detail: `references/endeca-architecture-audit.md`
