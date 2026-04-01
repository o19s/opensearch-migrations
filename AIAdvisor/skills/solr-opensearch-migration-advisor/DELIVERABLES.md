# Solr Migration Advisor — Deliverables Alignment

> **DISCUSSION DRAFT — NOT A DELIVERABLE**
>
> **Audience:** Internal (Daniel, Eric, Jeff). Not for Amazon/external distribution.
>
> **What this is:** Our best guess at what Amazon expects, mapped to placeholder
> implementations that show one possible approach. Every row in the tables below
> is a strawman — the status, the interpretation, and the implementation choices
> are all meant to be challenged. The goal is to leave this conversation with a
> sharper, agreed-upon definition of what we're actually building.
>
> **What this is NOT:** A status report on a finalized plan. The code behind
> these rows is exploratory — it demonstrates feasibility and surfaces questions,
> not final architecture.
>
> **Living spec:** The test suite `tests/test_deliverables.py` mirrors this
> document. Passing tests = "one possible implementation exists." Failing tests =
> "our guess at what's still needed — argue with us about whether we're right."

---

## Project Delivery Summary

We're building a migration advisor that helps Solr users plan and execute a move
to OpenSearch. The target user has a working Solr deployment but limited expertise
with either system — they inherited it, did a minimal implementation, or are
evaluating the migration for the first time.

The engagement has three initiatives: (1) a **knowledge base** of steering
documents encoding migration expertise, (2) a **transport-agnostic agent system**
that uses this knowledge to produce actionable migration reports, and (3)
**packaging** for multiple deployment contexts (Migration Assistant, MCP, Kiro,
web app).

This branch is a working prototype — not mockups. The knowledge base is largely
complete. The agent system has functional schema/query conversion, incompatibility
detection, session persistence, and report generation. The conversational workflow
(multi-turn guided migration) is specified but not implemented. Packaging has
working MCP and Kiro integrations; Migration Assistant and web app are not started.

**Run `pytest tests/test_deliverables.py -v` to see exactly what's done and
what's not.**

---

## Initiative 1: Knowledge Base [P0]

Amazon's requirement: *"A knowledge base, delivered as a set of steering documents,
that encodes migration expertise for the AI advisor."*

Our approach: 8 Markdown files in `steering/`, loaded at runtime as data files
(not compiled into code). The LLM tiers receive these as context; the deterministic
tier uses structured rules derived from them.

| Amazon Requirement | Our Implementation | Status | Notes |
|---|---|---|---|
| **Incompatibility catalog** — Known gaps, unsupported features, behavioral differences | `steering/incompatibilities.md` (263 lines). 18 categorized issues across Query, Feature, Infrastructure, Plugin gaps. Each has severity, code examples, remediation. | Done | Also implemented as deterministic detection rules in `incompatibility_detector.py` (8 rules). The steering doc is richer (prose + examples); the detector is mechanical + testable. Both serve different tiers. |
| **Single-query translation** — Converting Solr queries (dismax, edismax, function queries) to Query DSL | `steering/query_translation.md` (419 lines). Covers Standard, DisMax, eDisMax, spatial, MLT, aggregations, deep pagination, streaming expressions. | Done | The deterministic query converter (`query_converter.py`) handles Standard parser patterns. eDisMax falls back to `query_string` — documented limitation. The steering doc covers what the converter can't do mechanically. |
| **Index design** — Schema mapping, analyzer chains, field type conversions | `steering/index_design.md` (285 lines). Field type mappings, analyzer chains, copyField→copy_to, dynamic templates, nested docs, anti-patterns. | Done | The schema converter (`schema_converter.py`) handles mechanical conversion. The steering doc covers judgment calls the converter can't make (when to use nested vs flat, analyzer chain equivalences). |
| **Sizing and capacity planning** — Heuristics for translating Solr topologies to OpenSearch sizing | `steering/sizing.md` (226 lines). Shard sizing formulas, replica strategy, JVM heap, traffic patterns, node roles. | Done | Steering doc provides heuristics but the agent system doesn't yet implement sizing calculations. Needs the conversational workflow (Step 5) to collect user topology, then apply the formulas. |
| **User customization questions** — Curated question sets to uncover custom handlers, plugins, auth, operational constraints | `steering/stakeholders.md` (97 lines). 6 stakeholder roles with role-specific priorities and question sets. | Done | Questions are defined but the conversational workflow doesn't ask them yet. The SKILL.md workflow (Steps 0, 4, 5, 6) specifies exactly when to ask what. Implementation is the gap, not the knowledge. |
| **Steering docs as data files** — *"Bundled as data files alongside the core rather than baked into code"* | `steering/` directory, loaded at runtime by `skill.py:_load_steering_docs()`. | Done | Steering docs can be updated without code changes. Different deployments could bundle different sets. |
| **Additional steering** — accuracy principles, relevance tuning, client migration paths | `steering/accuracy.md` (24 lines), `steering/relevance.md` (107 lines), `steering/client_migration.md` (169 lines). | Done | These weren't explicitly requested but fill gaps. `accuracy.md` is the "never guess" principle. `relevance.md` covers BM25 tuning. `client_migration.md` covers SolrJ→opensearch-java, pysolr→opensearch-py, etc. |

