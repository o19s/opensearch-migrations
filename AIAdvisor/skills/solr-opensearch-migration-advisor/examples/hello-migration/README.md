---
Skill-Version: 0.3.0
Generated: 2026-03-23
Mode: Express (YOLO)
---

```
╔══════════════════════════════════════════════════════════════════════╗
║  ⚡ EXPRESS MODE — GENERATED WITH ASSUMPTIONS ⚡                    ║
║                                                                      ║
║  This spec was generated in express ("YOLO") mode. The skill made    ║
║  its best expert guesses where information was missing. Every        ║
║  assumption is marked [ASSUMED: ...] for your review.                ║
║                                                                      ║
║  DO NOT execute this migration without reviewing assumptions.        ║
║  Express mode is a starting point, not a greenlight.                 ║
║                                                                      ║
║  Skill-Version: 0.3.0                                                ║
╚══════════════════════════════════════════════════════════════════════╝
```

# Solr → OpenSearch Migration: `hello` Collection

## What This Is

This is a complete migration specification for the **`hello`** Solr collection migrating
to **AWS OpenSearch Service 2.x**. It was generated in Express Mode — meaning the skill
applied expert defaults for every missing piece of information.

The collection [ASSUMED: a general-purpose content/document search index with text,
metadata, and facet fields] is a representative starting point for teams that want to
understand what a migration looks like before committing to a full discovery engagement.

## Assumptions Summary

Search this file (and all files in this spec) for `[ASSUMED:` to find every gap that
was filled with a default. High-risk assumptions are starred below — **review these first.**

| # | Assumption | Default Used | Risk |
|---|-----------|--------------|------|
| A1 | Solr version | 8.11 (modern, Point fields, eDisMax default) | Low |
| A2 | Collection count | Single collection named `hello` | Low |
| A3 | Document count | ~100K documents | Medium |
| A4 | Query pattern | eDisMax with `title^3 body^1`, basic facets | **Medium** |
| A5 | Application platform | Spring Boot 3.x / Kotlin | Low |
| A6 | AWS region | us-east-1 | Low |
| A7 | OpenSearch version | 2.17 (latest AWS-supported at time of generation) | Low |
| A8 | Instance type | `r6g.large.search`, 2 data nodes, 2-AZ | Medium |
| A9 | Auth model | IAM + SigV4 (no FGAC, no basic auth) | Low |
| A10 ⭐ | Relevance requirements | Match current Solr behavior (parity goal) | **High** |
| A11 ⭐ | Analyzer chains | Standard English analyzer (no custom plugins) | **High** |
| A12 ⭐ | Document structure | Flat documents — no nested or parent-child | **High** |
| A13 | Schema | 8 explicit fields, 2 dynamic patterns (see design.md) | Medium |
| A14 | Streaming expressions | Not in use | Medium |
| A15 | CDCR / replication | Not in use | Medium |
| A16 | Atomic updates | Not in use | Medium |
| A17 | Dual-write duration | 3 weeks shadow traffic | Medium |
| A18 | Rollback window | 30 days keep-Solr-warm after cutover | Low |
| A19 | Client library | SolrJ → opensearch-java (direct HTTP acceptable too) | Medium |
| A20 | Data Import Handler | Not in use — documents ingested via SolrJ/HTTP | Medium |

**High-risk assumptions explained:**

- **A10 (Relevance parity):** BM25 (OpenSearch default) vs TF-IDF (Solr default) produces
  measurable ranking differences, especially for short fields like `title`. If this assumption
  is wrong — e.g., the team actually wants *better* relevance, not parity — the entire
  validation strategy changes. Clarify this with product stakeholders before Phase 2.

- **A11 (Standard analyzers):** If there are custom Java tokenizers, language-specific
  stemmers, or synonym files maintained externally, the analyzer migration effort can
  double or triple. Check `schema.xml` for `<analyzer class="...">` pointing to non-standard
  class names.

- **A12 (Flat documents):** Nested or parent-child document relationships require a
  fundamentally different approach in OpenSearch (`nested` type or `join` field). A surprise
  here invalidates most of the mapping in `design.md`. Run
  `grep -r "childFilter\|BlockJoin\|toParent\|toChild" solrconfig.xml` before proceeding.

## Migration Complexity Score

**`hello` collection: 2/5 (Low-Medium Complexity)**

Based on express-mode defaults:

| Factor | Score | Notes |
|--------|-------|-------|
| Schema complexity | 1/5 | Assumed standard types, no custom fieldTypes |
| Query complexity | 2/5 | eDisMax with facets — real translation needed |
| Analyzer complexity | 1/5 | Assumed standard analyzer only |
| Infrastructure | 2/5 | 2-node AWS managed — straightforward |
| Client migration | 2/5 | SolrJ → opensearch-java requires query rewrite |
| Operational risk | 1/5 | No CDCR, no streaming, no DIH |

**What would raise this score:**
- Custom analyzers (synonym files, stemmer configs): +1
- Any nested/parent-child documents: +2
- Streaming expressions: +2
- Multi-collection joins: +1
- Atomic updates in indexing pipeline: +1

## File Structure

```
hello-migration/
├── README.md               (this file — orientation + assumptions)
├── MANIFEST.txt            (file inventory)
├── steering/
│   ├── product.md          (scope, success criteria, stakeholders)
│   ├── tech.md             (stack decisions, compatibility matrix)
│   └── structure.md        (Spring Boot/Kotlin project layout)
├── requirements.md         (EARS user stories + acceptance criteria)
├── design.md               (mappings, query translation, architecture)
└── tasks.md                (implementation checklist, 5 phases)
```

## How to Use This Spec

1. **Grep for assumptions first** — `grep -rn '\[ASSUMED:' .` — and resolve the high-risk ones
   before touching code.
2. **Read `steering/product.md`** — confirm the scope matches your actual goal.
3. **Review `design.md` mapping** — substitute real field names from your `schema.xml`.
4. **Walk through `tasks.md`** — adjust effort estimates for your team size and data volume.
5. **Use `requirements.md`** as your acceptance test checklist.

## Next Steps

> **Next steps:** Search this spec for `[ASSUMED:` to find every assumption made.
> High-risk assumptions (A10, A11, A12) are the ones most likely to invalidate sections
> of this spec — review those first. When you're ready to refine any section interactively,
> start with `design.md` → Index Mapping and replace placeholder field names with your
> actual schema.

## Local Toy Demo

If you want something runnable before building the full migration app, this spec now includes
a toy local OpenSearch demo:

- Mapping: `demo/hello-index.json`
- Sample corpus: `demo/hello-docs.json`
- Bootstrap script: `tools/bootstrap_hello_demo.py`
- One-command launcher: `tools/demo_hello_search.sh`

Run it from the repo root:

```bash
bash tools/demo_hello_search.sh
```

That will start a local single-node OpenSearch Docker container, create a local `hello` index,
and bulk-load the toy documents so you can query the index immediately.

To launch the lightweight demo UI on top of that index:

```bash
python tools/hello_demo_server.py
```

Then open `http://127.0.0.1:8010`.

---

**Generated:** 2026-03-23
**Methodology:** OSC Solr→OpenSearch Migration Consulting Playbook
**Mode:** Express (YOLO) — all gaps filled with expert defaults
**Skill-Version:** 0.3.0
