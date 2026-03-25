# Hello Evaluations — Promptfoo Smoke Test

A minimal [SSCCE](https://sscce.org/) (Short, Self-Contained, Correct/Compilable Example)
proving the eval pipeline works end-to-end for the Solr → OpenSearch migration advisor.

## What This Tests

One scenario: ask the migration advisor to run in **YOLO / Express mode** for the classic
Solr TechProducts demo collection. The test verifies that the output:

| Assertion | Why it matters |
|-----------|----------------|
| Contains `EXPRESS MODE` banner | Advisor respects the express-mode contract |
| Contains `[ASSUMED:` markers | Advisor flags assumptions rather than silently guessing |
| Mentions `BM25` | Advisor always flags the TF-IDF → BM25 behavioral change |
| Mentions `opensearch-java` | Advisor recommends the correct client library replacement |
| Mentions `multi_match` | Advisor translates eDisMax keyword search correctly |
| LLM-rubric: refactor posture + geo_point | Holistic quality gate via LLM-as-judge |

## Prerequisites

- Node.js 18+
- An OpenAI API key (or another provider — see below)

```bash
export OPENAI_API_KEY=sk-...
```

## Running the Eval

```bash
# From this directory:
npx promptfoo@latest eval

# Open the results UI:
npx promptfoo@latest view
```

Expected output on success:

```
Eval complete.
1 test(s): 1 passed, 0 failed
```

## Using a Different Provider

The config defaults to `openai:gpt-4o-mini`. To swap:

```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
PROMPTFOO_DEFAULT_PROVIDER=anthropic:claude-haiku-4-5-20251001 npx promptfoo@latest eval

# AWS Bedrock (uses ambient credentials / instance role)
PROMPTFOO_DEFAULT_PROVIDER=bedrock:us.anthropic.claude-3-5-haiku-20241022-v1:0 npx promptfoo@latest eval
```

Or edit `providers:` in `promptfooconfig.yaml` directly.

## What "SSCCE" Means Here

This file intentionally covers one scenario with the minimum config needed to demonstrate
the pattern. For the full golden scenario suite, see `../../` (the skill's broader eval
harness). This file is the "does it work at all?" check — run it first when onboarding or
troubleshooting the eval pipeline.

## Relationship to the Broader Eval Suite

```
skills/solr-opensearch-migration-advisor/
└── tests/
    └── evals/
        ├── promptfooconfig.yaml   ← YOU ARE HERE (hello-world smoke test)
        └── ...                    ← full golden scenario suite (future)
```
