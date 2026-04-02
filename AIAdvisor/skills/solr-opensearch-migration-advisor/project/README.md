# 00-Project

This folder is the repo's project/governance layer.

It is intentionally split into a few buckets so new readers can answer:

- where do I start?
- what is canonical?
- what is planning vs testing vs demos vs working notes?

## Start Here

- [core/product.md](core/product.md)
- [core/structure.md](core/structure.md)
- [testing/testing-status.md](testing/testing-status.md)
- [demos/five-demo-stories-solr-migration.md](demos/five-demo-stories-solr-migration.md)

## Canonical Docs

These are the best “trust this first” docs in `project`:

- [core/product.md](core/product.md)
  - what the repo is trying to be
- [core/structure.md](core/structure.md)
  - how the repo is organized
- [testing/testing-status.md](testing/testing-status.md)
  - where implementation/testing really stands
- [demos/five-demo-stories-solr-migration.md](demos/five-demo-stories-solr-migration.md)
  - current demo ladder and rough readiness

## Working Notes

These are useful, but should be read as active analysis/supporting material rather than top-level
canonical reference:

- most files under [solr/](solr/)
- most files under [upstream/](upstream/)
- some files under [demos/](demos/) that are presentation/runbook specific

Good rule of thumb:

- `core/`, `testing/`, and the main demo ladder are the durable orientation layer
- `solr/` and `upstream/` are the active working-analysis layer

## Folders

- `core/`
  - repo orientation, positioning, structure, foundational docs
- `planning/`
  - delivery planning and larger project-analysis docs
- `testing/`
  - testing status, shareable testing overview, eval/testing roadmap
- `demos/`
  - demo scripts, demo ladders, LLM-vs-deterministic framing
- `upstream/`
  - Amazon/upstream query-translation assessments and follow-up questions
- `solr/`
  - Solr-specific working notes, coverage matrix, deep-dive review material

## Practical Reading Paths

If you are new to the repo:

1. [core/product.md](core/product.md)
2. [core/structure.md](core/structure.md)
3. [testing/testing-status.md](testing/testing-status.md)

If you are preparing a demo:

1. [demos/five-demo-stories-solr-migration.md](demos/five-demo-stories-solr-migration.md)
2. [demos/hello-migration-demo-script.md](demos/hello-migration-demo-script.md)
3. [demos/llm-vs-deterministic-query-translation-demo.md](demos/llm-vs-deterministic-query-translation-demo.md)

If you are working the Solr-specific lane:

1. [solr/solr-specific-review-index.md](solr/solr-specific-review-index.md)
2. [upstream/upstream-query-translation-assessment.md](upstream/upstream-query-translation-assessment.md)
3. [solr/solr-query-coverage-matrix.md](solr/solr-query-coverage-matrix.md)

## Quick Heuristics

If you are unsure where something belongs:

- durable repo identity or structure -> `core/`
- planning or delivery backlog -> `planning/`
- implementation status or eval/testing policy -> `testing/`
- presentation/runbook material -> `demos/`
- Amazon/upstream coordination -> `upstream/`
- Solr-specific deep-dive analysis -> `solr/`
