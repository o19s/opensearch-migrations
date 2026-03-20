# Solr → OpenSearch Migration Advisor

This repository is a documentation-first workspace for Solr-to-OpenSearch migration work.
It combines source material, consulting playbooks, an agent skill in source form, worked
example specs, and a Python helper that can translate a live Solr schema into an OpenSearch
mapping and bulk-load documents.

## Workspace Layout

```text
agent99/
├── 00-project/          Project steering (vision, architecture, this layout)
├── 01-sources/          Raw reference material by topic (~50 files)
├── 02-playbook/         OSC consulting methodology + assessment kit
├── 03-specs/            Per-client engagement specs (3 examples)
├── 04-skills/           Installable AI skill (SKILL.md + references/)
├── 05-working/          Contributor workflow and content tracking
├── docker-compose.yaml  Local demo stacks (Solr, OpenSearch, ES)
└── CLAUDE.md / GEMINI.md
```

For detailed folder responsibilities, governance rules, and how content flows between
layers, see [`00-project/structure.md`](00-project/structure.md).

## Where To Start

| You want to... | Start here |
|----------------|-----------|
| Understand the project | `00-project/product.md` |
| Contribute content | `05-working/CONTRIBUTOR-GUIDE.md` |
| See what's complete vs. missing | `05-working/CONTENT-STRUCTURE.md` |
| See a worked engagement example | `03-specs/techproducts-demo/` |
| Use the skill references directly | `04-skills/solr-to-opensearch-migration/references/` |
| Run a client intake session | `02-playbook/intake-template.md` |
| Run expert interviews (Sessions 2–3) | `02-playbook/interview-guide.md` |
| Use the assessment kit | `02-playbook/assessment-kit/assessment-kit-index.md` |

## Skill Structure

The skill has two layers:

- `SKILL.md`: routing layer with quick-reference material and file pointers
- `references/`: expert content layer

The long-term content plan is tracked in `05-working/CONTENT-STRUCTURE.md`. The planned
numbered chunks are:

```text
01-strategic-guidance.md
02-source-audit.md
03-target-design.md
04-migration-execution.md
05-relevance-validation.md
06-operations.md
07-platform-integration.md
```

## Using The Repository

### Directly in an agent or CLI

The simplest path is to run your agent inside this repository and let it read the markdown
sources directly.

### Local demo stacks

The root [`docker-compose.yaml`](docker-compose.yaml) supports three separate local workflows:

- Solr plus ZooKeeper for source-side testing
- OpenSearch plus Dashboards for the Northstar migration demo
- Elasticsearch plus Kibana for side-by-side compatibility checks

Typical startup commands:

```bash
docker compose up -d
docker compose --profile solr-init up solr-init-cm1
docker compose --profile opensearch-demo up -d
docker compose --profile elasticsearch-demo up -d
bash tools/demo_search_stack.sh both
```

Default demo endpoints:

- Solr: `http://localhost:8985/solr`
- OpenSearch: `http://localhost:9200`
- OpenSearch Dashboards: `http://localhost:5601`
- Elasticsearch: `http://localhost:9201`
- Kibana: `http://localhost:5602`

The Northstar demo app in `01-sources/samples/northstar-enterprise-app/northstar-enterprise-app/`
is already configured to use the root OpenSearch demo defaults. That means the repo-level
OpenSearch profile can stand in for the app-local compose file when you want one shared demo
stack.

For the cleanest demo setup, `tools/demo_search_stack.sh` will start the selected engine profile,
wait for cluster health, and load the shared Northstar sample corpus into OpenSearch,
Elasticsearch, or both.

### As a packaged skill

This checkout does not include a built `.skill` artifact, but the source is present in
`04-skills/solr-to-opensearch-migration/`. To package it locally:

```bash
cd 04-skills/solr-to-opensearch-migration
zip -r ../../solr-to-opensearch-migration.skill SKILL.md references/
```

## Status At A Glance

| Layer | Status |
|---|---|
| `SKILL.md` routing layer | Complete |
| `consulting-methodology.md` | Draft, needs expert review |
| `migration-strategy.md` | Draft, needs war stories |
| `aws-opensearch-service.md` | Draft, needs current-version review |
| `solr-concepts-reference.md` | Draft, needs validation |
| `01-strategic-guidance.md` | Started |
| `05-validation-cutover.md` | Started |
| `07-platform-integration.md` | Started |
| `02-playbook/` methodology | Intake + interview guides complete, assessment kit organized |
| `03-specs/techproducts-demo/` | Complete worked example |
| `03-specs/northstar-enterprise-demo/` | Session 1 intake complete |
