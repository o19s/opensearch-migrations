# Contributor Guide — Migration Advisor Knowledge Base
**Read time:** ~5 minutes
**Audience:** O19s consultants contributing content to the skill corpus

---

## What We're Building and Why

This is a structured knowledge base that lets an AI agent (Claude, Kiro, or similar)
give expert-quality guidance on Solr → OpenSearch migrations — reflecting O19s methodology,
not just generic documentation.

**The analogy:** Think of it as encoding a senior O19s consultant's knowledge into
structured markdown files. When a junior consultant (or a client's engineer) asks
"how do I approach this migration?", the agent responds the way a senior O19s consultant
would — not the way the AWS docs would.

**The output** of using this knowledge base is a set of Kiro-format spec files
(requirements.md, design.md, tasks.md) tailored to a specific migration project,
which an engineer can open in Kiro IDE to drive implementation.

---

## The Two-Layer Structure

```
SKILL.md                        ← routing layer (don't edit unless you own the skill)
  └── references/               ← expert knowledge layer (this is where you contribute)
        ├── 01-strategic-guidance.md
        ├── 02-source-audit.md
        ├── 03-target-design.md
        ├── 04-migration-execution.md
        ├── 05-relevance-validation.md   ← highest priority for O19s
        ├── 06-operations.md
        ├── 07-platform-integration.md
        └── [supporting files — already drafted, need review]
```

The numbered files are the primary work packages. Each is a discrete, ownable chunk.
See `CONTENT-STRUCTURE.md` for full scope and source mappings.

---

## How to Pick Up a Chunk

1. Open `CONTENT-STRUCTURE.md` — find a chunk with no owner, claim it (add your initials)
2. Read the "Source material" list for that chunk — skim, don't deep-read
3. **Write the Key Judgements section first, from memory, before re-reading sources**
   This is the most important instruction in this doc. If you read first, you'll
   summarise. If you write from memory first, you'll encode expert knowledge.
4. Fill in the remaining sections using sources for detail and verification
5. Update the Status field in `CONTENT-STRUCTURE.md` when done

---

## The File Template (Every chunk follows this shape)

```markdown
# [Title]
**Scope:** one sentence — what's in and what's deliberately out
**Audience:** O19s consultants advising Solr→OpenSearch migrations
**Last reviewed:** YYYY-MM-DD  |  **Reviewer:** [initials]

---

## Key Judgements
<!-- 5-10 expert opinions. Hard-won. Opinionated. Not "it depends." -->

## [Content sections — varies by chunk]

## Decision Heuristics
<!-- If X, then Y. Fast pattern-matching for common situations. -->

## Common Mistakes
<!-- What actually goes wrong. Real, not theoretical. -->

## Open Questions / Evolving Guidance
<!-- What we don't know yet, or where the field is moving. -->
```

---

## Quality Bar — What "Done" Looks Like

A chunk is **done** when:
- Key Judgements has 5–10 genuine expert opinions — not neutral summaries
- Decision Heuristics has at least 3 concrete "if X then Y" patterns
- Common Mistakes reflects things that actually happen, not textbook errors
- At least one specific example or war story grounds the abstract guidance
- Someone could read it in 10 minutes and immediately use it on a client engagement

A chunk is **not done** when:
- It summarises what the source documents say
- The opinions are hedged to the point of uselessness ("it depends on your situation")
- There are no concrete examples

---

## The Five Already-Drafted Files (Need Review, Not Rewrite)

These exist as AI-generated first drafts. They need expert eyes, not fresh writing:

| File | Main review task | Who |
|------|-----------------|-----|
| `consulting-methodology.md` | Verify OSC playbook distilled accurately; add missing heuristics | — |
| `migration-strategy.md` | Check dual-write pattern against real experience; add war stories | — |
| `solr-concepts-reference.md` | Verify complexity scoring against actual migrations | — |
| `aws-opensearch-service.md` | Check AWS version numbers and pricing are current | — |
| `spring-boot-kotlin-integration.md` | Verify dependency versions; test code patterns compile | — |

Reviewing one of these is a 30-minute task. Writing a new chunk is 2–4 hours.

---

## Where Things Live

```
agent99/
├── 00-project/          Kiro steering docs for the migration advisor project itself
├── 01-sources/          Raw source material (AWS docs, community posts, Solr reference)
│   ├── opensearch-migration/       ← richest folder, start here for Chunks 3 & 4
│   ├── opensearch-best-practices/  ← for Chunk 6
│   ├── aws-opensearch-service/     ← for Chunk 6
│   ├── solr-reference/             ← for Chunk 2
│   ├── opensearch-fundamentals/    ← for Chunks 3 & 7
│   └── community-insights/         ← real-world experience, all chunks
├── 02-playbook/         OSC consulting playbook (source for Chunks 1 & 5)
├── 03-specs/            OUTPUT — Kiro specs generated by the skill (examples here)
│   └── techproducts-demo/          ← worked example, read this to see end-to-end output
├── 04-skills/           The skill itself
│   └── solr-to-opensearch-migration/
│       ├── SKILL.md                ← routing layer
│       └── references/             ← YOUR WORK GOES HERE
└── 05-working/          Coordination docs (this file, CONTENT-STRUCTURE.md)
```

---

## The Worked Example

`03-specs/techproducts-demo/` contains a complete migration analysis of the Solr
techproducts demo collection — from schema audit through Kiro specs. Read it before
contributing to see what the skill produces and what "good output" looks like.

---

## Questions / Coordination

For now: Sean owns overall structure. Ping him before making structural changes to
SKILL.md or CONTENT-STRUCTURE.md. Content contributions to the 7 numbered chunks
are open — just claim your chunk first.
