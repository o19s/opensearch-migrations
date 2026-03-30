# Skill Impact Demo — Three Tiers

Proves that the migration advisor skill adds measurable value, tested through
three increasingly realistic execution paths.

## Tiers

### Tier 1: Prompt Stuffing (does the content help?)

Concatenates SKILL.md + steering files into a system prompt and sends the same
question to an LLM with and without that context. Proves the skill's *content*
changes LLM output.

- No skill code involved — just text injected into the prompt
- Requires: Bedrock (or `--ollama` for local)
- Fast, cheap (~10K tokens)

```bash
export AWS_DEFAULT_REGION=us-east-1
bash run_tier1_stuffing.sh
```

### Tier 2: Skill Code Provider (does the skill code work?)

Uses promptfoo's exec provider to call `skill.handle_message()` directly —
the same Python code path that Kiro/Claude Code would invoke via MCP. No LLM
involved; tests the deterministic converters.

- Real skill engagement: schema conversion, query translation, report generation
- Requires: Python 3.11+ with skill dependencies
- Instant, zero cost

```bash
bash run_tier2_skill.sh
```

### Tier 3: Claude Code CLI (does it work in a real IDE?)

Runs the same question through Claude Code's CLI in two modes:
1. `--bare` (no CLAUDE.md, no skill context) — baseline
2. Default mode from `AIAdvisor/` (auto-discovers CLAUDE.md + skill) — enhanced

This is the closest to real-world usage without manually opening an IDE.

- Real IDE integration path
- Requires: `claude` CLI installed and authenticated
- Costs API tokens (two LLM calls)

```bash
bash run_tier3_claude.sh
```

## Bedrock Setup

Tiers 1 and 3 require AWS credentials with Bedrock model access:

1. Configure credentials: `aws configure` or set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
2. Set your region: `export AWS_DEFAULT_REGION=us-east-1`
3. Enable the model in [Bedrock Model Access](https://console.aws.amazon.com/bedrock/home#/modelaccess) — request access to `Amazon Nova Lite` (used by tier 1)
4. Verify: `aws bedrock list-foundation-models --query "modelSummaries[?modelId=='amazon.nova-lite-v1:0'].modelId" --output text`

If you see `ResourceNotFoundException: Model use case details have not been submitted`, you need step 3.

See [AWS Bedrock Getting Started](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html) for full details.

## What to look for

Across all three tiers, the pattern should be consistent:
- **Without skill context:** generic or incomplete answers
- **With skill context:** precise field types (geo_point, keyword, integer),
  correct translations (copy_to), and incompatibility flags

## Optional: Kiro Live Demo (Run Book)

For a live demo with Kiro:
1. Open `AIAdvisor/` folder in Kiro
2. Kiro auto-discovers the skill (check `.kiro/skills/` symlink)
3. Open agent chat and ask:
   > "I have a Solr schema with a LatLonPointSpatialField, a copyField from
   > title to title_sort, and a TrieIntField for price. What OpenSearch mapping
   > should I create?"
4. Compare the response against the Tier 1-3 automated results
