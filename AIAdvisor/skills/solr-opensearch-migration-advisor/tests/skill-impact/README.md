# Skill Impact Demo

Proves that the migration advisor's skill content (SKILL.md + steering documents)
measurably changes LLM output quality.

## What it does

Runs the same domain-specific questions through an LLM twice:
1. **WITHOUT** skill context — the bare LLM answers from general knowledge
2. **WITH** skill context — SKILL.md + steering files injected as system prompt

Promptfoo assertions check for specific domain terms the skill teaches
(e.g., `geo_point`, `copy_to`, `multi_match`, `BM25`). The "without" variant
should fail these assertions; the "with" variant should pass.

## Prerequisites

- `promptfoo` installed (`npm install -g promptfoo`)
- AWS credentials configured for Bedrock (required)
- Or Ollama running locally (optional alternative)

## Usage

```bash
# Default: Amazon Bedrock
export AWS_DEFAULT_REGION=us-east-1
bash run_impact_demo.sh

# Alternative: Ollama
bash run_impact_demo.sh --ollama
```

## What to look for

The key result is the **before/after difference**. If the skill adds value,
you'll see the "bare" LLM miss domain-specific terms that the "with-skill"
LLM produces reliably.
