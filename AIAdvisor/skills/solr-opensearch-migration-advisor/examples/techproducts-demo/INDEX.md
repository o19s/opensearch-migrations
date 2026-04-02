# Techproducts Demo: Complete Specification Index

This directory contains **7 complete Kiro-format specification documents** for migrating the Apache Solr techproducts collection to AWS OpenSearch Service 2.x.

## Quick Navigation

| Document | Lines | Purpose | Read When |
|----------|-------|---------|-----------|
| **README.md** | 102 | Overview, complexity score, how to use all files | First — orientation |
| **steering/product.md** | 129 | Project goal, scope, success criteria, decisions | Planning phase |
| **steering/tech.md** | 105 | Stack details, compatibility matrix, risks | Technical lead |
| **steering/structure.md** | 234 | Project layout, Spring Boot organization, class design | Architecture |
| **requirements.md** | 356 | 17 user stories (EARS format) with acceptance criteria | Requirements phase |
| **design.md** | 714 | Index mapping (JSON), query translations, architecture | Design phase |
| **tasks.md** | 355 | 22 implementation tasks in 5 phases with estimates | Execution |

**Total: 1,995 lines | 88 KB on disk**

---

## Reading Paths

### Path 1: First-time Solr→OpenSearch migrator (1-2 hours)
1. README.md — understand what this is
2. steering/product.md — scope and goals
3. steering/tech.md — what you're migrating to/from
4. steering/structure.md — how the app is organized
5. design.md → "Index Mapping" section only — see what fields map to what
6. requirements.md → skim the requirements table

### Path 2: Technical architect (2-3 hours)
1. steering/product.md — full review
2. steering/tech.md — full review, especially compatibility matrix
3. design.md — all three main sections (mapping, queries, architecture)
4. tasks.md → dependencies graph only
5. requirements.md → acceptance criteria summary

### Path 3: Implementation team lead (3-4 hours)
1. README.md — full
2. steering/structure.md — full (project layout)
3. design.md — full (queries matter for implementation)
4. tasks.md — full (phases, estimates, dependencies)
5. requirements.md → as reference for acceptance criteria during development

### Path 4: QA/validation engineer (2-3 hours)
1. requirements.md — full
2. design.md → "Query Architecture" section + "Relevance Baseline"
3. tasks.md → Phase 4 (Testing) + Phase 5 (Validation)
4. README.md → complexity score & success metrics

### Path 5: DevOps/infrastructure (1-2 hours)
1. steering/tech.md → AWS section
2. steering/structure.md → deployment section
3. tasks.md → Phase 1 (Setup)
4. design.md → "Index Mapping" + "Index Settings"

---

## Core Concepts

### The 7 Sample Products (Reference Data)

All specs use these exact products for examples and testing:

1. **SP2514N** — Samsung SpinPoint hard drive, $92, in stock
2. **6H500F0** — Maxtor hard drive, $350, out of stock
3. **IW-02** — iPod with video, $399, out of stock
4. **F8V7067-APL-KIT** — Belkin iPod cable, $19.95, out of stock
5. **MA147LL/A** — Apple 60GB iPod, $399, in stock
6. **0579B002** — Canon camera, $210, out of stock
7. **9885A004** — Canon lens, $479.95, in stock

### Schema (15 explicit fields + 7 dynamic patterns)

| Solr Type | OpenSearch Type | Example Fields |
|-----------|-----------------|----------------|
| String | keyword | id, manu, manu_exact, cat |
| TextField | text | name, features, description, comments |
| pfloat | float | weight, price |
| pint | integer | popularity |
| pdate | date | manufacturedate_dt |
| boolean | boolean | inStock |
| LatLonPointSpatialField | geo_point | store |

**Dynamic patterns:** `*_s` (keyword), `*_i` (int), `*_f` (float), `*_l` (long), `*_b` (bool), `*_t` (text), `*_dt` (date), `*_p` (geo)

### Success Criteria (From requirements.md)

✓ Keyword search returns relevant results (top-10 overlap ≥ 80%)
✓ Filters (by stock, price, category) reduce results correctly
✓ Facets return counts matching Solr exactly
✓ Geo search executes without error
✓ All 7 documents index successfully
✓ Query response time < 100ms for all patterns

---

## Implementation Roadmap

| Phase | Duration | Deliverables | Owner |
|-------|----------|--------------|-------|
| **1. Setup** | 3 days | AWS domain, index mapping, analyzer config | Infrastructure |
| **2. Indexing** | 3 days | Solr exporter, bulk loader, repository | Platform engineers |
| **3. Queries** | 6 days | 8 query patterns, facets, geo search | Search engineers |
| **4. Testing** | 4 days | Unit tests, integration tests, validation | QA + Search team |
| **5. Validation** | 2 days | Documentation, runbook, sign-off | Everyone |
| **TOTAL** | **~2 weeks** | Complete migration demo | Cross-functional team |

---

## Design Highlights

### Index Mapping (Excerpt)

