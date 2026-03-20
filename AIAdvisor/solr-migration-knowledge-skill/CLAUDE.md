# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a knowledge base for guiding Solr-to-OpenSearch migration consulting engagements.
Most of the repository is structured markdown, but this checkout also includes a small Python
migration helper and generated sample artifacts at the repo root.

## Repository Layout

```
agent99/
├── 00-project/          Steering docs (project scope, architecture, structure)
├── 01-sources/          Raw source material by topic
│   ├── opensearch-migration/       Start here for execution patterns
│   ├── opensearch-best-practices/  Production operations guidance
│   ├── aws-opensearch-service/     AWS-specific configs, networking, security
│   ├── solr-reference/             Solr architecture and feature inventory
│   ├── opensearch-fundamentals/    Core OpenSearch concepts and APIs
│   └── community-insights/         Real-world migration stories
├── 02-playbook/         OSC consulting methodology in markdown
├── 03-specs/            OUTPUT — generated engagement specs
│   └── techproducts-demo/          Complete worked example
├── 04-skills/           The installable skill
│   └── solr-to-opensearch-migration/
│       ├── SKILL.md                Routing layer (metadata, quick-reference tables)
│       └── references/             Expert knowledge layer (7 numbered content chunks)
├── 05-working/          Coordination: CONTENT-STRUCTURE.md, CONTRIBUTOR-GUIDE.md
├── VERSION                          Current skill version (semver)
├── bump-version.sh                  Bump version in VERSION + SKILL.md
├── solr_to_opensearch.py           Migration helper script
└── corpusminder_*.json/.md         Generated sample artifacts
```

## Key Files to Understand

| Purpose | File |
|---------|------|
| Skill routing layer | `04-skills/solr-to-opensearch-migration/SKILL.md` |
| Content contribution workflow | `05-working/CONTRIBUTOR-GUIDE.md` |
| Chunk ownership and status | `05-working/CONTENT-STRUCTURE.md` |
| Worked example of skill output | `03-specs/techproducts-demo/` (9 files) |
| Methodology source | `02-playbook/` markdown files |

## Building the Skill

To rebuild the `.skill` file after edits to `04-skills/`:

```bash
cd 04-skills/solr-to-opensearch-migration
zip -r ../../solr-to-opensearch-migration.skill SKILL.md references/
```

## Skill Architecture

The skill uses two layers:

**SKILL.md** — routing layer with metadata, quick-reference tables, critical gotchas, and pointers to references. Claude loads this first for fast pattern matching.

**references/** — expert knowledge layer with 7 numbered content chunks, each ownable by one consultant:
- `01-strategic-guidance.md` — when/why/when-not-to migrate
- `02-source-audit.md` — inventorying a Solr deployment
- `03-target-design.md` — designing the OpenSearch solution
- `04-migration-execution.md` — dual-write, cutover, pipelines
- `05-relevance-validation.md` — measurement, tools, go/no-go (highest O19s priority)
- `06-operations.md` — AWS ops, monitoring, ISM, DR
- `07-platform-integration.md` — Spring Boot/Kotlin (and other platforms)

The current committed references are a smaller draft/supporting set; use
`05-working/CONTENT-STRUCTURE.md` to distinguish planned files from files that already exist.

## Content Quality Bar

Reference files must have:
- **Key Judgements**: 5-10 genuine expert opinions (not neutral summaries)
- **Decision Heuristics**: At least 3 "if X, then Y" patterns
- **Common Mistakes**: Real things that actually go wrong
- At least one war story or concrete example

Files that simply summarize source documents are **not done**.

## Writing Content

When contributing to skill chunks:
1. **Write Key Judgements from memory first, before re-reading sources** — this produces expert knowledge, not summaries
2. Claim a chunk in `05-working/CONTENT-STRUCTURE.md` before starting
3. Follow the markdown template in `05-working/CONTRIBUTOR-GUIDE.md`
4. Update status in `CONTENT-STRUCTURE.md` when done

## Versioning

The skill version lives in two places, kept in sync:
- `VERSION` (repo root) — single-line semver, source of truth
- `version:` field in `04-skills/solr-to-opensearch-migration/SKILL.md` frontmatter

**To bump:** `./bump-version.sh 0.3.0`

**Output artifacts must include the version.** When generating specs in `03-specs/`, stamp
the skill version in the MANIFEST.txt header and README.md frontmatter, e.g.:
```
Skill-Version: 0.2.1
```

## Creating Client Engagements

1. Create folder: `03-specs/[client-name]/`
2. Use `03-specs/techproducts-demo/` as template
3. Customize: `steering/product.md` (scope), `steering/tech.md` (stack), `requirements.md` (client requirements)
4. Open in Kiro IDE — steering docs + specs drive implementation

## Express Mode

The skill supports an "express" (YOLO) mode that generates a complete migration spec from
minimal input using expert defaults. See `Express Mode (YOLO)` section in SKILL.md for full
rules. Key points:
- Every assumption marked `[ASSUMED: ...]` inline
- Output banner warns this is assumption-driven
- Full spec package generated (same structure as `03-specs/techproducts-demo/`)
- Assumptions summary with risk levels in README.md

## Domain Context

**Solr → OpenSearch migration** involves:
- Query translation: DisMax/eDisMax → Query DSL
- Schema translation: schema.xml → JSON index mappings
- Relevance tuning: TF-IDF → BM25 (expect 30-40% ranking difference)
- Infrastructure: ZooKeeper-based → embedded Raft (AWS managed)
- Dual-write patterns, shadow traffic, gradual cutover

Key tools in the O19s methodology: Quepid (relevance testing), RRE, judgment sets, nDCG measurement.
