# Migration Advisor: Workspace Structure

This document describes the layout and governance of the **agent99** workspace — the knowledge base and skill for the Solr → OpenSearch Migration Advisor.

---

## Workspace Organization

```
agent99/                              ← Root workspace
├── 00-project/                       ← Project steering (this folder)
│   ├── product.md                    ← Vision, success criteria, stakeholder concerns
│   ├── structure.md                  ← This navigation document
│   └── tech.md                       ← Technical architecture decisions
│
├── 01-sources/                       ← Raw source material by topic
│   ├── aws-opensearch-service/       ← AWS-specific operational guides
│   ├── community-insights/           ← Case studies, war stories, lessons learned
│   ├── opensearch-best-practices/    ← Production patterns, tuning
│   ├── opensearch-fundamentals/      ← Core concepts, APIs
│   ├── opensearch-migration/         ← Migration guides + consumed assessment drafts
│   ├── samples/                      ← Sample apps and data (Northstar, etc.)
│   └── solr-reference/               ← Solr architecture, feature reference
│
├── 02-playbook/                      ← OSC consulting methodology
│   ├── README.md                     ← Playbook overview and contribution guide
│   ├── intake-template.md            ← Session 1: structured intake (9 blocks, ~59 questions)
│   ├── interview-guide.md            ← Sessions 2–3: expert interview + readiness gates
│   ├── pre-migration-assessment.md   ← When not to migrate, risk register, prerequisites
│   ├── relevance-methodology.md      ← Baseline→tune loop, Quepid/RRE, metrics
│   ├── migration-roles-matrix.md     ← Delivery roles and responsibilities
│   ├── team-and-process.md           ← Team roles, communication, meeting cadence
│   └── assessment-kit/               ← Reusable assessment artifacts (8 files)
│       ├── assessment-kit-index.md   ← Index and usage sequence
│       ├── architecture-option-cards.md
│       ├── artifact-request-checklist.md
│       ├── assessment-intake-questionnaire.md
│       ├── assessment-respondent-guidance.md
│       ├── risk-and-readiness-rubric.md
│       ├── strategic-readout-template.md
│       └── stump-the-chumps.md       ← Red-team checklist for design reviews
│
├── 03-specs/                         ← Output engagement specs (per-client)
│   ├── techproducts-demo/            ← Worked example (complete)
│   ├── northstar-enterprise-demo/    ← Demo engagement with intake session
│   │   ├── steering/                 ← product.md, tech.md, structure.md
│   │   ├── intake/                   ← session-01-foundation-intake.md
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── tasks.md
│   └── drupal-solr-opensearch-demo/  ← Drupal scenario demo
│
├── 04-skills/                        ← Packaged skills (installable)
│   └── solr-to-opensearch-migration/
│       ├── SKILL.md                  ← Routing layer (metadata, quick-reference)
│       └── references/               ← Expert content layer
│           ├── 01-strategic-guidance.md
│           ├── 05-validation-cutover.md
│           ├── 07-platform-integration.md
│           ├── aws-opensearch-service.md
│           ├── consulting-concerns-inventory.md
│           ├── consulting-methodology.md
│           ├── migration-strategy.md
│           ├── scenario-drupal.md
│           ├── solr-concepts-reference.md
│           └── sample-catalog.md
│
├── 05-working/                       ← Coordination and contributor workflow
│   ├── CONTENT-STRUCTURE.md          ← Chunk ownership and completion status
│   ├── CONTRIBUTOR-GUIDE.md          ← How to add/update content
│   └── source-index.md              ← Searchable index of 01-sources/ files
│
├── docker-compose.yaml               ← Local demo stacks (Solr, OpenSearch, ES)
├── README.md                         ← Root workspace overview
├── CLAUDE.md                         ← Claude Code workspace instructions
└── GEMINI.md                         ← Gemini workspace instructions
```

---

## Folder Responsibilities

### `00-project/` — Project Steering

**Purpose:** High-level "what and why" for the migration advisor *project itself* — not for any specific client engagement. These docs answer: what are we building, who is it for, and what does success look like?

**Audience:** Anyone orienting to this workspace for the first time, or AI tools that consume steering docs for context (Kiro IDE uses `steering/product.md` + `tech.md` + `structure.md` as its workspace context, similar to how `CLAUDE.md` works for Claude Code).

**Contents:**
- `product.md` — Project vision, success criteria, stakeholder concerns, non-goals. The "product charter" for the knowledge base itself.
- `tech.md` — Technical reference for the migration domain: current Solr deployment patterns, feature inventory, migration paths, client library patterns.
- `structure.md` — This file. Navigation map, folder responsibilities, governance rules.

**When to update:** When the project scope, folder structure, or governance model changes.

---

### `01-sources/` — Raw Knowledge Base

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

### `02-playbook/` — OSC Consulting Methodology

**Purpose:** Repeatable process tools for running migration engagements. This is the "how we do it" layer — practitioner-facing guides that a consultant picks up and uses during client work.

**Audience:** OSC consultants running or preparing for migration engagements.

