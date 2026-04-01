# Migration Advisor — 4-Tier Report Quality Eval

Evaluates migration report quality through four increasingly complex tiers,
from deterministic Python to full LLM + MCP integration.

## Evaluation Philosophy

`T1-T4` are generation tiers. The rubric types are quality dimensions applied
to outputs from those tiers.

`T1` is the deterministic baseline. It should score well on the core, codified
dimensions of report quality:

- incompatibilities
- client migration
- migration plan

`T2-T4` are richer reasoning tiers and are evaluated across the full rubric
set, including more judgment-heavy dimensions such as index design and
stakeholder coverage.

This split is intentional. Higher-tier evaluations can surface useful concerns
that are missing from the deterministic report. When those concerns prove
broadly valuable and can be expressed reliably, they should be promoted into
the Python report generator. In that way, `T1` becomes an iteratively
improving baseline distilled from what the richer tiers repeatedly teach us.

| Rubric Type | T1 Deterministic | T2 LLM+Skill+Mapping | T3 LLM+Skill | T4 LLM+MCP |
|---|---|---|---|---|
| `incompatibilities_quality` | Primary | Primary | Primary | Primary |
| `client_migration_quality` | Primary | Primary | Primary | Primary |
| `migration_plan_quality` | Primary | Primary | Primary | Primary |
| `index_design_quality` | Advisory initially | Primary | Primary | Primary |
| `stakeholder_coverage_quality` | Advisory initially | Primary | Primary | Primary |

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

All tiers are evaluated against the same assertion families:

- **Schema mapping**: geo_point, keyword, integer, date
- **Report structure**: all 7 canonical sections (Incompatibilities, Client
  Impact, Stage Plan, Milestones, Blockers, Implementation, Cost)
- **Stage plan quality**: target validation, success criteria, stop conditions
- **Incompatibility detection**: copyField → copy_to flagged
- **Client integration**: SolrJ mentioned
- **Qualitative rubrics**: incompatibilities, client migration, index design,
  migration plan, stakeholder coverage

## What to expect

- **T1**: should pass the structural checks and establish the deterministic
  baseline; advanced qualitative rubrics may initially lag and serve as a
  signal for what to codify next
- **T2**: should perform well on both structural and qualitative checks when
  the mapping is already available
- **T3**: is the hardest pure-skill tier and often reveals gaps in synthesis,
  index design judgment, and missing report content
- **T4**: should be the strongest end-to-end tier because it can combine skill
  guidance with live MCP tools
