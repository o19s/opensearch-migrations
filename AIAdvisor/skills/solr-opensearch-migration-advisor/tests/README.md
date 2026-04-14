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
| `eval-guidance-impact.yaml` | Steering content changes LLM output (before/after) | Ollama (local) |
| `eval-media-search.yaml` | Solr→OS query translation (30 tests) | Claude agent |
| `eval.yaml` | General conversation flow | Claude agent |

#### Guidance Impact (Ollama, free, fast)

Proves steering docs are not decorative — the same scenario sent bare vs
with steering produces different expert terms.

```bash
cd tests/evals
ollama pull llama3.2    # one-time setup

# Run all (bare + guided, side by side):
promptfoo eval -c eval-guidance-impact.yaml

# View results:
promptfoo view

# Export shareable report:
promptfoo eval -c eval-guidance-impact.yaml --output guidance-impact.html
```

To compare models: `OLLAMA_MODEL=qwen3:14b promptfoo eval -c eval-guidance-impact.yaml`

| Model | Bare | Guided | Delta |
|-------|------|--------|-------|
| llama3.2 (3B) | ~1/4 concepts | 3-4/4 | **+2-3** |
| qwen3 (14B) | ~3/4 concepts | 4/4 | +1 |

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