The mapping JSON (complete in design.md) handles:
- **copyField patterns** via `copy_to` (name, features, manu, cat → _text_)
- **Multi-fields** for both text and exact match (cat → cat.text + cat.keyword)
- **Dynamic templates** replacing Solr's `*_s`, `*_i`, etc. patterns
- **Custom analyzers** with index/query separation (synonym expansion at query time)

### Query Translations (8 examples)

Each Solr query is translated to Query DSL with exact expected results:

1. Keyword search (eDisMax) → multi_match
2. Stock filter (fq=inStock:true) → bool.filter
3. Price range filter → range query
4. Category facets → terms aggregation
5. Stock facets → terms aggregation (boolean)
6. Price range facets → range aggregation
7. Geo search (geofilt) → geo_distance filter
8. Combined filters + facets → nested bool query

### Architecture Pattern

Simple, single-pass reindex:

```
Solr → SolrExporter → ProductDocument list 
                          ↓
                  MigrationService
                          ↓
                   OpenSearch bulk API
                          ↓
                   Verification (count == 7)
```

No dual-write, no shadow reads — appropriate for a learning example.

---

## Key Files for Copy-Paste

### 1. Complete OpenSearch Mapping (design.md)
~150 lines of production-ready JSON. Use directly via:
```bash
curl -X PUT https://your-opensearch-domain.com/techproducts/_mapping \
  -H 'Content-Type: application/json' \
  -d @mapping.json
```

### 2. Kotlin ProductDocument Class (structure.md)
Template for @Document annotation and field mappings. Modify for your Solr schema.

### 3. All 8 Query Patterns (design.md)
Copy OpenSearch Query DSL blocks directly into your SearchService implementation.

### 4. Spring Boot build.gradle.kts (structure.md)
Dependencies list for OpenSearch client, Spring Data, AWS SDK, TestContainers.

### 5. Task Checklist (tasks.md)
Copy into Jira or GitHub Projects for sprint planning.

---

## Testing & Validation

### Unit Tests
- ProductSearchService (mock repository, test query logic)
- SolrExporter (parse JSON, transform to ProductDocument)

### Integration Tests (with TestContainers)
- ProductRepository (CRUD operations, finders)
- Full migration flow (index creation → bulk load → queries)
- All 8 query patterns against live OpenSearch container

### Spot-Check Validation
- Compare Solr vs OpenSearch results for each query pattern
- Verify top-10 overlap ≥ 80%
- Compare facet counts (must match exactly)

---

## Adapting to Your Own Migration

When you use this as a template for a *different* Solr collection:

1. **Replace field names** — keep the pattern (explicit + dynamic)
2. **Adjust complexity score** — depends on your features (nested? CDCR? custom analyzers?)
3. **Extend mapping** — copy the template, add your fields
4. **Adapt query patterns** — use these 8 as reference for your patterns
5. **Expand task list** — estimate based on data volume and team size

**Complexity scoring:**
- 2/5 (like techproducts): standard fields, no special features
- 3/5: nested docs, custom analyzers, complex faceting
- 4/5: CDCR, atomic updates, streaming expressions, large scale
- 5/5: all of above + political/organizational complexity

---

## Methodology

All specifications follow **O19s Search Engine Migration Consulting Playbook**:

1. **Scope before design** (steering docs first)
2. **Requirements before implementation** (EARS format, acceptance criteria)
3. **Design before coding** (mappings, queries, architecture)
4. **Implementation phases** (setup → indexing → queries → testing → validation)
5. **Experiment-driven** (measure, don't guess; baseline before tuning)
6. **Knowledge transfer** (document everything; enable client to sustain)

---

## Support & Questions

For questions about:

- **What is this?** → README.md
- **Should we do this?** → steering/product.md
- **What are we building?** → requirements.md
- **How do we build it?** → design.md
- **What's the plan?** → tasks.md
- **How do we structure the code?** → steering/structure.md
- **What are the technical tradeoffs?** → steering/tech.md

---

## Deliverables Summary

```
techproducts-demo/
├── README.md                         ← START HERE
├── MANIFEST.txt                      ← File overview
├── INDEX.md                          ← This file
├── steering/
│   ├── product.md                    ← Scope & goals
│   ├── tech.md                       ← Stack & decisions
│   └── structure.md                  ← Project layout
├── requirements.md                   ← 17 user stories (EARS format)
├── design.md                         ← Mapping JSON + query translations
└── tasks.md                          ← 22 implementation tasks in 5 phases

TOTAL: 7 markdown files + 1 text file
       1,995 lines of specification
       88 KB on disk
       ~3-4 hours to read thoroughly
       ~2 weeks to implement
```

---

**Version:** 1.0
**Generated:** 2026-03-17
**Methodology:** OSC Search Engine Migration Consulting Playbook
**Status:** Complete, ready for implementation

For the latest version of this specification and reference implementations, see:
`/sessions/clever-affectionate-mccarthy/mnt/agent99/examples/`