**Contents:**
- `intake-template.md` — Session 1 structured intake guide (9 blocks, ~59 questions, watch-for signals, output tables, completion criteria)
- `interview-guide.md` — Sessions 2–3 expert interview guide (gap-fill, assumption challenge, design review, readiness scoring, readiness gates)
- `pre-migration-assessment.md` — When not to migrate, risk register, prerequisites and preparation checklists, decision heuristics
- `relevance-methodology.md` — Baseline→tune loop, Quepid/RRE workflow, metrics, judgment methodology
- `migration-roles-matrix.md` — Delivery roles and responsibilities
- `team-and-process.md` — Team roles, communication cadence, project phases
- `assessment-kit/` — Reusable assessment artifacts: architecture option cards, readiness rubric, readout template, red-team checklist, respondent guidance (8 files, indexed by `assessment-kit-index.md`)

**Governance:** Files here should meet the content quality bar defined in CLAUDE.md: Key Judgements (5–10 expert opinions), Decision Heuristics (at least 3 "if X then Y" patterns), Common Mistakes, and at least one war story. Files that merely summarize source material belong in `01-sources/`, not here.

**Relationship to `04-skills/`:** Playbook content is the primary source for several skill reference chunks. When a playbook file is updated, the corresponding skill reference may need updating too. See `02-playbook/README.md` for the specific mappings.

**When to update:** When methodology evolves, new engagement patterns emerge, or expert review adds real-world depth to draft material.

---

### `03-specs/` — Engagement-Specific Output

**Purpose:** Per-client engagement specifications — the working documents for a specific migration project. Each subdirectory is one engagement.

**Audience:** OSC consultants and client teams during active engagements.

**Contents (per engagement):**
- `steering/` — Engagement-level product, tech, and structure docs (Kiro IDE format)
- `intake/` — Session notes from client intake interviews
- `requirements.md` — User stories and functional requirements
- `design.md` — Technical architecture, schema mappings, query translations
- `tasks.md` — Implementation checklist

**Current engagements:**
- `techproducts-demo/` — Complete worked example using Solr's techproducts collection. Use as a template for new engagements.
- `northstar-enterprise-demo/` — Demo engagement for Northstar Industrial Systems. Has a completed Session 1 intake.
- `drupal-solr-opensearch-demo/` — Drupal Search API migration scenario.

**Governance:** To start a new engagement, copy `techproducts-demo/` and customize. Tag milestones with git tags (`v0.0-intake-session-NN`, `v0.1-foundation-lock`, etc.). See `consulting-methodology.md` → Session Management for the full tagging protocol.

**When to update:** During active engagements — after each client session, design review, or milestone.

---

### `04-skills/` — Packaged Expertise (Skill)

**Purpose:** The installable AI skill — the distilled, opinionated expert knowledge that an AI assistant loads to guide migration conversations. This is the product that the rest of the repository feeds.

**Audience:** AI assistants (Claude, Gemini, etc.) that consume the skill to provide migration guidance. Contributors who are building or reviewing skill content.

**Contents:**
- `SKILL.md` — Routing layer: metadata, quick-reference tables, critical gotchas, and pointers to reference files. Loaded first for fast pattern matching.
- `references/` — Expert content layer: numbered reference chunks, each ownable by one consultant. These contain the deep knowledge — heuristics, war stories, decision frameworks, translation tables.

**Planned reference chunks** (per `05-working/CONTENT-STRUCTURE.md`):
```
01-strategic-guidance.md      ← When/why/when-not to migrate
02-source-audit.md            ← Inventorying a Solr deployment
03-target-design.md           ← Designing the OpenSearch solution
04-migration-execution.md     ← Dual-write, cutover, pipelines
05-relevance-validation.md    ← Measurement, tools, go/no-go
06-operations.md              ← AWS ops, monitoring, ISM, DR
07-platform-integration.md    ← Spring Boot/Kotlin, other platforms
```

**Governance:** Reference files must meet the content quality bar (Key Judgements, Decision Heuristics, Common Mistakes, war stories). The skill is rebuilt by zipping `SKILL.md` + `references/` — see CLAUDE.md for the build command.

**When to update:** When expert knowledge is refined, new migration patterns are validated, or playbook improvements need to flow into the skill.

---

### `05-working/` — Coordination

**Purpose:** Internal tracking and contributor workflow — the "project management" layer for the knowledge base itself.

**Audience:** Contributors to the repository.

**Contents:**
- `CONTENT-STRUCTURE.md` — Map of which skill chunks are complete, in-progress, or not started. Tracks ownership and priority.
- `CONTRIBUTOR-GUIDE.md` — How to add or update content: templates, quality bar, review process.
- `source-index.md` — Searchable index of all files in the `01-sources/` corpus.

**When to update:** When content status changes (chunks started, completed, or reassigned), or when the contribution process evolves.

---

## How Content Flows Through the Workspace

```
01-sources/ (raw material)
     ↓ curate + add expert opinion
02-playbook/ (practitioner tools)
     ↓ distill into skill-sized chunks
04-skills/ (packaged expertise)
     ↓ apply to client work
03-specs/ (engagement output)
```

`05-working/` tracks the status of this flow. `00-project/` defines what the end-state should look like.

---

**Last updated**: 2026-03-19
