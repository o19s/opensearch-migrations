# Solr → OpenSearch Migration Advisor

An O19s knowledge base and installable AI skill for guiding Solr-to-OpenSearch migration engagements.  
The goal is to encode senior O19s consulting expertise: methodology, war stories, decision heuristics, etc  
The goal is to guide a technical developer, or a thoughtful non-tech employee, to get expert-quality guidance 
from an AI agent without needing a senior OSC person in the room.

**What this repo is:** structured reference content + a packaged Agent Skill  
**What it produces:** per-engagement migration specs (Kiro-format) and AI-assisted consulting guidance   
**Current state:** scaffolding and first-draft reference content complete; expert review and gap-filling underway   

---

## Workspace Layout

```
agent99/
├── 00-project/          Steering docs (project decisions, architecture, structure)
├── 01-sources/          Raw source material — AWS docs, community posts, Solr reference
│   ├── opensearch-migration/       richest folder; start here for execution patterns
│   ├── opensearch-best-practices/  production operations guidance
│   ├── aws-opensearch-service/     AWS-specific configs, networking, security
│   ├── solr-reference/             Solr architecture and feature inventory
│   ├── opensearch-fundamentals/    core OpenSearch concepts and APIs
│   └── community-insights/         real-world migration stories and war stories
├── 02-playbook/         OSC consulting playbook (PPTX) — methodology source of truth
├── 03-specs/            OUTPUT — generated engagement specs; techproducts-demo is the worked example
├── 04-skills/           The installable skill
│   └── solr-to-opensearch-migration/
│       ├── SKILL.md                routing layer (don't edit unless you own the skill)
│       └── references/             expert content layer — this is where contributors work
├── 05-working/          Coordination: CONTENT-STRUCTURE.md, CONTRIBUTOR-GUIDE.md
└── solr-to-opensearch-migration.skill   packaged, installable skill file
```

The single most important folder for contributors: `04-skills/solr-to-opensearch-migration/references/`
The single most useful read for understanding what the skill produces: `03-specs/techproducts-demo/`

---

## The Skill Architecture

The skill uses two layers:

**SKILL.md** is the routing layer — metadata, quick-reference tables, critical gotchas, and pointers to reference files. Claude loads this first and uses it for fast pattern matching.

