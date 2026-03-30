# Skill Impact Demo — Quick Reference

## Setup

```bash
git checkout feature/sma-skill-impact
cd AIAdvisor/skills/solr-opensearch-migration-advisor/tests/skill-impact
export AWS_DEFAULT_REGION=us-east-1
```

## Run

```bash
bash run_tier1_stuffing.sh     # Bedrock, bare vs with-skill, 3 sec
bash run_tier2_skill.sh        # Deterministic, no LLM, instant
bash run_tier3_claude.sh       # Claude Code CLI, ~30 sec
bash run_report_demo.sh        # Generate migration report (saved to migration-report.md)
bash run_report_demo.sh /path/to/your/schema.xml   # Use your own schema
```

## Expected Results

* **Tier 1:** WITHOUT = FAIL, WITH = PASS (skill content changes LLM output)
* **Tier 2:** 2/2 PASS (real skill code, no LLM)
* **Tier 3:** bare = weaker, with-skill = stronger (real IDE integration)

## DEMO: Live in Kiro (Optional)

1. Open `AIAdvisor/` folder in Kiro
2. Open agent chat: *"I want to use the Solr to OpenSearch skill."*
3. Pick **Search Engineer** when asked about your role
4. Paste the [techproducts managed-schema.xml](https://github.com/apache/solr/blob/main/solr/server/solr/configsets/sample_techproducts_configs/conf/managed-schema.xml) when asked for a schema

## DEMO: Live in Claude Code CLI (Optional)

1. `cd AIAdvisor && claude`
2. *"I want to use the Solr to OpenSearch skill."*
3. Follow the same workflow as Kiro above

## Talking Points

* **Portable** — same SKILL.md works in Kiro, Claude Code, Cursor, Copilot, Gemini
* **Kiro is first among equals** — steering with `inclusion: always`, hooks, native MCP
* **Deterministic where possible** — schema/query conversion is Python, not LLM generation
* **Accuracy over speed** — every incompatibility flagged, every uncertain mapping called out
