# Migration Advisor: Workspace Structure

This document describes the layout and governance of the **agent99** workspace — the knowledge base and skill for the Solr → OpenSearch Migration Advisor, including companion-style review artifacts that support planning and approval workflows.

---

## Workspace Organization

```
agent99/                              ← Root workspace
├── project/                       ← Project steering (this folder)
│   ├── product.md                    ← Vision, success criteria, stakeholder concerns
│   ├── opensearch-migrations-positioning.md ← Relationship to upstream execution framework
│   ├── structure.md                  ← This navigation document
│   └── tech.md                       ← Technical architecture decisions
│
├── sources/                       ← Raw source material by topic
│   ├── aws-opensearch-service/       ← AWS-specific operational guides
│   ├── community-insights/           ← Case studies, war stories, lessons learned
│   ├── opensearch-best-practices/    ← Production patterns, tuning
│   ├── opensearch-fundamentals/      ← Core concepts, APIs
│   ├── opensearch-migration/         ← Migration guides + consumed assessment drafts
│   ├── samples/                      ← Sample apps and data (Northstar, etc.)
│   └── solr-reference/               ← Solr architecture, feature reference
│
├── playbook/                      ← OSC consulting methodology
│   ├── README.md                     ← Playbook overview and contribution guide
│   ├── intake-template.md            ← Session 1: structured intake (9 blocks, ~59 questions)
│   ├── interview-guide.md            ← Sessions 2–3: expert interview + readiness gates
│   ├── pre-migration-assessment.md   ← When not to migrate, risk register, prerequisites
│   ├── relevance-methodology.md      ← Baseline→tune loop, Quepid/RRE, metrics
│   ├── migration-roles-matrix.md     ← Delivery roles and responsibilities
│   ├── team-and-process.md           ← Team roles, communication, meeting cadence
│   └── assessment-kit/               ← Reusable assessment artifacts (11 files)
│       ├── assessment-kit-index.md   ← Index and usage sequence
│       ├── architecture-option-cards.md
│       ├── artifact-request-checklist.md
│       ├── assessment-intake-questionnaire.md
│       ├── assessment-respondent-guidance.md
│       ├── consumer-inventory-template.md
│       ├── go-no-go-review-template.md
│       ├── risk-and-readiness-rubric.md
│       ├── strategic-readout-template.md
│       ├── success-definition-template.md
│       └── stump-the-chumps.md       ← Red-team checklist for design reviews
│
├── examples/                         ← Output engagement specs and artifact demos
│   ├── techproducts-demo/            ← Small worked example (complete)
│   ├── migration-companion-demo/     ← Assessment/playbook/approval artifact chain
│   ├── northstar-enterprise-demo/    ← Demo engagement with intake session
│   │   ├── steering/                 ← product.md, tech.md, structure.md
│   │   ├── intake/                   ← session-01-foundation-intake.md
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── tasks.md
│   └── drupal-solr-opensearch-demo/  ← Drupal scenario demo
│
├── skills/                        ← Packaged skills (installable)
│   └── solr-to-opensearch-migration/
│       ├── SKILL.md                  ← Routing layer (metadata, quick-reference)
│       └── references/               ← Expert content layer
│           ├── 01-strategic-guidance.md
│           ├── 02-pre-migration.md
│           ├── 03-target-design.md
│           ├── 04-migration-execution.md
│           ├── 05-validation-cutover.md
│           ├── 06-operations.md
│           ├── 07-platform-integration.md
│           ├── 08-edge-cases-and-gotchas.md
│           ├── 09-approval-and-safety-tiers.md
│           ├── 10-playbook-artifact-and-review.md
│           ├── aws-opensearch-service.md
│           ├── consulting-concerns-inventory.md
│           ├── consulting-methodology.md
│           ├── migration-strategy.md
│           ├── scenario-drupal.md
│           ├── solr-concepts-reference.md
│           └── sample-catalog.md
│
├── working/                       ← Coordination and contributor workflow
│   ├── CONTENT-STRUCTURE.md          ← Chunk ownership and completion status
│   └── source-index.md              ← Searchable index of sources/ files
│
├── DESIGN.md                         ← Architecture and design tenets
├── DEVELOPER_GUIDE.md                ← How to contribute content
├── docker-compose.yaml               ← Local demo stacks (Solr, OpenSearch, ES)
├── README.md                         ← Root workspace overview
├── CLAUDE.md                         ← Claude Code workspace instructions
└── GEMINI.md                         ← Gemini workspace instructions
```

---

## Folder Responsibilities

### `project/` — Project Steering

**Purpose:** High-level "what and why" for the migration advisor *project itself* — not for any specific client engagement. These docs answer: what are we building, who is it for, and what does success look like?

