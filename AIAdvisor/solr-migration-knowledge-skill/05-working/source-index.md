# Source Index: Solr → OpenSearch Migration Corpus
**Last updated:** 2026-03-19
**Total files:** ~60 | **Status:** ✅ Current

---

## 00-project — Kiro Steering Documents
These are the Kiro steering docs that persist across sessions and provide project context.

| File | Description | Status |
|------|-------------|--------|
| `product.md` | Project vision, success criteria, constraints, stakeholder concerns | ✅ |
| `tech.md` | Source/target stack, build tooling, key decisions | ✅ |
| `structure.md` | Repository layout and governance boundaries | ✅ |

---

## 01-sources — Reference Material
The core knowledge library.

### 01-sources/opensearch-fundamentals
Foundational concepts. 
- `intro-to-opensearch.md`, `mappings.md`, `create-index-api.md`, `ingest-data.md`, `index-management.md`, `spring-boot-kotlin-opensearch-client.md`, `opensearch-query-dsl-kotlin-examples.md`.

### 01-sources/opensearch-migration
The migration-specific technical library.
- `aws-solr-migration-blog.md`, `query-syntax-mapping.md`, `schema-field-type-mapping.md`, `common-pitfalls.md`, `solrcloud-practitioners-guide.md`.

### 01-sources/opensearch-best-practices
Operational readiness.
- `aws-operational-best-practices.md`, `cluster-sizing-and-design.md`, `indexing-speed-tuning.md`, `search-relevance-tuning.md`, `ism-lifecycle-management.md`, `performance-testing.md`.

### 01-sources/samples
Sample code, app implementations, and enterprise search scenarios.
- `northstar-enterprise-app/`: Full Kotlin/Spring Boot reference application.
- `northstar-enterprise-search/`: Industrial enterprise migration sample data (schema, queries, docs).

---

## 02-playbook — OSC Consulting Methodology
The source of truth for engagement structure.

| File | Description |
|------|-------------|
| `pre-migration-assessment.md` | Assessment framework for new clients |
| `migration-roles-matrix.md` | Tiered role definition (Strategic vs. Tactical) |
| `relevance-methodology.md` | Relevance-first tuning approach |
| `team-and-process.md` | Roles, communication, and meeting cadences |

---

## 03-specs — Kiro Specs (Output)
Migration artifacts generated per client.

| Folder | Description |
|------|-------------|
| `techproducts-demo/` | The canonical worked example (Use as template) |
| `northstar-enterprise-demo/` | Industrial enterprise migration worked example |
| `drupal-solr-opensearch-demo/` | Drupal-specific migration worked example |

---

## 04-skills — Agent Expertise Layer
The packaged skill and its internal reference knowledge.

| File | Description |
|------|-------------|
| `SKILL.md` | Routing layer for the AI Advisor |
| `references/` | 7 expert content chunks (see `05-working/CONTENT-STRUCTURE.md`) |

---

## tools — Automation Engine
Core migration scripts.

| File | Description |
|------|-------------|
| `migration/solr_to_opensearch.py` | Automated schema translation, reindexing, and smoke testing |

---

## 05-working — Coordination
Project management and contribution guidelines.

| File | Description |
|------|-------------|
| `CONTENT-STRUCTURE.md` | Master tracking for the 7 expert content chunks |
| `CONTRIBUTOR-GUIDE.md` | Contribution rules and "Write from memory first" mandate |
