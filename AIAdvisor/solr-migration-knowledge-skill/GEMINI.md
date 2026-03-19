# GEMINI.md - Solr → OpenSearch Migration Advisor

This workspace contains the **Solr → OpenSearch Migration Advisor**, a knowledge base and installable AI skill designed to encode senior OSC (OpenSource Connections) consulting expertise into a reusable AI asset.

## Project Overview

*   **Goal:** Guide technical developers or non-tech employees through expert-quality Solr-to-OpenSearch migration engagements without requiring a senior consultant in the room.
*   **Architecture:** A two-layer "Skill" architecture:
    *   **Routing Layer (`SKILL.md`):** Metadata, quick-reference tables, and pointers to reference files.
    *   **Expert Knowledge Layer (`references/`):** 7 numbered content chunks encoding methodology, key judgements, decision heuristics, and war stories.
*   **Primary Output:** Per-engagement migration specs in **Kiro format** (`requirements.md`, `design.md`, `tasks.md`).

## Directory Overview

*   `00-project/`: Steering docs, technical decisions, and workspace structure.
*   `01-sources/`: Raw source material (AWS docs, community posts, Solr/OpenSearch reference).
*   `02-playbook/`: OSC consulting playbook — the methodology source of truth.
*   `03-specs/`: Output engagement specs; `techproducts-demo/` is the canonical worked example.
*   `04-skills/`: The packaged AI skill (`solr-to-opensearch-migration/`).
*   `05-working/`: Coordination docs, including `CONTRIBUTOR-GUIDE.md` and `CONTENT-STRUCTURE.md`.
*   `solr-to-opensearch-migration.skill`: The packaged, installable skill file (zip format).

## Key Files

*   `README.md`: High-level overview and quick-start guide.
*   `04-skills/solr-to-opensearch-migration/SKILL.md`: The core routing and metadata for the AI skill.
*   `05-working/CONTRIBUTOR-GUIDE.md`: Essential rules for content contributors (e.g., "Write from memory first").
*   `05-working/CONTENT-STRUCTURE.md`: Tracking for the 7 expert content chunks and their current status.
*   `03-specs/techproducts-demo/README.md`: Explains how to use the worked example to generate new client specs.

## Usage & Development Conventions

### Content Contribution (Critical)

1.  **Expert-First:** When adding or updating reference chunks, **write the "Key Judgements" section from memory first** before reading sources. This ensures expert knowledge is captured, not just documentation summaries.
2.  **Opinionated:** Avoid "it depends" without a follow-up heuristic. Provide concrete decision heuristics and "If X, then Y" patterns.
3.  **Structure:** Every reference file must include:
    *   Metadata (Scope, Audience, Last reviewed).
    *   **Key Judgements:** 5-10 bullet points of hard-won expert opinion.
    *   **Decision Heuristics:** Fast pattern-matching for common situations.
    *   **Common Mistakes:** Real-world pitfalls and war stories.
4.  **Coordination:** Claim a chunk in `05-working/CONTENT-STRUCTURE.md` by adding your initials before starting work.

### Packaging the Skill

To rebuild the `.skill` file after editing the files in `04-skills/`:

```bash
cd 04-skills/solr-to-opensearch-migration
zip -r ../../solr-to-opensearch-migration.skill SKILL.md references/
```

### Starting a New Engagement

1.  Create a new folder: `03-specs/[client-name]/`.
2.  Template it from `03-specs/techproducts-demo/`.
3.  Customize steering docs and requirements to drive Kiro's implementation tasks.

## Technical Context

*   **Foundation:** Both Solr and OpenSearch are Lucene-based, but have divergent APIs and coordination models (ZooKeeper vs. Raft).
*   **Relevance:** Default scoring differs (TF-IDF vs. BM25). Relevance measurement (Quepid/RRE) is a core requirement of every engagement.
*   **Target Stack:** Typically AWS OpenSearch Service (managed), often with Spring Boot/Kotlin as the application layer.
