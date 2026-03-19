# Kiro Migration Advisor: Workspace Structure

This document describes the layout and governance of the **agent99** workspace — the knowledge base and skill for the Solr → OpenSearch Migration Advisor.

---

## Workspace Organization

```
agent99/                          ← Root workspace
├── 00-project/                   ← Steering docs (this folder)
│   ├── product.md                ← Project vision, success criteria
│   ├── structure.md              ← This navigation document
│   └── tech.md                   ← Technical decisions, architecture
│
├── 01-sources/                   ← Raw source material by topic
│   ├── aws-opensearch-service/   ← AWS-specific operational guides
│   ├── community-insights/       ← Case studies, war stories, lessons learned
│   ├── opensearch-best-practices/← Production patterns, tuning
│   ├── opensearch-fundamentals/  ← Core concepts, APIs
│   ├── opensearch-migration/     ← Best practices for moving from other engines
│   └── solr-reference/           ← Solr architecture, feature reference
│
├── 02-playbook/                  ← OSC consulting playbook
│   ├── OSC Playbook - Search Engine Migration.pptx
│   ├── pre-migration-assessment.md
│   ├── README.md
│   ├── relevance-methodology.md
│   └── team-and-process.md
│
├── 03-specs/                     ← Output engagement specs
│   └── techproducts-demo/        ← Worked example
│       ├── steering/             ← steering/product.md, tech.md, structure.md
│       ├── requirements.md
│       ├── design.md
│       ├── tasks.md
│       └── README.md
│
├── 04-skills/                    ← Packaged skills (installable)
│   └── solr-to-opensearch-migration/
│       ├── SKILL.md              ← Skill routing & metadata
│       └── references/           ← Expert content layer
│           ├── aws-opensearch-service.md
│           ├── consulting-concerns-inventory.md
│           ├── consulting-methodology.md
│           ├── migration-strategy.md
│           └── solr-concepts-reference.md
│
├── 05-working/                   ← Coordination, WIP
│   ├── CONTENT-STRUCTURE.md      ← Tracking for skill content chunks
│   ├── CONTRIBUTOR-GUIDE.md      ← How to add/update content
│   └── source-index.md           ← Index of all source files
│
├── README.md                     ← Root workspace overview
└── solr-to-opensearch-migration.skill ← Packaged, installable skill file
```

---

## Folder Responsibilities

### `00-project/` — Steering
**What**: High-level project decisions, architecture, and vision.
**Content**:
- `product.md`: Project vision, success criteria, constraints.
- `tech.md`: Architecture choices, infrastructure decisions.
- `structure.md`: This navigation document.

---

### `01-sources/` — Raw Knowledge Base
**What**: Unstructured reference material, organized by topic.
**Content**: Markdown files, diagrams, tables, and code snippets curated from AWS, OpenSearch, and community sources.

---

### `02-playbook/` — Consulting Methodology
**What**: Repeatable process flows and OSC proprietary methodology.
**Content**:
- `OSC Playbook...pptx`: The core methodology presentation.
- `relevance-methodology.md`: How to measure and tune relevance (Quepid/RRE).
- `team-and-process.md`: Roles, communication, and project phases.

---

### `03-specs/` — Engagement-Specific Output
**What**: Customized Kiro-format specs generated per engagement.
**Content**:
- `requirements.md`: User stories and functional requirements.
- `design.md`: Technical architecture and data models.
- `tasks.md`: Implementation checklist.

---

### `04-skills/` — Packaged Expertise (Skill)
**What**: The source files for the installable AI skill.
**Contents**:
- `SKILL.md`: Routing layer—metadata, pattern matching, and quick-reference.
- `references/`: Distilled expert knowledge layer (Heuristics, War Stories).

---

### `05-working/` — Coordination
**What**: Internal tracking and guides for contributors.
**Content**:
- `CONTENT-STRUCTURE.md`: Map of which expert chunks are complete or in-progress.
- `source-index.md`: A searchable index of the 50+ files in the `01-sources` corpus.

---

**Last updated**: 2026-03-18
