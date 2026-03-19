# Source Index: Solr → OpenSearch Migration Corpus
**Last updated:** 2026-03-17
**Total files:** 54 | **Total size:** ~4.5 MB
**Status legend:** ✅ Fetched from source | 📝 Written from training knowledge | 🔗 Source URL included | ⚠️ Needs manual review

---

## 00-project — Kiro Steering Documents
These are the three Kiro steering docs that persist across sessions and provide project context.

| File | Description | Status |
|------|-------------|--------|
| `product.md` | Project vision, success criteria, constraints, stakeholder concerns, phase timeline | 📝 |
| `tech.md` | Source/target stack, build tooling, key decisions made vs open | 📝 |
| `structure.md` | Multi-module Gradle layout, package structure, interface boundaries | 📝 |

**Action needed:** Review these files and update them with your actual project constraints. They are based on a generic multi-stack migration context.

---

## 01-sources/opensearch-fundamentals
Core OpenSearch concepts. Foundation reading before migration design.

| File | Description | Status |
|------|-------------|--------|
| `intro-to-opensearch.md` | Overview, architecture, features, use cases | 📝 🔗 |
| `getting-started.md` | Setup, cluster health, initial operations | 📝 🔗 |
| `mappings.md` | Field types, configuration options, best practices for data structure | 📝 🔗 |
| `create-index-api.md` | API reference, shard/replica strategy, practical examples | 📝 🔗 |
| `ingest-data.md` | Bulk API, Logstash, Beats, performance tuning | 📝 🔗 |
| `index-management.md` | ISM policies, lifecycle management, aliases | 📝 🔗 |
| `spring-boot-kotlin-opensearch-client.md` | Spring Boot 3.5+/Kotlin client setup, SigV4, TestContainers | 📝 |
| `opensearch-query-dsl-kotlin-examples.md` | 30+ Kotlin/Java code examples for all major query types | 📝 |

**Priority reads for Spring Boot/Kotlin work:** `spring-boot-kotlin-opensearch-client.md`, `opensearch-query-dsl-kotlin-examples.md`

---

## 01-sources/opensearch-migration
The core migration-specific content. Most strategically dense folder.

| File | Description | Status |
|------|-------------|--------|
| `aws-solr-migration-blog.md` | AWS blog: full refactor strategy, dual-write, query/schema migration | 📝 🔗 |
| `query-syntax-mapping.md` | Comprehensive Solr→OpenSearch query mapping with 41 sections, before/after examples | 📝 🔗 |
| `schema-field-type-mapping.md` | Field type mapping table, analyzer chains, copyField→copy_to, nested docs | 📝 🔗 |
| `common-pitfalls.md` | 12 real-world pitfalls: scoring, shard collocation, commit semantics, atomic updates | 📝 |
| `bigdata-boutique-deep-dive.md` | Architecture, queries, data strategies deep dive | 📝 🔗 |
| `bigdata-boutique-guide.md` | Elasticsearch/OpenSearch data migration guide | 📝 🔗 |
| `schema-migration.md` | Schema-focused migration reference | 📝 🔗 |
| `aws-prescriptive-guidance.md` | AWS prescriptive guidance patterns | 📝 🔗 |
| `solrcloud-practitioners-guide.md` | SolrCloud-specific migration considerations | 📝 |
| `tecracer-migration-2024.md` | 2024 practitioner experience | 📝 🔗 |
| `README.md` | Navigation guide, phase-by-phase usage, timeline estimates | 📝 |

**Priority reads for migration planning:** `aws-solr-migration-blog.md` → `common-pitfalls.md` → `query-syntax-mapping.md` → `schema-field-type-mapping.md`

---

## 01-sources/opensearch-best-practices
Production readiness and operational guidance.

| File | Description | Status |
|------|-------------|--------|
| `aws-operational-best-practices.md` | AWS official BP: sizing, storage, monitoring, slow logs | 📝 🔗 |
| `cluster-sizing-and-design.md` | Shard sizing, replica strategy, hot-warm architecture | 📝 🔗 |
| `cluster-creation.md` | Cluster creation, configuration decisions | 📝 🔗 |
| `indexing-speed-tuning.md` | Refresh interval, bulk sizing, replica=0 during indexing | 📝 🔗 |
| `search-relevance-tuning.md` | BM25 tuning, boosting, function_score patterns | 📝 🔗 |
| `ism-lifecycle-management.md` | ISM policies: rollover, read-only, delete, force merge | 📝 🔗 |
| `performance-testing.md` | OpenSearch Benchmark (Rally), performance testing methodology | 📝 🔗 |
| `prosperops-15-best-practices.md` | 15 production best practices for AWS OpenSearch | 📝 🔗 |

**Priority reads for production setup:** `aws-operational-best-practices.md` → `cluster-sizing-and-design.md` → `indexing-speed-tuning.md`

