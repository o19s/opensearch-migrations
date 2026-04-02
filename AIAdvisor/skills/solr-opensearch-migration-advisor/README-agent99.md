# Solr → OpenSearch Migration Advisor

An AI-powered skill that provides expert guidance for migrating Apache Solr (SolrCloud)
collections to AWS OpenSearch Service. Works with **Claude Code**, **Cursor**, **Kiro**,
and any agent that supports the [Agent Skills specification](https://agentskills.io/specification).

---

## Available Skills

| Skill | Category | Description |
|-------|----------|-------------|
| **[solr-to-opensearch-migration](skills/solr-to-opensearch-migration/)** | Migration | Expert guidance for Solr → OpenSearch migration planning, execution, and validation |
| **[endeca-to-opensearch-migration](skills/endeca-to-opensearch-migration/)** | Migration | Oracle Endeca → OpenSearch migration guidance (early) |
| **[endeca-to-elasticsearch-migration](skills/endeca-to-elasticsearch-migration/)** | Migration | Oracle Endeca → Elasticsearch migration guidance (early) |

---

## Install a Skill

Install any skill into your project using [`npx skills`](https://agentskills.io):

```bash
npx skills add opensearch-project/opensearch-migrations
```

After installing, try:

> *"I'm migrating a SolrCloud cluster with 8 collections to OpenSearch — where do I start?"*

Your agent reads the skill instructions and reference files to provide expert migration guidance.

### Install in Kiro (Kiro Power)

1. Open **Kiro** → **Powers** panel → **Add Power**
2. Paste: `https://github.com/seanoc5/agent99/tree/master/kiro/solr-to-opensearch-migration`

### Install in Cursor

Clone the repo and open it in Cursor. The plugin is discovered from
`cursor/plugins/solr-to-opensearch-migration/`.

---

## Workspace Layout

This repository serves a dual purpose: **skills distribution** (the primary artifact)
and **consulting knowledge base** (the development substrate).

```text
agent99/
├── skills/              Installable skills (Agent Skills spec)
├── kiro/                Kiro Powers (POWER.md + steering/)
├── cursor/              Cursor plugins (plugin.json + skills symlink)
├── project/          Project steering (vision, architecture, this layout)
├── sources/          Raw reference material by topic
├── playbook/         OSC consulting methodology + assessment kit
├── examples/            Per-client engagement specs (4 examples)
├── working/          Content tracking and coordination
├── DESIGN.md            Architecture and design tenets
├── DEVELOPER_GUIDE.md   How to contribute
├── docker-compose.yaml  Local demo stacks (Solr, OpenSearch, ES)
└── CLAUDE.md / GEMINI.md
```

For detailed folder responsibilities, governance rules, and how content flows between
layers, see [`project/core/structure.md`](project/core/structure.md), [`project/core/opensearch-migrations-positioning.md`](project/core/opensearch-migrations-positioning.md), and [`DESIGN.md`](DESIGN.md).

## Where To Start

| You want to... | Start here |
|----------------|-----------|
| Get oriented quickly | `START-HERE.md` |
| Understand the project | `project/core/product.md` |
| See how this repo relates to upstream `opensearch-migrations` | `project/core/opensearch-migrations-positioning.md` |
| Contribute content | `DEVELOPER_GUIDE.md` |
| See what's complete vs. missing | `working/CONTENT-STRUCTURE.md` |
| See a realistic worked engagement example | `examples/northstar-enterprise-demo/` |
| See the smallest worked example | `examples/techproducts-demo/` |
| See the companion-style artifact flow | `examples/migration-companion-demo/` |
| Use the skill references directly | `skills/solr-to-opensearch-migration/references/` |
| Run a client intake session | `playbook/intake-template.md` |
| Run expert interviews (Sessions 2–3) | `playbook/interview-guide.md` |
| Use the assessment kit | `playbook/assessment-kit/assessment-kit-index.md` |
| Start from reusable companion artifacts | `playbook/assessment-kit/` |

## Supported Operating Modes

This repo supports four distinct usage modes. Calling them out explicitly avoids a lot of
confusion about what is "the product" vs what is development scaffolding.

| Mode | Primary entry point | What it is for |
|------|---------------------|----------------|
| Skill/reference mode | `skills/solr-to-opensearch-migration/` | Agent reads curated migration guidance and file pointers |
| Python core mode | `scripts/skill.py` and converter/report modules | Deterministic workflow floor without requiring full MCP orchestration |
| MCP mode | `scripts/mcp_server.py` | Tool surface for MCP-capable agent clients |
| Consultant artifact mode | `playbook/` and `examples/` | Human-led assessment, planning, review, and approval artifacts |

The repo should be understood as all four, not just one of them.

## Workflow Phases and Artifact Chain

The migration-advisor process is phase-based even when the user experiences it as a single
conversation. The durable outputs matter more than the conversational surface.

| Phase | Primary purpose | Minimum durable outputs |
|------|------------------|-------------------------|
| 1. Intake | establish scope, stakeholders, source facts, missing inputs | intake notes, artifact request list |
| 2. Assessment | identify constraints, risks, incompatibilities, readiness gaps | readiness/risk findings, consumer inventory |
| 3. Target design | map Solr behavior into OpenSearch design choices | schema/query translation findings, design decisions |
| 4. Planning | turn findings into implementation and sequencing | migration playbook, phased task plan |
| 5. Validation and approval | define go/no-go evidence and review posture | success definition, validation plan, approval record |
| 6. Deployment readiness and handoff | prepare target-team execution and cutover control | cutover checklist, operator-facing handoff artifacts |

This is the main connection point between the skill references, playbook, and worked examples
under `examples/`.

## Prerequisites and Fallbacks

For normal repository work:

- Python 3.11+ is the practical baseline
- `pytest` is the test entry point
- `mcp` is required for the MCP-server test path
- Docker is optional and used for local demo stacks, not for the core test suite
- AWS credentials are optional and only relevant for AWS-target design or deployment exercises

Fallback posture:

- if MCP is unavailable, the skill/reference path remains usable
- if an LLM is unavailable, the deterministic core still provides converter/report behavior
- if live eval scoring is unavailable, emit or review structured eval tasks/results without scoring
- if deployment details are missing, produce a deployment-readiness gap list rather than a false-ready plan

## Skill Structure

The skill has two layers:

- `SKILL.md`: routing layer with quick-reference material and file pointers
- `references/`: expert content layer (primary + secondary tiers)

### Primary References (01–07) — Core Migration Path

These cover the 80% case that applies to most engagements:

```text
01-strategic-guidance.md    — go/no-go decisions, when NOT to migrate
02-pre-migration.md         — inventorying a Solr deployment
03-target-design.md         — designing the OpenSearch solution
04-migration-execution.md   — dual-write, cutover, pipelines
05-validation-cutover.md    — relevance measurement, go/no-go gates
06-operations.md            — AWS ops, monitoring, ISM, DR
07-platform-integration.md  — Spring Boot, Python, Drupal, Rails
```

### Secondary References (08+) — Edge Cases and Long Tail

These cover the remaining 20% — obscure Solr features, uncommon configurations, and issues
that only surface in specific situations:

```text
08-edge-cases-and-gotchas.md  — 30+ gotchas with external source links
```

**Design rationale:** AI agents have limited context windows. Loading everything by default
wastes context on issues that may not apply. The SKILL.md routing layer decides which
references to load based on the user's question. Secondary references are loaded only when
the user's situation suggests edge cases are relevant (uncommon Solr features, post-migration
debugging, exhaustive risk assessment). This keeps the default experience focused while
ensuring deep coverage is available when needed.

The long-term content plan is tracked in `working/CONTENT-STRUCTURE.md`.

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

The root compose file uses the explicit project name `agent99` and repo-local default ports for
Solr and ZooKeeper so it can run alongside other local demo stacks. Override the host ports with
`ZK_HOST_PORT` and `SOLR_HOST_PORT` if needed. A starter override file is available at
`.env.example`; copy it to `.env` at the repository root to customize local port bindings.

Default demo endpoints:

- Solr: `http://localhost:18985/solr`
- OpenSearch: `http://localhost:9200`
- OpenSearch Dashboards: `http://localhost:5601`
- Elasticsearch: `http://localhost:9201`
- Kibana: `http://localhost:5602`

The Northstar demo app in `sources/samples/northstar-enterprise-app/`
is already configured to use the root OpenSearch demo defaults. That means the repo-level
OpenSearch profile can stand in for the app-local compose file when you want one shared demo
stack.

For the cleanest demo setup, `tools/demo_search_stack.sh` will start the selected engine profile,
wait for cluster health, and load the shared Northstar sample corpus into OpenSearch,
Elasticsearch, or both.

### As a packaged skill

This checkout does not include a built `.skill` artifact, but the source is present in
`skills/solr-to-opensearch-migration/`. To package it locally:

```bash
cd skills/solr-to-opensearch-migration
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
| `01-strategic-guidance.md` | Expanded RFC-aligned draft |
| `02-pre-migration.md` | Expanded RFC-aligned draft |
| `03-target-design.md` | Expanded RFC-aligned draft |
| `04-migration-execution.md` | Expanded RFC-aligned draft |
| `05-validation-cutover.md` | Expanded RFC-aligned draft |
| `06-operations.md` | Expanded RFC-aligned draft |
| `07-platform-integration.md` | Expanded RFC-aligned draft |
| `09-approval-and-safety-tiers.md` | New governance reference |
| `10-playbook-artifact-and-review.md` | New playbook/artifact reference |
| `playbook/` methodology | Intake + interview guides complete, assessment kit organized |
| `examples/techproducts-demo/` | Complete compact worked example |
| `examples/northstar-enterprise-demo/` | More realistic enterprise worked example |
| `examples/drupal-solr-opensearch-demo/` | Drupal migration intake/demo package |
| `examples/migration-companion-demo/` | Companion-style assessment, playbook, approval, and cutover artifact set |
