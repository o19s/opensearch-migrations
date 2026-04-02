# Source Index: Solr → OpenSearch Migration Corpus
**Last updated:** 2026-03-19
**Tracked files:** 174
**Status:** High-level map, manually maintained

---

## Purpose

This is a lightweight index of the repo's major content areas.
It is not a file-by-file manifest. For exact inventory, use `rg --files`.

---

## project

Project steering and repo navigation.

- `product.md`: project vision and success criteria
- `tech.md`: technical direction and constraints
- `structure.md`: workspace responsibilities and governance

---

## sources

Raw source library used to build the playbook and skill.

- `aws-opensearch-service/`: AWS-specific service and operational material
- `community-insights/`: field reports, blog posts, migration war stories
- `opensearch-best-practices/`: production readiness, ops, testing, tuning
- `opensearch-fundamentals/`: core APIs, mappings, indexing, client examples
- `opensearch-migration/`: Solr-to-OpenSearch technical migration references
- `samples/`: demo apps, sample schemas, sample corpora
- `solr-reference/`: Solr architecture and feature reference

Notable sample paths:
- `sources/samples/northstar-enterprise-search/`: enterprise sample source material
- `sources/samples/northstar-enterprise-app/`: Kotlin/Spring Boot demo app
- `sources/samples/drupal-solr8/`: Drupal-oriented sample schema and documents

---

## playbook

Consultant-facing methodology and assessment tools.

- `intake-template.md`: Session 1 intake
- `interview-guide.md`: Sessions 2-3 expert interviews
- `pre-migration-assessment.md`: risk framing and prerequisites
- `relevance-methodology.md`: baseline/tune/validate loop
- `migration-roles-matrix.md`: staffing tiers and responsibility coverage
- `team-and-process.md`: roles, cadence, delivery posture
- `assessment-kit/`: questionnaires, rubrics, readout templates, red-team checklist

---

## examples

Worked examples and engagement-specific output.

- `techproducts-demo/`: smallest clean worked example
- `northstar-enterprise-demo/`: more realistic enterprise worked example
- `drupal-solr-opensearch-demo/`: Drupal intake/demo package

---

## skills

Installable skill source.

- `solr-to-opensearch-migration/SKILL.md`: routing layer
- `solr-to-opensearch-migration/references/`: expert reference layer

Live numbered references:
- `01-strategic-guidance.md`
- `02-pre-migration.md`
- `03-target-design.md`
- `04-migration-execution.md`
- `05-validation-cutover.md`
- `06-operations.md`
- `07-platform-integration.md`

Supporting references:
- `consulting-methodology.md`
- `consulting-concerns-inventory.md`
- `roles-and-escalation-patterns.md`
- `migration-strategy.md`
- `aws-opensearch-service.md`
- `solr-concepts-reference.md`
- `scenario-drupal.md`
- `sample-catalog.md`

---

## tools

Local demo and bootstrap helpers.

- `tools/demo_search_stack.sh`: starts demo engines and bootstraps sample data
- `tools/bootstrap_search_demos.py`: loads Northstar sample data into OpenSearch and/or Elasticsearch

---

## working

Contributor coordination.

- `CONTENT-STRUCTURE.md`: completion map and cleanup backlog
- `DEVELOPER_GUIDE.md` (at repo root): contribution rules and context-discipline guidance
- `source-index.md`: this overview file

---

## Notes

- Some generated artifacts are still committed in sample/demo areas. See `CONTENT-STRUCTURE.md`
  for cleanup TODOs.
- If this file drifts again, keep it short rather than trying to maintain a full manifest.