---

## 01-sources/aws-opensearch-service
AWS-specific managed service considerations.

| File | Description | Status |
|------|-------------|--------|
| `aws-opensearch-vs-self-managed.md` | Managed vs self-hosted trade-offs, cost model, version lag, FGAC | 📝 |
| `aws-opensearch-migration-service.md` | Migration tooling: Glue, Lambda, Kinesis, Data Prepper, Logstash patterns | 📝 |
| `aws-opensearch-networking-security.md` | VPC, IAM, SAML, KMS encryption, CCS, compliance | 📝 |
| `config-changes.md` | Configuration change management on AWS | 📝 🔗 |
| `domain-management.md` | Domain management operations | 📝 🔗 |
| `getting-started.md` | AWS service getting started | 📝 🔗 |

---

## 01-sources/solr-reference
Solr architecture and query reference — for accurate source-side analysis.

| File | Description | Status |
|------|-------------|--------|
| `solr-architecture-concepts.md` | SolrCloud, ZooKeeper, overseer, tlog, CDCR, operational pain points | 📝 |
| `solr-query-features-reference.md` | DisMax/eDisMax params, faceting, grouping, collapsing, RTG, atomic updates | 📝 |
| `solr-schema-concepts.md` | schema.xml, fieldType hierarchy, analyzers, dynamic fields, docValues | 📝 |

**Use these to:** audit your current Solr collections before migration, identify features that need migration attention.

---

## 01-sources/community-insights
Real-world experiences and practitioner advice.

| File | Description | Status |
|------|-------------|--------|
| `canva-migration-experience.md` | Canva's production migration: relevance regression, analyzer translation | 📝 🔗 |
| `relevance-scoring-differences.md` | TF-IDF vs BM25 deep dive, scoring migration strategy | 📝 |
| `client-library-landscape.md` | Survey of OpenSearch client libraries across languages | 📝 |
| `herodevs-should-you-migrate.md` | Decision framework: should you migrate from Solr? | 📝 🔗 |
| `opensearch-forum-solr-diffs.md` | Community-sourced list of Solr vs OpenSearch behavioral differences | 📝 🔗 |
| `opster-ilm-vs-ism.md` | ILM (Elasticsearch) vs ISM (OpenSearch) comparison | 📝 🔗 |

---

## 02-playbook — Your Consulting Playbook
**Status: NOT EMPTY — Contains PPTX + 4 markdown files**

This folder contains the OSC consulting playbook for search engine migration.
- `OSC Playbook - Search Engine Migration.pptx` (32 slides)
- `pre-migration-assessment.md`
- `README.md`
- `relevance-methodology.md`
- `team-and-process.md`

---

## 03-specs — Kiro Specs (Output)
**Status: NOT EMPTY — Contains techproducts-demo**

This folder contains the worked example of a migration engagement spec.
- `techproducts-demo/` (9 files including steering, requirements, design, tasks)

---

## 04-skills — Agent Skills (Output)
**Status: NOT EMPTY — Packaged Agent Skill**

This folder contains the core Expertise Layer of the Advisor.
- `solr-to-opensearch-migration/SKILL.md` (Routing Layer)
- `solr-to-opensearch-migration/references/` (Distilled reference docs)

---

## Key URLs for Manual Fetching
The following high-value URLs were blocked by the egress proxy. Worth visiting manually and saving content to the appropriate folders:

### OpenSearch Official Docs (docs.opensearch.org)
- https://docs.opensearch.org/latest/migration/
- https://docs.opensearch.org/latest/query-dsl/
- https://docs.opensearch.org/latest/analyzers/
- https://docs.opensearch.org/latest/tuning-your-cluster/
- https://docs.opensearch.org/latest/im-plugin/ism/policies/

### AWS OpenSearch Service Docs
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/bp.html
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/indexing.html
- https://docs.aws.amazon.com/opensearch-service/latest/developerguide/managedomains-snapshots.html

### High-Value Community Posts
- https://bigdataboutique.com/blog/solr-to-opensearch-migration-deep-dive
- https://bigdataboutique.com/blog/schema-migration-from-solr-to-elasticsearch-opensearch-a0072b
- https://www.canva.dev/blog/engineering/migrating-from-solr-to-elasticsearch-and-their-differences/
- https://innocentcoder.medium.com/migration-of-solr-to-opensearch-a3b04ce0378f (100M doc migration)
- https://aws.amazon.com/blogs/big-data/migrate-from-apache-solr-to-opensearch/

---

## Session Notes
- **2026-03-17:** Initial corpus build. All files written from training knowledge due to egress proxy blocking direct fetches. Source URLs included in each file for verification.
- **Next session priorities:** (1) Add your consulting playbook to `02-playbook/`, (2) Review/correct `00-project/` steering docs, (3) Begin skill synthesis
