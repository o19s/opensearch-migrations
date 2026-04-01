# Solr to OpenSearch Migration Advisor — Discussion Draft

> **This branch is NOT a deliverable.** It exists solely to help us define,
> focus, and refine what the deliverable should be. Everything here — the code,
> the tests, the docs — is a **strawman meant to be challenged, rewritten, or
> thrown away** during discussion.
>
> **What's useful here:**
> - The **README** and **[DELIVERABLES.md](DELIVERABLES.md)** are draft proposals
>   for scope and structure — read them to react to, not to accept.
> - The **test suite** (`tests/test_deliverables.py`) is a strawman specification
>   of what "done" looks like — run it to see what we think needs building, then
>   argue about whether we're right.
> - The **code and packaging** are placeholder implementations showing one possible
>   approach — they demonstrate feasibility, not final architecture.
>
> **How to use this branch:** Read it, run it, then tell us what's wrong, what's
> missing, and what shouldn't be here. The goal is a sharper, more detailed
> deliverable definition — not approval of what's already written.
>
> **Run `pytest tests/test_deliverables.py -v`** to see the strawman spec — **76
> passing** (one possible implementation exists) and **21 failing** (our best
> guess at what still needs building — challenge these too).

## What This Demo Does

Give it a Solr schema (XML, JSON, or from a live instance) and it produces a
migration report with:

- **Detected incompatibilities** grouped by severity (Breaking / Behavioral / Unsupported)
- **Actionable recommendations** for each finding
- **A 5-stage migration plan** with prerequisites, success criteria, and stop conditions
- **Blockers** surfaced from Breaking/Unsupported incompatibilities
- **Implementation points** and cost estimates

Against the included e-commerce demo schema (22 fields, 7 copyFields, deprecated
TrieIntField, phonetic/edge-ngram/synonym analyzers, spatial fields), the advisor
detects **19+ incompatibilities** across 8 detection rules.

### Quick Demo (no Docker required)

```bash
cd AIAdvisor/skills/solr-opensearch-migration-advisor
uv pip install -e ".[dev]"

# Run the test suite (198 tests, ~1 second)
pytest

# Generate a report from the demo schema
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from skill import SolrToOpenSearchMigrationSkill
from storage import InMemoryStorage

skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
with open('tests/connected/solr-demo/conf/schema.xml') as f:
    skill.handle_message(f'Convert this schema: {f.read()}', 'demo')
print(skill.generate_report('demo'))
"
```

### Full Demo (Docker + live Solr)

```bash
# Start Solr, load 10K products, inspect, and generate report
bash tests/connected/run_demo.sh --quick
```

---

## How This Maps to the Engagement Deliverables

The table below maps each deliverable from the engagement overview to its current
state in this branch. Use this to identify gaps, challenge scope, and decide
priorities.

### Initiative 1: Knowledge Base [P0]

| Deliverable | Status | Implementation |
|---|---|---|
| **Incompatibility catalog** | Implemented | `steering/incompatibilities.md` (263 lines) — 18 categorized incompatibilities across Query, Feature, Infrastructure, and Plugin gaps. Each has severity, code examples, and concrete remediation. |
| **Single-query translation** | Implemented | `steering/query_translation.md` (419 lines) — Standard, DisMax, eDisMax, spatial, MLT, aggregations, deep pagination, streaming expressions. |
| **Index design** | Implemented | `steering/index_design.md` (285 lines) — field type mappings, analyzer chains, copyField→copy_to, dynamic templates, nested docs, anti-patterns. |
| **Sizing and capacity planning** | Implemented | `steering/sizing.md` (226 lines) — shard sizing formulas, replica strategy, JVM heap, traffic patterns, node roles. |
| **User customization questions** | Implemented | `steering/stakeholders.md` (97 lines) — 6 stakeholder roles with role-specific question sets and priority ordering. |
| **Additional steering** | Implemented | `steering/accuracy.md`, `steering/relevance.md`, `steering/client_migration.md` — accuracy-first principles, BM25 tuning, client library migration paths. |

**Total: 8 steering documents, ~1,600 lines of encoded migration expertise.**

