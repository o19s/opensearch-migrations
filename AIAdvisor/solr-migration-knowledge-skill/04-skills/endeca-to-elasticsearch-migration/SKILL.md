---
name: endeca-to-elasticsearch-migration
description: >
  Expert guidance for migrating Oracle Commerce Guided Search (Endeca) deployments to Elasticsearch (Self-managed or Elastic Cloud).
  Use this skill whenever someone is working on: Endeca-to-Elasticsearch migration planning; translating Endeca 
  Forge/CAS pipelines to Elasticsearch indexing; mapping Dimension/Property schemas to Elasticsearch Index Templates; 
  re-implementing Experience Manager (XMGR) logic in Elasticsearch; and handling Endeca-specific 
  features like Multi-Select OR facets, Dynamic Ranking (Thesauraus/Stopwords), and Guided Navigation.
---

# Endeca → Elasticsearch Migration Skill

## How to Use This Skill

Read the relevant reference file when the user's question falls in that domain.

| User needs | Read |
|------------|------|
| Endeca Architecture Audit (MDEX, Forge, CAS, Dgraph) | `references/endeca-architecture-audit.md` |
| Pipeline Translation (Forge/CAS → ETL/Elasticsearch) | `references/pipeline-translation.md` |
| Dimension/Property Mapping (Schema.xml equivalents) | `references/dimension-mapping.md` |
| Experience Manager (XMGR) → Rule Engine Mapping | `references/experience-manager-transition.md` |
| Multi-Select OR / Guided Navigation in Elasticsearch | `references/query-syntax-mapping.md` |

---

## Core Mental Model

Endeca is a **C++/Proprietary** system built for high-performance guided navigation. Elasticsearch is a **Java/Lucene-based** system built for search relevance and scale.

**Full refactor is mandatory** because:
- **No 1:1 Pipeline:** Endeca's "Forge" uses a sequential, file-based pipeline (XML/JavaScript). Elasticsearch needs a modern ETL (Logstash, Python, or Custom API).
- **The "Dimension" vs "Field":** Endeca's guided navigation (Dimensions) is far more rigid and powerful than Elasticsearch "Facets." You must re-design your "Navigation Tree."
- **MDEX vs Dgraph:** Endeca's Dgraph is an in-memory index. Elasticsearch stores on disk (with OS cache). Expect different performance and scaling profiles.
- **Rules Engine:** Endeca's "Thesaurus" and "One-way Synonyms" have strict behaviors that Elasticsearch handles through its own Analyzers and Query DSL.

---

## Critical Differences Quick Reference

| Concept | Endeca | Elasticsearch | Migration note |
|---------|--------|-----------|----------------|
| Ingest Tool | Forge / CAS | Logstash / Spark / API | Endeca's file-based XML ingest is dead. |
| Record Store | Record Store (CAS) | Document / Index | Elasticsearch "Documents" are more flexible. |
| Navigation | Dimensions | Facets / Aggregations | Multi-Select OR is natively harder in Elasticsearch. |
| Index Unit | MDEX (Dgraph) | Shard / Replica | Scaling is horizontal in Elasticsearch. |
| Page Config | Experience Manager (XMGR) | Custom Logic / CMS | Elasticsearch doesn't have a built-in "Page Builder." |
| Relevance | Dynamic Ranking (Relevance Ranking) | Query DSL + Function Score | Endeca's "FirstMatch" strategy is unique. |

---

## Migration Phase Overview

```
Phase 1: Pipeline Audit (2–4 wks)
  ├─ Audit: Forge XML pipelines, CAS Record Stores, Property/Dimension definitions
  └─ Design: New ETL pipeline (e.g., Python/Logstash) and Elasticsearch Mappings

Phase 2: Navigation Redesign (2–4 wks)
  ├─ Map Endeca Dimensions to Elasticsearch Aggregations
  └─ Implement "Multi-Select OR" logic (requires complex Bool filter/should)

Phase 3: Experience Manager (XMGR) Port (4–8 wks)
  ├─ Inventory XMGR rules, triggers, and content zones
  └─ Re-implement as "Search Rules" or Custom Middleware (e.g., Quepid/Search-Collector)

Phase 4: Dual-Write & Baseline (2–4 wks)
  ├─ Index to both Endeca (via CAS) and Elasticsearch
  └─ Compare relevance: Endeca's "FirstMatch" vs Elasticsearch "BM25"

Phase 5: Cutover (1–2 wks)
  └─ Traffic shift, decommission MDEX/Forge, cleanup XML configs
```

> For full architectural audit detail: `references/endeca-architecture-audit.md`
