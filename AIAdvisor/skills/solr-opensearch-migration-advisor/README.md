# Solr-to-OpenSearch Migration Advisor

An AI-powered migration advisor that provides expert guidance for migrating
Apache Solr deployments to AWS OpenSearch Service. It combines curated expert
knowledge, deterministic conversion tools, and structured consulting methodology
into a single interactive skill.

**Branch:** `feature/one-big-hairy`

---

## Getting Started

```bash
git checkout feature/one-big-hairy
cd AIAdvisor/skills/solr-opensearch-migration-advisor
claude
```

The skill loads automatically. You're now talking to a migration advisor that has
access to expert references, schema/query converters, and a Solr inspection toolkit.

---

## What To Ask — By Use Case

### Migration Planning (executive/PM perspective)

Use when you need to scope work, allocate resources, or build a migration roadmap
before any technical work begins.

> *"We have 12 Solr collections totaling 800GB across 3 SolrCloud clusters. We need
> to migrate to AWS OpenSearch. Help me build a phased migration plan with resource
> estimates and risk areas."*

> *"What are the typical phases of a Solr-to-OpenSearch migration, and what team
> roles do we need at each stage? We have 2 search engineers and 1 DevOps person."*

> *"Our CTO wants a go/no-go framework for this migration. What criteria should we
> use to decide whether we're ready to cut over?"*

### Solr Audit and Discovery

Use when you're starting a new engagement and need to understand what you're working
with before making any decisions.

> *"I have a Solr 8.11 cluster. Walk me through what I should inventory before
> planning a migration — collections, schemas, query patterns, consumers, the works."*

> *"Here's our schema.xml — what stands out as potentially tricky to migrate?
> What should I flag for the team?"*
>
> *(paste or attach schema.xml)*

> *"We know our main search app uses Solr, but we suspect there are other consumers
> hitting it directly. How should I discover and document all the Solr consumers?"*

### Technical Deep Dive

Use when you need to understand specific migration challenges, plan around
incompatibilities, or prepare the team for what's ahead.

> *"Walk me through the differences between Solr's eDisMax and OpenSearch's
> multi_match. We rely heavily on qf, pf, mm, and bq — what breaks and what
> translates cleanly?"*

> *"We use TF-IDF scoring and our relevance is finely tuned. What should we expect
> when moving to BM25, and how do we validate that search quality hasn't regressed?"*

> *"Our Solr setup uses nested documents, function queries for boosting by recency,
> and a custom UpdateRequestProcessor chain. Give me an honest assessment of the
> migration complexity for each."*

### Iterative Migration Partnership (phone-a-friend)

Use throughout active migration work. The advisor can help with specific conversion
tasks, review your work, troubleshoot issues, or guide you step-by-step through
a phase you haven't done before.

> *"Here's our Solr schema.xml — convert it to an OpenSearch index mapping and flag
> anything that needs manual attention."*
>
> *(paste or attach schema.xml)*

> *"I'm converting our faceted search queries from Solr to OpenSearch. Here are
> 3 representative queries — translate them and explain what changed."*
>
> *(paste query examples)*

> *"We just deployed the OpenSearch cluster and our first batch of migrated queries
> is returning different result ordering than Solr. Help me diagnose why and figure
> out what to adjust."*

> *"I'm setting up dual-write so we can run both engines in parallel. Walk me through
> the pattern — what infrastructure do I need, how do I validate consistency, and
> when is it safe to cut over?"*

---

## Running Tests

```bash
python3.12 -m pytest tests/ -q          # 345 tests, all passing
```

---

## What's In This Branch

### Skill Content

| Component | Details |
|-----------|---------|
| `SKILL.md` | Routing layer with 8-step guided workflow and 18 MCP tools |
| `references/` | 18 expert reference files — strategic guidance through platform integration |
| `data/` | 5 JSON files: incompatibility catalog, analyzer/query mappings, sizing heuristics, workflow prompts |
| `steering/` | 7 docs: accuracy, incompatibilities, index design, query translation, sizing, stakeholders, metrics interpretation |

### Deterministic Tools (`scripts/`)

| Module | Purpose |
|--------|---------|
| `skill.py` | Core advisor: session management, schema/query conversion, checklist, report, Solr inspection |
| `schema_converter.py` | Solr XML/JSON schema to OpenSearch mappings |
| `query_converter.py` | Solr query syntax to OpenSearch Query DSL |
| `mcp_server.py` | FastMCP server exposing 18 tools (conversion, inspection, AWS knowledge) |
| `solr_inspector.py` | 6 read-only Solr API methods (schema, metrics, luke, mbeans, collections, system) |
| `storage.py` | Session state persistence (in-memory + file backends) |
| `report.py` | Migration report generation |

### Tests and Evaluation

| Suite | Count | What it covers |
|-------|-------|----------------|
| Unit tests (`tests/test_*.py`) | ~230 | Converters, skill, storage, MCP, inspector, eval validation |
| Integration tests (`tests/integration/`) | ~100 | Golden scenarios, artifact integrity, doc consistency |
| Scenario evals (`tests/scenario-evals/`) | 119 scenarios | 4 datasets: golden, stump-the-chumps, Solr features, advisor interactions |
| Skill impact (`tests/skill-impact/`) | 4 tiers | T1 deterministic through T4 full LLM+MCP |
| Conversational eval (`tests/conversational-eval/`) | 12 steps | Sequential multi-turn workflow validation |
| Connected demo (`tests/connected/`) | Live Solr | Docker-based e-commerce demo with 200K docs |

### Worked Examples

| Example | Complexity | Purpose |
|---------|------------|---------|
| `examples/techproducts-demo/` | 2/5 | Smallest complete example (teaching) |
| `examples/hello-migration/` | 1/5 | Minimal migration walkthrough |
| `examples/drupal-solr-opensearch-demo/` | 3/5 | Drupal-specific intake and assessment |
| `examples/northstar-enterprise-demo/` | 4/5 | Realistic enterprise migration |
| `examples/migration-companion-demo/` | N/A | Companion artifact templates (risk register, go/no-go, cutover) |

### Consulting Playbook (`playbook/`)

| File | Purpose |
|------|---------|
| `intake-template.md` | Session 1 structured intake (~59 questions) |
| `interview-guide.md` | Sessions 2-3 expert interview |
| `assessment-kit/` | 11 reusable templates (risk rubric, go/no-go, success criteria, etc.) |

---

## Dev Loop (for content iteration)

1. **Edit content:** Modify `references/*.md` or `SKILL.md`
2. **Ad-hoc test:** Ask a question in your Claude session (reference edits are picked up immediately; SKILL.md changes need a session restart)
3. **Unit tests:** `python3.12 -m pytest tests/ -q`
4. **Eval baseline check:** `python3.12 tests/scenario-evals/run_eval_tasks.py --baseline tests/scenario-evals/baselines/golden_scenarios_baseline.json --fail-on-regression`
5. **4-tier eval:** `cd tests/skill-impact && bash run_eval.sh --tier 1` (tiers 2+ require API key)
6. **Conversational eval:** `cd tests/conversational-eval && bash run_eval.sh` (requires API key)