> **Discussion point:** The knowledge base is the most complete part of the
> deliverable. Are there topics missing? Is the depth right? The steering docs
> are bundled as data files alongside the core (not baked into code), so they
> can be updated independently — per the packaging requirement.

### Initiative 2: Agent System

| Deliverable | Priority | Status | Implementation | Notes |
|---|---|---|---|---|
| **Transport-agnostic core** | P0 | Implemented | `scripts/skill.py` — `SolrToOpenSearchMigrationSkill` class with `handle_message(message, session_id) -> str` interface. No HTTP, MCP, or protocol awareness. | The core is a plain Python class. Each deployment target wraps it. |
| **Pluggable storage interface** | P0 | Implemented | `scripts/storage.py` — `StorageBackend` ABC with `_save_raw`, `_load_raw`, `delete`, `list_sessions`. Two built-in backends: `InMemoryStorage`, `FileStorage`. | Adding a DynamoDB or S3 backend requires implementing 4 methods. |
| **Persistent memory store** | P1 | Implemented | `SessionState` dataclass preserves conversation history, discovered facts, migration progress (step number), incompatibilities, and client integrations across sessions. | Session files are human-readable JSON. |
| **Migration report** | P0 | Implemented | `scripts/report.py` + `scripts/skill.py:generate_report()` — Markdown report with 7 sections. | See [Report Sections](#what-the-report-covers) below. |
| **Incompatibility detection** | P0 | **Implemented (this branch)** | `scripts/incompatibility_detector.py` — 8 detection rules, runs automatically on schema conversion. | See [Detection Rules](#incompatibility-detection-rules) below. |
| **Schema conversion** | P0 | Implemented | `scripts/schema_converter.py` — XML and JSON → OpenSearch mapping. Handles field types, attributes, dynamic fields. | |
| **Query conversion** | P0 | Implemented | `scripts/query_converter.py` — Standard parser queries → Query DSL. Boolean, range, wildcard, phrase, match-all. | eDisMax falls back to `query_string` (documented limitation). |
| **Live Solr inspection** | P0 | Implemented | `scripts/solr_inspector.py` — read-only Schema, Metrics, MBeans, Luke, Collections, System APIs. | |
| **Conversational workflow** | — | Not implemented | SKILL.md defines a 7-step workflow (Steps 0-6) but `handle_message()` uses keyword-matching, not a state machine. | See [What's Not Here Yet](#whats-not-here-yet). |

### Initiative 3: Packaging

| Deliverable | Priority | Status | Implementation |
|---|---|---|---|
| **OpenSearch Migration Assistant integration** | P0 | Not started | No adapter exists yet. The core's `handle_message(message, session_id) -> str` interface is designed for this. |
| **MCP server** | P0 | Implemented (stub) | `scripts/mcp_server.py` — exposes all skill methods as MCP tools over stdio. Works end-to-end. Marked as proof-of-concept pending production hardening. |
| **Kiro power** | P1 | Implemented | `.kiro/skills/solr-to-opensearch/` with steering context, hooks, and MCP config. Auto-discovers in Kiro IDE. |
| **Standalone web app** | P2 | Not started | — |
| **Multi-IDE packaging** | — | Scaffolded | Config stubs for Cursor (`.cursorrules`), Claude Code (`CLAUDE.md`), GitHub Copilot (`.github/copilot-instructions.md`), Gemini (`GEMINI.md`). |

---

## What the Report Covers

The migration report (generated by `generate_report()`) includes these sections:

1. **Incompatibilities** — grouped by severity (Breaking → Unsupported → Behavioral),
   with category, description, and recommendation for each. Breaking/Unsupported
   items trigger an "Action required" callout.
2. **Client & Front-end Impact** — grouped by kind (libraries, UI, HTTP, other).
   Currently populated manually; auto-detection requires the conversational workflow.
3. **Stage Plan** — 5 stages (Target Validation → Sample Backfill → Full Backfill →
   Application Integration Validation → Staged Cutover), each with objective,
   prerequisites, actions, success criteria, and stop conditions. Breaking
   incompatibilities are injected into Stage 1 prerequisites.
4. **Major Milestones** — infrastructure setup, schema migration, data re-indexing,
   application migration, parallel testing and cutover.
5. **Potential Blockers** — auto-populated from Breaking/Unsupported incompatibilities
   plus schema analysis status.
6. **Implementation Points** — concrete technical tasks (copy_to migration, client
   library replacement, etc.) plus any customizations collected during the session.
7. **Cost Estimates** — infrastructure and effort estimates (currently templated;
   cluster-specific sizing requires the conversational workflow).

## Incompatibility Detection Rules

The detector (`scripts/incompatibility_detector.py`) runs 8 rules against every
schema it processes:

| # | Rule | Severity | What it catches |
|---|------|----------|-----------------|
| 1 | Deprecated Trie fields | Breaking | TrieIntField, TrieDateField, TrieLongField, TrieFloatField, TrieDoubleField |
| 2 | copyField directives | Breaking | Each source→dest pair (OpenSearch has no copyField; requires `copy_to`) |
| 3 | Complex analyzers | Behavioral | Phonetic (DoubleMetaphone), EdgeNGram, Synonym filters, plus any filter not in the safe list |
| 4 | Spatial field types | Behavioral | LatLonPointSpatialField, SpatialRecursivePrefixTreeFieldType (coordinate order differs) |
| 5 | Dynamic field patterns | Behavioral | Each `<dynamicField>` (OpenSearch uses different matching syntax) |
| 6 | Scoring model change | Behavioral | TF-IDF → BM25 (always emitted — every migration faces this) |
| 7 | Unsupported field types | Unsupported | ICUCollationField, EnumField, ExternalFileField, PreAnalyzedField, CurrencyFieldType |
| 8 | multiValued fields | Behavioral | Fields with multiValued="true" (OpenSearch arrays are implicit) |

> **Implementation choice:** Detection is deterministic (no LLM required). This
> means T1 (the cheapest eval tier) produces real findings. The LLM tiers (T2-T4)
> can add reasoning on top, but the baseline is always reliable.

---

## Implementation Choices Worth Discussing

### Deterministic detection vs. LLM-driven analysis

The incompatibility detector is pure Python pattern-matching, not LLM inference.
This was intentional:

- **Reproducible:** Same schema always produces the same findings. No temperature variance.
- **Fast and free:** No API calls. Runs in milliseconds.
- **Testable:** 16 unit tests cover every rule. The demo schema is a comprehensive integration test.
- **Composable:** LLM tiers (T2-T4) can enhance the deterministic baseline with reasoning, but the baseline is always there.

The trade-off: novel or ambiguous incompatibilities won't be caught without LLM
reasoning. The steering documents encode the knowledge for the LLM to use, but
the deterministic detector handles the mechanical checks.

### Schema-first, not conversation-first

This demo prioritizes "give me a schema, get a useful report" over the full 7-step
conversational workflow. The reasoning:

- The schema is the highest-value input. Most incompatibilities are detectable from
  the schema alone.
- A useful report from a single input is more demonstrable than a multi-turn
  conversation that requires user participation.
- The conversational workflow (stakeholder identification, query collection, client
  integration discovery, sizing) adds value but depends on user input that can't
  be demoed non-interactively.

### Steering docs as data files

Steering documents live in `steering/` as Markdown files, not compiled into code.
They're loaded at runtime by the skill constructor. This means:

- The knowledge base can be updated without code changes or releases.
- Different deployment contexts can bundle different steering sets.
- LLM-powered tiers receive the steering docs as context, while the deterministic
  tier uses the structured rules in `incompatibility_detector.py`.

### Pluggable storage with typed session state

The storage layer uses a typed `SessionState` dataclass (not raw dicts) with a
pluggable backend behind a 4-method ABC. This was a deliberate choice over simpler
approaches:

- `Incompatibility`, `ClientIntegration`, and `MigrationStage` are first-class
  data types with serialization. This makes the report generator's job trivial.
- The ABC (`StorageBackend`) has only `_save_raw`, `_load_raw`, `delete`,
  `list_sessions`. Adding a DynamoDB, S3, or database backend is straightforward.
- Session files are human-readable JSON, making debugging easy.

---

## What's Not Here Yet

These are known gaps between this demo and the full deliverable. They're listed
here to focus discussion on whether and when they should be built.

| Gap | Why it's not here | What it would take |
|-----|-------------------|--------------------|
| **Conversational workflow (Steps 0-6)** | Requires multi-turn state machine; this demo prioritizes single-shot value. | State machine in `handle_message()` checking `session.progress`, prompting for next input, validating prerequisites. |
| **Client integration auto-detection** | Client libraries are a user-provided input — can't be reliably inferred from a schema or Solr API. | Needs the conversational workflow (Step 6) to ask the user. |
| **Stakeholder-aware report tailoring** | Role collection requires conversation (Step 0). | Store role in session, reorder/filter report sections by role. |
| **Cluster-specific sizing** | Requires user-provided topology (node count, doc count, QPS). | Needs conversational workflow (Step 5) + sizing calculations from steering doc. |
| **OpenSearch Migration Assistant integration** | P0 deployment target, not yet started. | Thin adapter wrapping the core's `handle_message` interface. |
| **Standalone web app** | P2; lowest priority. | Minimal chat UI wrapping the core. |
| **solrconfig.xml analysis** | The demo analyzes `schema.xml` only, not `solrconfig.xml` (request handlers, plugins, update chains). | New parser + detection rules for solrconfig elements. |

---

## Project Structure

```
scripts/
  skill.py                    # Transport-agnostic core (facade)
  incompatibility_detector.py # 8 deterministic detection rules
  schema_converter.py         # Solr XML/JSON → OpenSearch mapping
  query_converter.py          # Solr query syntax → Query DSL
  report.py                   # Markdown report generator
  storage.py                  # SessionState + pluggable backends
  solr_inspector.py           # Read-only Solr API client
  mcp_server.py               # MCP server (proof-of-concept)

steering/                     # Knowledge base (8 docs, ~1,600 lines)
  accuracy.md                 # Accuracy-first principles
  client_migration.md         # Language-specific client migration paths
  incompatibilities.md        # Categorized incompatibility catalog
  index_design.md             # Schema mapping and analyzer guidance
  query_translation.md        # Query pattern translation reference
  relevance.md                # BM25 tuning and scoring guidance
  sizing.md                   # Cluster sizing heuristics
  stakeholders.md             # Role definitions and question sets

tests/
  test_incompatibility_detector.py  # 16 tests for detection rules
  test_skill.py                     # 33 tests for the core skill
  test_schema_converter.py          # Schema conversion tests
  test_query_converter.py           # Query conversion tests
  test_report.py                    # Report rendering tests
  test_storage.py                   # Storage and serialization tests
  test_mcp_server.py                # MCP server smoke tests
  test_kiro_packaging.py            # Kiro integration tests
  test_ide_packaging.py             # Multi-IDE config tests
  connected/                        # Docker-based live Solr demo
  report-eval/                      # 4-tier promptfoo evaluation framework
```

**198 tests total**, all passing. Test suite runs in ~1 second.

## Evaluation Framework

The `tests/report-eval/` directory contains a 4-tier evaluation framework using
[promptfoo](https://promptfoo.dev/) that measures report quality across tiers:

| Tier | What it tests | LLM required? | Cost |
|------|---------------|---------------|------|
| **T1** | Deterministic: MCP tools only (schema conversion + report generation) | No | Free |
| **T2** | LLM + skill + pre-converted mapping | Yes (Claude) | API cost |
| **T3** | LLM + skill, no pre-converted mapping (hardest) | Yes (Claude) | API cost |
| **T4** | Full integration: Claude Code + MCP tools | Yes (Claude Code) | API cost |

Assertions cover schema mapping correctness, report section completeness,
incompatibility detection, stage plan structure, and qualitative rubrics.

---

## Running the Tests

```bash
cd AIAdvisor/skills/solr-opensearch-migration-advisor
uv pip install -e ".[dev]"
pytest -v
```

## Example Prompts

For interactive use (Kiro, Claude Code, or any MCP client):

- "Help me migrate from Solr to OpenSearch."
- "Convert this Solr schema to OpenSearch mapping: `<schema>...</schema>`"
- "Translate this Solr query to OpenSearch: `title:opensearch AND price:[10 TO 100]`"
- "Generate a migration report for my session."
- "Show me the migration checklist."
