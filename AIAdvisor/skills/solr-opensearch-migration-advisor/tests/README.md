# Migration Advisor Tests

## Quick Start

```bash
cd AIAdvisor/skills/solr-opensearch-migration-advisor
uv pip install -e ".[dev]"
pytest    # unit tests only — no LLM needed
```

## Test Tiers

### Tier 1: Unit Tests — pytest (no external dependencies)

Fast, deterministic tests for converters, skill logic, storage, and reports.

```bash
pytest tests/test_schema_converter.py tests/test_query_converter.py tests/test_skill.py tests/test_storage.py tests/test_report.py
```

### Tier 2: Promptfoo Evals (requires LLM)

All LLM-backed tests use [promptfoo](https://promptfoo.dev/). Three eval
configs, each testing a different aspect:

| Config | What it tests | LLM needed |
|--------|---------------|------------|
| `eval-guidance-impact.yaml` | Steering changes skill output (bare vs guided) | Claude agent |
| `eval-media-search.yaml` | Solr→OS query translation (30 tests) | Claude agent |
| `eval.yaml` | General conversation flow | Claude agent |

#### Guidance Impact (Claude agent, context engineering)

Proves steering docs are not decorative — runs the **real skill** twice:
once with empty `steering/` (bare), once with full steering content.
The side-by-side report shows bare=red, guided=green.

```bash
cd tests/evals

# One-time setup: create bare skill fixture (symlinks without steering)
bash fixtures/skill-bare/setup.sh

# Run (two Claude agent calls per test — bare and guided):
promptfoo eval -c eval-guidance-impact.yaml

# View side-by-side results:
promptfoo view

# Export shareable report:
promptfoo eval -c eval-guidance-impact.yaml --output guidance-impact.html
```

#### Media Search Query Translation (Claude agent)

28 deterministic + 2 LLM-judge tests for Solr eDisMax → OpenSearch DSL.

```bash
cd tests/evals
export PROMPTFOO_PYTHON=$(pwd)/../../.venv/bin/python

# Deterministic only (fast):
promptfoo eval -c eval-media-search.yaml --filter-pattern "^(?!judge)"

# Single category:
promptfoo eval -c eval-media-search.yaml --filter-pattern "^hl-"

# LLM-judge only:
promptfoo eval -c eval-media-search.yaml --filter-pattern "^judge"
```

#### General Conversation Flow (Claude agent)

Tests the advisor's conversational behavior (role clarification, schema
request, migration plan).

```bash
cd tests/evals
export PROMPTFOO_PYTHON=$(pwd)/../../.venv/bin/python
promptfoo eval -c eval.yaml
```

See `tests/evals/README.md` for Claude auth setup.