**Our read:** The knowledge base feels like the most complete initiative. 8 documents,
~1,600 lines. But we're guessing at depth and coverage — is this what Amazon
expects? Are there topics we're missing? Is the format right (Markdown prose vs.
structured data)?

---

## Initiative 2: Agent System

Amazon's requirement: *"An agent system capable of reasoning about Solr migrations...
transport-agnostic core library with a clean interface: it accepts a message and a
session handle and returns a response."*

| Amazon Requirement | Our Implementation | Status | Notes |
|---|---|---|---|
| **[P0] Transport-agnostic core** — *"A library with a simple call interface that encapsulates all agentic reasoning, with no protocol or deployment assumptions."* | `scripts/skill.py` — `SolrToOpenSearchMigrationSkill` class. Interface: `handle_message(message, session_id) -> str`. No HTTP, MCP, or protocol awareness. | Done | Each deployment target (MCP server, Kiro, future web app) is a thin wrapper around this class. The class has zero dependencies on any transport. |
| **[P0] Pluggable storage interface** — *"A defined storage contract (load, save, list sessions) so each deployment target can supply its own backend."* | `scripts/storage.py` — `StorageBackend` ABC with 4 methods: `_save_raw`, `_load_raw`, `delete`, `list_sessions`. Two built-in: `InMemoryStorage`, `FileStorage`. | Done | Adding DynamoDB, S3, or database backend = implement 4 methods. The ABC handles typed serialization (SessionState ↔ dict) so backends only deal with raw JSON. |
| **[P1] Persistent memory store** — *"Session-resumable memory that preserves conversation state, discovered facts, and migration progress."* | `SessionState` dataclass with `history`, `facts`, `progress`, `incompatibilities`, `client_integrations`. Serialized to JSON, loaded by session_id. | Done | Sessions survive process restarts (FileStorage). Human-readable JSON files. Full conversation history + all discovered state. Open question from Amazon's doc: *"How much we do here for the first release is up for debate."* |
| **[P0] Migration report — Major milestones** | `report.py` + `skill.py:generate_report()`. 5 milestones: infrastructure setup, schema migration, data re-indexing, application migration, parallel testing/cutover. | Done | Milestones are currently static. Could be made dynamic based on what the session discovered (e.g., skip "application migration" milestone if no client integrations recorded). |
| **[P0] Migration report — Surface blockers** | Breaking and Unsupported incompatibilities auto-surface in Potential Blockers section. Schema-not-analyzed is also flagged. | Done | Blockers are derived from incompatibility detection — not manually authored. As detection improves, blockers improve automatically. |
| **[P0] Migration report — Implementation points** | Implementation points section with concrete technical tasks. Customizations from session facts are appended. | Done | Currently semi-static ("Map Solr field types...", "Replace copyField...", "Update client libraries...") plus any customizations collected. Would benefit from being more dynamic based on detected incompatibilities. |
| **[P0] Migration report — Front-end integration** | Client & Front-end Impact section in report, grouped by kind (library, UI, HTTP, other). `ClientIntegration` dataclass with name, kind, notes, migration_action. | Partial | The report section and data model are complete. But nothing *collects* client integrations automatically — requires the conversational workflow (Step 6) to ask the user. Currently only populated if manually added to session state. |
| **[P0] Migration report — Cost estimates** | Cost Estimates section in report with Infrastructure and Effort line items. | Partial | Currently templated ("Estimated 10% increase...", "Moderate 2-4 weeks..."). Not personalized to the user's cluster size, doc count, or complexity. Needs sizing calculations from Step 5. |
| **Schema conversion** | `schema_converter.py` — XML and JSON → OpenSearch mapping. Handles field types, stored/indexed attributes, dynamic fields. | Done | Handles the mechanical conversion well. Doesn't attempt analyzer chain translation (that's a judgment call for the LLM tiers). |
| **Query conversion** | `query_converter.py` — Standard parser → Query DSL. Boolean, range, wildcard, phrase, match-all. | Done | eDisMax (qf, pf, bq, bf) falls back to `query_string`. This is the "80% of straightforward queries" from the engagement overview. The remaining 20% needs LLM reasoning + steering docs. |
| **Incompatibility detection** | `incompatibility_detector.py` — 8 deterministic rules. Runs automatically on every schema conversion. | Done | Detects deprecated Trie fields, copyField directives, complex analyzers, spatial types, dynamic fields, BM25 scoring change, unsupported types, multiValued fields. 19+ findings on the demo schema. |
| **Live Solr inspection** | `solr_inspector.py` — read-only Schema, Metrics, MBeans, Luke, Collections, System APIs. | Done | Can connect to a running Solr instance and pull everything needed for a migration assessment. Used in the connected demo. |
| **Conversational workflow (Steps 0-6)** — *"The agent system should be capable of... asking targeted questions about the user's front-end code."* | SKILL.md defines 7-step workflow. `handle_message()` currently uses keyword matching, not a state machine. | Not Done | This is the biggest gap. The workflow is fully *specified* (SKILL.md is 460 lines of detailed step-by-step instructions) but not *implemented* in code. The current `handle_message()` detects keywords and routes to converters — it doesn't guide the user through steps, validate prerequisites, or prompt for missing info. |
| **Stakeholder-aware guidance** — *Role-specific depth and focus* | Stakeholders steering doc defines 6 roles. SKILL.md has per-step stakeholder guidance. | Not Done | Role collection requires Step 0 of the conversational workflow. Report tailoring (reordering sections by role) is not implemented. |
| **Client integration gathering** — *"Ask targeted questions about the user's front-end code"* | `SessionState.add_client_integration()` exists. SKILL.md Step 6 defines the prompts and mapping table. | Not Done | Data model is ready. The workflow step to ask the user isn't implemented. |
| **Cluster sizing calculations** — *Apply sizing heuristics to user's topology* | Sizing steering doc has the formulas. No code implements them. | Not Done | Need Step 5 of conversational workflow to collect topology, then apply `sizing.md` heuristics to produce concrete recommendations. |
| **solrconfig.xml analysis** — *Custom request handlers, plugins, update chains* | Not started. Only `schema.xml` is analyzed. | Not Done | Daniel's doc mentions "custom request handlers, plugins, authentication schemes." The incompatibility catalog covers these conceptually but no code parses or detects them from config. |
| **Stage plan** — *Suggested sequencing with prerequisites and stop conditions* | 5-stage plan with prerequisites, actions, success criteria, stop conditions. Breaking incompatibilities inject into Stage 1 prereqs. Client integrations inject into Stage 4 actions. | Done | This exceeds what was explicitly requested (Amazon said "milestones and suggested sequencing"). We added stop conditions and success criteria to make it more actionable. |

