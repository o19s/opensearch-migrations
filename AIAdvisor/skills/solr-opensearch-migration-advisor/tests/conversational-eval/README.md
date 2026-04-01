# Migration Advisor — Conversational Step Eval

Evaluates the advisor's multi-turn workflow by walking through Steps 0-7
as a sequential conversation, asserting that each step produces the
expected content.

This complements the [report-eval](../report-eval/) which evaluates
report *output quality* in a single-shot prompt. This eval tests the
*interactive experience* — does the advisor follow its workflow, ask the
right questions, and produce the right content at each step?

## Design

Follows the pattern established in
[PR #23](https://github.com/o19s/opensearch-migrations/pull/23):
sequential promptfoo tests that build on a shared conversation session.

- `continue: "false"` starts a fresh Claude session
- `continue: "true"` resumes the previous session via `--resume --session-id`

Tests **must** run sequentially (`--max-concurrency 1`) since each test
depends on prior conversation context.

## Steps covered

| Test | Workflow Step | What it asserts |
|------|-------------|-----------------|
| Step 0 | Stakeholder ID | Asks for role with 5+ examples |
| Step 1 | Schema Acquisition | Asks for schema; produces mapping |
| Step 1b | Schema Acquisition | Mapping quality (geo_point, keyword, etc.) |
| Step 2 | Incompatibility Analysis | Flags copyField → copy_to, classifies severity |
| Step 3 | Query Translation | Translates standard + edismax queries to DSL |
| Step 4 | Customizations | Asks about handlers, plugins, auth |
| Step 4b | Customizations | Maps Basic Auth + URP to OpenSearch equivalents |
| Step 5 | Infrastructure | Asks about cluster topology |
| Step 5b | Infrastructure | Provides sizing recommendation |
| Step 6 | Client Integration | Asks about client libraries |
| Step 6b | Client Integration | Maps SolrJ → opensearch-java, /select → /_search |
| Step 7 | Report | Generates report reflecting full conversation |

## Running

```bash
bash run_eval.sh
```

Run `npx promptfoo view` after to inspect results in the browser.

## Cost

This eval makes 12 sequential Claude CLI calls with MCP tools. Expect
~10-15 minutes runtime and moderate API cost. For a quick smoke test,
you can comment out later steps in `eval.yaml` and run only Steps 0-1.
