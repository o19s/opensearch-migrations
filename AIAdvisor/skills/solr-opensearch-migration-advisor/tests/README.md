# Migration Advisor Tests

## Quick Start

```bash
cd AIAdvisor/skills/solr-opensearch-migration-advisor
uv pip install -e ".[dev]"
pytest
```

## Test Tiers

### Tier 1: Unit Tests (no external dependencies)

Fast, deterministic tests for converters, skill logic, storage, and reports.

```bash
pytest tests/test_schema_converter.py tests/test_query_converter.py tests/test_skill.py tests/test_storage.py tests/test_report.py
```

### Tier 2: Guidance Impact Tests (requires LLM)

**These tests prove that the steering content we maintain actually changes
model output.** They send the same migration scenario to an LLM with and
without our `steering/` content, then check whether specific expert terms
appear in the response.

```bash
# Auto-detect backend (tries Bedrock, then local Ollama, skips if neither)
pytest tests/test_guidance_impact.py -v

# Explicitly require Ollama (fails if not running)
pytest tests/test_guidance_impact.py -v --llm-backend=ollama

# Explicitly require AWS Bedrock (fails if no credentials)
pytest tests/test_guidance_impact.py -v --llm-backend=bedrock
```

Every test run (including unit tests) creates a session directory under
`tests/artifacts/<timestamp>/` and symlinks `tests/artifacts/latest/`.

```
tests/artifacts/
  2026-04-03T015624Z/
    pytest-results.xml           # standard junit XML
    guidance-impact-report.md    # LLM responses + concept scorecard
    run-metadata.json            # git SHA, steering file hashes, backend config
  latest -> 2026-04-03T015624Z/
```

Session directories accumulate so you can compare runs over time.
The `run-metadata.json` includes SHA-256 hashes of each steering file,
so you can trace exactly which guidance version produced which result.

#### Why This Matters

Without steering content, a small LLM gives generic migration advice:
*"most functionality should port"*, *"syntax may differ slightly"*.

With steering content loaded, the same model produces specific, opinionated
guidance that a consultant would actually give: `script_score` as the
replacement for function queries, *"no direct equivalent"* for custom
handlers, `terms lookup` for join replacements.

#### Model Size vs. Guidance Impact

Smaller models show a larger delta, making the impact more obvious:

| Model | Bare | Guided | Delta | Time |
|-------|------|--------|-------|------|
| llama3.2 (3B) | ~1/4 concepts | 3-4/4 | **+2-3** | ~8s |
| qwen3 (14B) | ~3/4 concepts | 4/4 | +1 | ~144s |

The 3B model is the default: fast, free, and the guidance impact is
dramatic. The 14B model already knows most facts from training data, but
guidance still adds the opinionated framing (*"must rebuild"* vs
*"may require adjustments"*) that distinguishes consultant-grade advice.

To compare models:

```bash
pytest tests/test_guidance_impact.py -v -s --ollama-model=llama3.2:latest
pytest tests/test_guidance_impact.py -v -s --ollama-model=qwen3:14b
```

#### Backend Options

| Flag | Description |
|------|-------------|
| `--llm-backend=auto` | Default. Tries Bedrock then Ollama, skips if neither available |
| `--llm-backend=ollama` | Requires Ollama, **fails** if unavailable |
| `--llm-backend=bedrock` | Requires AWS Bedrock, **fails** if no credentials |
| `--ollama-base-url` | Override Ollama URL (default: `http://localhost:11434`) |
| `--ollama-model` | Override Ollama model (default: `llama3.2:latest`) |
| `--bedrock-model-id` | Override Bedrock model (default: `anthropic.claude-3-haiku-20240307-v1:0`) |
| `--bedrock-region` | Override AWS region (default: `us-east-1`) |

#### Prerequisites

**Ollama** (local, free):
```bash
ollama pull llama3.2:latest
ollama serve   # or ensure it's already running
```

**Bedrock** (AWS, pay-per-use): Requires AWS credentials with Bedrock
model access. No additional setup needed if `boto3` can authenticate.

### Tier 3: Claude Evals (requires Claude API)

End-to-end evaluations using Claude as both advisor and judge.
See `tests/evals/README.md`.