**Our read:** The mechanical pieces (convert, detect, report) have placeholder
implementations. The conversational pieces (guide, ask, tailor) are specified
in SKILL.md but not implemented in code. The big open question: does Amazon want
an "agent that reasons through a multi-turn workflow" or a "tool that converts
on demand and produces a report"? Those are very different amounts of work, and
this draft assumes the latter is a viable first release.

---

## Initiative 3: Packaging

Amazon's requirement: *"The advisor must be packaged for multiple deployment
contexts... each packaging target is a thin adapter that wraps the transport-agnostic
agent core."*

| Amazon Requirement | Our Implementation | Status | Notes |
|---|---|---|---|
| **[P0] OpenSearch Migration Assistant integration** — *"Deploy the agent as a component of the Migration Assistant, accessible via a queryable endpoint."* | Not started. | Not Done | The core's `handle_message(message, session_id) -> str` interface is designed for this — the adapter would translate HTTP requests to this call. We need clarity on the Migration Assistant's expected integration point (REST endpoint? gRPC? plugin API?). |
| **[P0] MCP server** — *"Expose the agent core as an MCP server so it can be consumed by any MCP-compatible AI tool or IDE."* | `scripts/mcp_server.py` — FastMCP server exposing all skill methods + Solr inspection tools over stdio. | Done (stub) | Works end-to-end. Marked as proof-of-concept pending production hardening (richer error handling, streaming). The MCP tools are: `convert_schema_xml`, `convert_schema_json`, `convert_query`, `handle_message`, `get_migration_checklist`, `generate_report`, plus 7 Solr inspection tools. |
| **[P1] Kiro power** — *"Package the MCP server as a Kiro power for in-IDE migration assistance."* | `.kiro/skills/solr-to-opensearch/` with symlink, steering context, hooks, MCP config. Auto-discovers in Kiro. | Done | Schema-assist hook auto-fires when `schema.xml` is dropped into the project. Steering docs loaded via `.kiro/steering/` with `inclusion: always`. |
| **[P2] Standalone web application** — *"A lightweight web app with a minimal chat interface."* | Not started. | Not Done | Lowest priority per Amazon's doc. The transport-agnostic core makes this straightforward — just a chat UI calling `handle_message()`. |
| **Multi-IDE packaging** | Config stubs for Cursor (`.cursorrules`), Claude Code (`CLAUDE.md`), GitHub Copilot (`.github/copilot-instructions.md`), Gemini (`GEMINI.md`). | Partial | Stubs exist and reference the skill. Not deeply tested in each IDE. Kiro is the most complete integration. |

