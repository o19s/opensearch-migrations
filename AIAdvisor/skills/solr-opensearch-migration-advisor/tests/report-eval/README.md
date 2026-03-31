# Migration Advisor — 4-Tier Report Quality Eval

Evaluates migration report quality through four increasingly complex tiers,
from deterministic Python to full LLM + MCP integration.

## Tiers

### T1: Deterministic (MCP stdio)

Calls the real MCP server over stdio — `convert_schema_xml`, `handle_message`,
`generate_report` — with no LLM involved. Produces the deterministic Python
report that serves as the structural "answer key."

- No LLM, no API cost, instant
- Tests: schema converter + report generator + MCP transport

```bash
bash run_eval.sh --tier 1
```

### T2: LLM + Skill + OS Mapping

Feeds Claude the assembled skill context (SKILL.md + steering docs) as a system
prompt, plus the Solr schema and its pre-converted OpenSearch mapping. No MCP
tools available — the LLM must produce a report purely from skill guidance.

- Tests: can the skill guide a complete report when the user has done the
  conversion work?
- Requires: `claude` CLI installed and authenticated

```bash
bash run_eval.sh --tier 2
```

### T3: LLM + Skill, No OS Mapping

Same as T2, but does NOT provide the pre-converted mapping. The LLM receives
only the raw Solr schema and must derive or reason about the OpenSearch mapping
from the skill's steering docs alone.

- Tests: can the skill guide a report with incomplete input? This is the
  hardest pure-skill test and the most revealing for skill authoring quality.
- Requires: `claude` CLI installed and authenticated

```bash
bash run_eval.sh --tier 3
```

### T4: LLM + MCP Tools

Runs Claude Code CLI with full MCP tool access. Claude can call
`convert_schema_xml`, `generate_report`, and all other skill tools.
This is the closest to the real-world user experience.

- Tests: full integration — LLM + skill + tools working together
- Requires: `claude` CLI installed and authenticated

```bash
bash run_eval.sh --tier 4
```

## Running

```bash
bash run_eval.sh              # all 4 tiers
bash run_eval.sh --tier 1     # T1 only (free, instant)
bash run_eval.sh --tier 2     # T2 only
bash run_eval.sh --tier 3     # T3 only
bash run_eval.sh --tier 4     # T4 only
bash run_eval.sh --mcp-only   # alias for --tier 1
```

Report artifacts are saved to `eval-reports/` with tier-prefixed filenames.

Run `promptfoo view` after an eval to inspect results in the browser.

## Assertions

All tiers are evaluated against the same assertions:

- **Schema mapping**: geo_point, keyword, integer, date
- **Report structure**: all 7 canonical sections (Incompatibilities, Client
  Impact, Stage Plan, Milestones, Blockers, Implementation, Cost)
- **Stage plan quality**: target validation, success criteria, stop conditions
- **Incompatibility detection**: copyField → copy_to flagged
- **Client integration**: SolrJ mentioned

## What to expect

- **T1**: all assertions pass (deterministic baseline)
- **T2**: all/most pass — LLM has mapping + skill guidance
- **T3**: most pass — hardest test, reveals skill content gaps
- **T4**: all pass — LLM can call tools to fill gaps