**Audience:** Anyone orienting to this workspace for the first time, or AI tools that consume steering docs for context (Kiro IDE uses `steering/product.md` + `tech.md` + `structure.md` as its workspace context, similar to how `CLAUDE.md` works for Claude Code).

**Contents:**
- `product.md` — Project vision, success criteria, stakeholder concerns, non-goals. The "product charter" for the knowledge base itself.
- `opensearch-migrations-positioning.md` — ADR-style note describing how `Agent99` relates to upstream `opensearch-project/opensearch-migrations`, including the recommended framing and likely integration seams.
- `tech.md` — Technical reference for the migration domain: current Solr deployment patterns, feature inventory, migration paths, client library patterns.
- `structure.md` — This file. Navigation map, folder responsibilities, governance rules.
- `../START-HERE.md` — Short onboarding path for first-time users

**When to update:** When the project scope, folder structure, or governance model changes.

---

### `sources/` — Raw Knowledge Base

**Purpose:** Curated reference material organized by topic. This is the "library" — facts, guides, and community knowledge that feeds the playbook and skill but isn't itself a practitioner tool.

**Audience:** Contributors writing playbook or skill content who need source material. Not intended to be read directly by clients or used during engagements.

**Contents:**
- `aws-opensearch-service/` — AWS-specific operational guides, networking, security, cost
- `community-insights/` — Real-world migration stories, blog posts, lessons learned
- `opensearch-best-practices/` — Production patterns, tuning, ISM, monitoring
- `opensearch-fundamentals/` — Core concepts, APIs, client libraries
- `opensearch-migration/` — Migration guides, query/schema mapping references, and consumed assessment framework drafts
- `samples/` — Sample applications and datasets (e.g., Northstar enterprise search app)
- `solr-reference/` — Solr architecture, SolrCloud, feature reference

**Governance:** Files here are raw inputs. They may be rough, incomplete, or opinionated. The quality bar is "useful as a source," not "ready to hand to a client." Consumed drafts (e.g., the original interview guide and assessment framework) are archived here after being refined into playbook tools.

**When to update:** When new source material is curated, or when draft documents are consumed into the playbook/skill and the originals need archiving.

---

### `playbook/` — OSC Consulting Methodology

**Purpose:** Repeatable process tools for running migration engagements. This is the "how we do it" layer — practitioner-facing guides that a consultant picks up and uses during client work.

**Audience:** OSC consultants running or preparing for migration engagements.

**Contents:**
- `intake-template.md` — Session 1 structured intake guide (9 blocks, ~59 questions, watch-for signals, output tables, completion criteria)
- `interview-guide.md` — Sessions 2–3 expert interview guide (gap-fill, assumption challenge, design review, readiness scoring, readiness gates)
- `pre-migration-assessment.md` — When not to migrate, risk register, prerequisites and preparation checklists, decision heuristics
- `relevance-methodology.md` — Baseline→tune loop, Quepid/RRE workflow, metrics, judgment methodology
- `migration-roles-matrix.md` — Delivery roles and responsibilities
- `team-and-process.md` — Team roles, communication cadence, project phases
- `assessment-kit/` — Reusable assessment artifacts: architecture option cards, readiness rubric, success definition, consumer inventory, go/no-go review, readout template, red-team checklist, respondent guidance (11 files, indexed by `assessment-kit-index.md`)

**Governance:** Files here should meet the content quality bar defined in CLAUDE.md: Key Judgements (5–10 expert opinions), Decision Heuristics (at least 3 "if X then Y" patterns), Common Mistakes, and at least one war story. Files that merely summarize source material belong in `sources/`, not here.

**Relationship to `skills/`:** Playbook content is the primary source for several skill reference chunks. When a playbook file is updated, the corresponding skill reference may need updating too. See `playbook/README.md` for the specific mappings.

**When to update:** When methodology evolves, new engagement patterns emerge, or expert review adds real-world depth to draft material.

---

### `examples/` — Engagement-Specific Output

**Purpose:** Per-client engagement specifications and companion-style artifact examples. This is where the repo shows what durable migration outputs should look like in practice.

**Audience:** OSC consultants and client teams during active engagements.

**Contents (per engagement):**
- `steering/` — Engagement-level product, tech, and structure docs
- `intake/` — Session notes from client intake interviews
- `requirements.md` — User stories and functional requirements
- `design.md` — Technical architecture, schema mappings, query translations
- `tasks.md` — Implementation checklist

**Current engagements:**
- `techproducts-demo/` — Complete small worked example using Solr's techproducts collection.
- `migration-companion-demo/` — Compact example showing assessment, risk, playbook, approval, and cutover artifacts for AI-assisted migration control.
- `northstar-enterprise-demo/` — More realistic enterprise demo engagement for Northstar Industrial Systems. Best starting point for a medium-complexity walkthrough.
- `drupal-solr-opensearch-demo/` — Drupal Search API migration scenario.