**Our read:** MCP and Kiro have placeholder implementations. Migration Assistant
(the P0) is not started — we need an integration spec from Amazon before we can
build the adapter. Web app is P2 and straightforward when needed. The multi-IDE
stubs are scaffolding to show portability, not tested integrations.

---

## Evaluation Framework

Not explicitly in Amazon's deliverables doc, but we built it to prove the skill
adds value and to catch regressions.

| What | Implementation | Status |
|---|---|---|
| **Unit tests** | `tests/test_*.py` — 198 tests covering all modules. ~1 second. | Done |
| **Deliverables TDD spec** | `tests/test_deliverables.py` — tests mirroring this document. Failures = work remaining. | Done |
| **4-tier report eval** | `tests/report-eval/` — promptfoo-based. T1 (deterministic) through T4 (full Claude Code + MCP). | Done |
| **Connected demo** | `tests/connected/` — Docker Solr, 200K docs, traffic gen, live inspection → report. | Done |
| **Multi-run stability** | Repeated T2/T3 runs checking LLM tier consistency. | Done |

---

## Key Open Questions

These need decisions before the next delivery milestone:

1. **Conversational workflow scope for first release.** Amazon says persistent
   memory is "up for debate." How much of Steps 0-6 do we implement vs. leave
   as steering doc guidance for the LLM? The mechanical detection (current approach)
   catches schema-level issues without conversation. The conversational workflow
   catches user-specific issues (client libraries, plugins, sizing) that require
   asking questions.

2. **Migration Assistant integration spec.** This is P0 but we have no spec for
   the integration point. REST endpoint? Plugin API? What does the Migration
   Assistant expect to call?

3. **solrconfig.xml analysis.** Daniel's doc mentions plugins and custom handlers.
   We analyze `schema.xml` thoroughly but don't touch `solrconfig.xml`. How
   important is this for first release?

4. **Report personalization vs. static templates.** Current cost estimates and
   milestones are generic. Making them cluster-specific requires the conversational
   workflow to collect topology data. Is the generic version acceptable for first
   release?

5. **"Core Solr knowledge is a deliverable; OpenSearch reasoning is not."** We
   integrated the AWS Knowledge MCP Server for OpenSearch-side answers. Is this
   the right boundary? Our steering docs contain OpenSearch-specific guidance
   (analyzer equivalences, Query DSL patterns) — is that in scope or should we
   lean harder on the AWS Knowledge server?