**references/** is the expert knowledge layer — 7 numbered content chunks, each ownable by one O19s consultant. This is where methodology, Key Judgements, Decision Heuristics, and war stories live.

```
SKILL.md  →  references/01-strategic-guidance.md
              references/02-pre-migration.md
              references/03-architecture-planning.md
              references/04-migration-execution.md
              references/05-validation-cutover.md   ← highest O19s priority
              references/06-operations-tuning.md
              references/07-platform-integration.md
```

Current status of the 7 chunks is tracked in `05-working/CONTENT-STRUCTURE.md`.

---

## Skills — Useful Links

**Agent Skills (Claude Desktop / Cowork)**
Skills are structured markdown packages that Claude loads as expertise context. The `.skill` file in the repo root is the installable artifact.
- [Introducing Skills in Claude.ai](https://support.claude.ai/hc/en-us/articles/27152142241811-Introducing-Skills-in-Claude-ai) — what skills are, how they work
- [Claude Desktop](https://claude.ai/download) — install here to use the skill; Skills tab → Install from file → select `solr-to-opensearch-migration.skill`
- Skills are platform-agnostic: the same `.skill` file works in Claude Desktop, Cowork, and any other host that supports the format

**Kiro IDE**
Kiro is AWS's AI IDE (Code OSS + Claude Sonnet). It uses spec-driven development: steering docs describe the project, and spec files (requirements.md / design.md / tasks.md) drive implementation.
- [Kiro IDE](https://kiro.dev) — download and docs
- [Kiro spec format](https://kiro.dev/docs/specs/) — how requirements/design/tasks files work
- The `03-specs/techproducts-demo/` folder contains a complete Kiro spec set — copy it as a template for new engagements

**Relationship between skills and Kiro:** the SKILL.md encodes expertise that enables Claude to *generate good Kiro specs* for a specific client project. They operate at different layers — expertise vs. implementation scaffold.

**OpenSearch / AWS Reference**
- [OpenSearch documentation](https://opensearch.org/docs/latest/) — query DSL, index management, analysis
- [AWS OpenSearch Service docs](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/) — provisioned, serverless, VPC, IAM
- [AWS prescriptive guidance: Solr → OpenSearch](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-apache-solr-amazon-opensearch-service/) — the AWS official migration playbook (distilled in `01-sources/opensearch-migration/aws-prescriptive-guidance.md`)

---

## Next Steps — By Interest

### "I want to install and use the skill"

1. Install [Claude Desktop](https://claude.ai/download)
2. Open Settings → Skills → Install from file
3. Select `solr-to-opensearch-migration.skill` from this repo root
4. Start a new conversation — the skill appears in the Skills panel
5. Try: *"I have a SolrCloud 8.x cluster with 4 collections. Help me plan a migration to AWS OpenSearch."*

To rebuild the skill after edits to `04-skills/`:
```bash
cd 04-skills/solr-to-opensearch-migration
zip -r ../../solr-to-opensearch-migration.skill SKILL.md references/
```
(Or use the `package_skill.py` script if it's in your environment.)

---

### "I want to contribute expert content"

The fastest way to make this skill meaningfully better is to add O19s opinion to the reference chunks — real heuristics, real war stories, things that actually go wrong.

1. Read `05-working/CONTRIBUTOR-GUIDE.md` (5 minutes — covers the contribution workflow and quality bar)
2. Open `05-working/CONTENT-STRUCTURE.md` — find an unclaimed chunk, add your initials
3. **Write the Key Judgements section from memory first** — before re-reading sources. This is the most important instruction. Reading first produces summaries; writing from memory first produces expert knowledge.
4. Highest-priority gaps: `01-strategic-guidance.md` (when *not* to migrate) and `05-validation-cutover.md` (Quepid/RRE-based relevance measurement — core O19s methodology)

The OSC consulting playbook is at `02-playbook/OSC Playbook - Search Engine Migration.pptx` — 32 slides, primary source for Chunks 1 and 5.

---

### "I want to start a new client engagement"

1. Create a new folder: `03-specs/[client-name]/`
2. Use `03-specs/techproducts-demo/` as your template — it's a complete worked example
3. Customize: `steering/product.md` (project scope), `steering/tech.md` (source/target stack), `requirements.md` (client-specific functional requirements)
4. Open the folder in Kiro — the steering docs + spec files drive Kiro's implementation tasks
5. Optionally share the `.skill` file with the client team so their engineers get the same guidance context

The techproducts-demo covers the canonical Solr demo collection: 10 document types, standard facets, MoreLikeThis, spell checking. It's a realistic first test case if you want to demo the workflow.

---

### "I want to extend the workspace structure"

- `00-project/structure.md` — the governance doc; describes folder responsibilities, content lifecycle, naming conventions, review cycles
- `00-project/tech.md` — technical decisions made (OpenSearch version, instance types, migration tooling choices, testing strategy)
- `00-project/product.md` — a worked example of a product steering doc for a migration engagement (phases, stakeholder concerns, success criteria, rollback plan)
- Structural changes to `SKILL.md` or `CONTENT-STRUCTURE.md`: coordinate with Sean first (see `CONTRIBUTOR-GUIDE.md`)

---

### "I want to add a new platform integration"

Platform-specific integration (Spring Boot, Python FastAPI, Node.js, etc.) is intentionally out of scope for this skill — it belongs in a separate platform skill that *imports* this one as a dependency. The `01-sources/opensearch-fundamentals/` folder has Spring Boot/Kotlin and other client library examples as raw material if you want to build that.

---

## Status at a Glance

| Layer | Status |
|---|---|
| SKILL.md routing layer | ✅ Complete |
| `consulting-methodology.md` | 🟡 AI draft — needs expert review (~30 min) |
| `migration-strategy.md` | 🟡 AI draft — needs war stories |
| `aws-opensearch-service.md` | 🟡 AI draft — needs version/pricing check |
| `solr-concepts-reference.md` | 🟡 AI draft — needs complexity scoring validation |
| `01-strategic-guidance.md` | 🔴 Not started — highest priority |
| `05-validation-cutover.md` | 🔴 Not started — Quepid/RRE methodology, core O19s IP |
| `03-specs/techproducts-demo/` | ✅ Complete — 9 files, worked example |

See `05-working/CONTENT-STRUCTURE.md` for full scope, source mappings, and ownership tracking.

---

**Maintainer:** Sean O'Connor
**Coordination:** add your initials to chunks in `CONTENT-STRUCTURE.md` before starting work