**Governance:** To start a new engagement, copy the closest matching example and customize it. Use `techproducts-demo/` for the smallest clean template and `northstar-enterprise-demo/` for a more realistic enterprise template. Tag milestones with git tags (`v0.0-intake-session-NN`, `v0.1-foundation-lock`, etc.). See `consulting-methodology.md` → Session Management for the full tagging protocol.

**When to update:** During active engagements — after each client session, design review, or milestone.

---

### `skills/` — Packaged Expertise (Skill)

**Purpose:** The installable AI skill — the distilled, opinionated expert knowledge that an AI assistant loads to guide migration conversations. This is the product that the rest of the repository feeds.

**Audience:** AI assistants (Claude, Gemini, etc.) that consume the skill to provide migration guidance. Contributors who are building or reviewing skill content.

**Contents:**
- `SKILL.md` — Routing layer: metadata, quick-reference tables, critical gotchas, and pointers to reference files. Loaded first for fast pattern matching.
- `references/` — Expert content layer: numbered reference chunks, each ownable by one consultant. These contain the deep knowledge — heuristics, war stories, decision frameworks, translation tables.

**Live numbered reference chunks**:
```
01-strategic-guidance.md      ← When/why/when-not to migrate
02-pre-migration.md           ← Assessment, readiness, and go/no-go posture
03-target-design.md           ← Designing the OpenSearch solution
04-migration-execution.md     ← Dual-write, cutover, pipelines
05-validation-cutover.md      ← Measurement, cutover safety, go/no-go
06-operations.md              ← AWS ops, monitoring, ISM, DR
07-platform-integration.md    ← Spring Boot/Kotlin, other platforms
09-approval-and-safety-tiers.md   ← Observe / Propose / Execute governance
10-playbook-artifact-and-review.md ← Reviewable playbook structure and approval gates
```

**Governance:** Reference files must meet the content quality bar (Key Judgements, Decision Heuristics, Common Mistakes, war stories). The skill is rebuilt by zipping `SKILL.md` + `references/` — see CLAUDE.md for the build command.

**When to update:** When expert knowledge is refined, new migration patterns are validated, or playbook improvements need to flow into the skill.

---

### `working/` — Coordination

**Purpose:** Internal tracking and contributor workflow — the "project management" layer for the knowledge base itself.

**Audience:** Contributors to the repository.

**Contents:**
- `CONTENT-STRUCTURE.md` — Map of which skill chunks are complete, in-progress, or not started. Tracks ownership and priority.
- `source-index.md` — Searchable index of all files in the `sources/` corpus.

Note: The contributor guide has been moved to `DEVELOPER_GUIDE.md` at the repo root.

**When to update:** When content status changes (chunks started, completed, or reassigned), or when the contribution process evolves.

---

## How Content Flows Through the Workspace

```
sources/ (raw material)
     ↓ curate + add expert opinion
playbook/ (practitioner tools)
     ↓ distill into skill-sized chunks
skills/ (packaged expertise)
     ↓ apply to client work and approval flows
examples/ (engagement output and artifact examples)
```

`working/` tracks the status of this flow. `project/` defines what the end-state should look like.

---

## Supported Operating Modes

To match how the repo is actually used, treat these as first-class modes:

- skill/reference mode: agent loads `skills/solr-to-opensearch-migration/`
- Python core mode: deterministic helpers in `scripts/` drive conversion, storage, and reporting
- MCP mode: `scripts/mcp_server.py` exposes the tool surface to compatible clients
- consultant artifact mode: humans use `playbook/` plus `examples/` for assessment and review

This distinction is important because not every environment will have MCP, live LLM access,
AWS access, or Docker available.

## Phase Model and Durable Outputs

Across those modes, the repo should still preserve the same migration-advisor phase model:

1. Intake and artifact collection
2. Source-system assessment
3. Target design and translation
4. Planning and implementation sequencing
5. Validation, approval, and cutover readiness
6. Deployment handoff

Each phase should have named durable outputs, not just conversation turns. The minimum expected
artifact chain is:

- intake notes and artifact-request checklist
- readiness/risk findings
- schema/query conversion findings with incompatibilities
- migration design and phased tasks
- success definition and approval/go-no-go artifacts
- cutover checklist and handoff notes

When adding new docs, examples, or automation, contributors should make the input/output
contract for the affected phase explicit.

## Manual Fallback Rule

The repo should never assume that the most automated path is the only path.

If an automated capability is unavailable:

- fall back from MCP/tool use to skill/reference guidance
- fall back from live judging to stored eval tasks/results and manual review
- fall back from deployment execution to deployment-readiness gaps and required next artifacts

That fallback behavior should be documented, not left implicit.

---

**Last updated**: 2026-03-23
