# Solr to OpenSearch Migration Skill — Demo Runbook

Last update: 2026/03/30

This runbook walks through demonstrating the Solr to OpenSearch Migration Advisor skill.
The skill helps users migrate from Apache Solr to Amazon OpenSearch by converting schemas,
translating queries, flagging incompatibilities, and generating migration reports.

## Prerequisites

* AWS credentials configured with Bedrock model access (Amazon Nova Lite)
  * `export AWS_DEFAULT_REGION=us-east-1`
  * Verify: `aws sts get-caller-identity`
  * Enable model access in [Bedrock console](https://console.aws.amazon.com/bedrock/home#/modelaccess) if needed
* The repo: `git clone git@github.com:o19s/opensearch-migrations.git`
* Branch: `git checkout feature/sma-skill-impact`
* Python 3.11+ with `uv` (for tier 2)
* `promptfoo` installed: `npm install -g promptfoo`
* Optional: Claude Code CLI (`claude`) for tier 3
* Optional: Kiro IDE for live demo

## DEMO: Three-Tier Skill Impact

The demo proves the skill adds measurable value through three levels of realism.
Run them in order — each builds on the story of the previous tier.

### Tier 1: Does the Skill Content Help? (Prompt Stuffing)

This tier shows that injecting the skill's knowledge into an LLM prompt
changes the quality of the response. Same question, two runs: one without
skill context, one with.

1. Navigate to the demo directory:
   ```
   cd AIAdvisor/skills/solr-opensearch-migration-advisor/tests/skill-impact
   ```
2. Run the eval:
   ```
   export AWS_DEFAULT_REGION=us-east-1
   bash run_tier1_stuffing.sh
   ```
3. What to look for in the output:
   * Two columns: "WITHOUT skill context" and "WITH skill context"
   * The WITHOUT column should show **[FAIL]** — the bare LLM gives a generic answer
   * The WITH column should show **[PASS]** — the skill-enhanced LLM produces precise
     field types (`geo_point`, `copy_to`, `integer`) and flags incompatibilities
4. The key talking point:
   *"The same LLM, the same question — but with our skill's domain knowledge
   injected, it produces the correct OpenSearch mapping and catches issues
   that the bare model misses."*

### Tier 2: Does the Skill Code Work? (Deterministic)

This tier uses the actual skill code — the same Python that Kiro and Claude Code
call via MCP. No LLM involved, instant, free.

1. From the same directory:
   ```
   bash run_tier2_skill.sh
   ```
2. What to look for:
   * Both test cases should show **[PASS]**
   * The schema conversion produces a valid OpenSearch mapping with correct types
   * The query translation produces valid Query DSL
   * A migration report is automatically generated
3. The key talking point:
   *"This is the real skill, not prompt stuffing. The same code that runs
   when you use the skill in Kiro or Claude Code. It deterministically
   converts schemas, translates queries, and generates reports."*

### Tier 3: Does It Work in a Real IDE? (Claude Code CLI)

This tier runs the question through Claude Code's actual CLI — the real IDE
integration path with CLAUDE.md auto-discovery.

1. From the same directory:
   ```
   bash run_tier3_claude.sh
   ```
2. This takes ~30 seconds and costs API tokens (two Claude calls)
3. What to look for:
   * Two responses saved to `tier3-results/`
   * `response-bare.txt` — Claude without skill context (generic)
   * `response-with-skill.txt` — Claude with CLAUDE.md + skill auto-discovered
   * Assertion summary shows the with-skill response passes more checks
4. The key talking point:
   *"This is what it looks like when a developer opens the project in Claude Code
   and asks a migration question. The IDE automatically loads the skill. No
   configuration, no copy-paste — just open the folder and ask."*

## DEMO: Live in Kiro (Optional)

For a live demo with Kiro IDE:

1. Open Kiro and select `File > Open Folder`, navigate to the `AIAdvisor/` directory
2. Kiro auto-discovers the skill — check the bottom status bar for skill detection
3. Open the agent chat and type:
   ```
   I want to use the Solr to OpenSearch skill.
   ```
4. The skill will ask about your role. Pick **"Search Engineer"** for the deepest
   technical response.
5. When asked for a schema, paste the [techproducts managed-schema.xml](https://github.com/apache/solr/blob/main/solr/server/solr/configsets/sample_techproducts_configs/conf/managed-schema.xml)
   from Solr's GitHub repository.
6. Walk through the migration workflow:
   * Schema conversion and incompatibility analysis
   * Query translation (try: `q=laptop&defType=edismax&qf=title^2 description`)
   * Ask for the migration report

## DEMO: Live in Claude Code CLI (Optional)

1. Change into the AIAdvisor directory:
   ```
   cd AIAdvisor
   ```
2. Start Claude Code:
   ```
   claude
   ```
3. Start the conversation:
   ```
   I want to use the Solr to OpenSearch skill.
   ```
4. Follow the same workflow as the Kiro demo above.

## Talking Points

* **The skill is portable** — same SKILL.md works in Kiro, Claude Code, Cursor,
  Copilot, and Gemini. Write once, use everywhere.
* **Kiro is first among equals** — it gets steering with `inclusion: always`,
  file-event hooks, and native MCP integration. Other IDEs get instruction stubs.
* **Deterministic where possible** — schema conversion and query translation are
  Python code, not LLM generation. The LLM orchestrates, but the heavy lifting
  is deterministic and testable.
* **Accuracy over speed** — the skill's steering documents enforce an accuracy-first
  approach. Every incompatibility is flagged, every uncertain mapping is called out.

## Troubleshooting

* **Bedrock "ResourceNotFoundException"**: You need to enable model access in the
  [Bedrock console](https://console.aws.amazon.com/bedrock/home#/modelaccess).
  Request access to Amazon Nova Lite.
* **promptfoo not found**: `npm install -g promptfoo`
* **Python import errors in tier 2**: Install skill dependencies:
  ```
  cd AIAdvisor/skills/solr-opensearch-migration-advisor
  uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
  ```
* **Tier 3 "claude not found"**: Install Claude Code CLI from https://claude.com/claude-code
