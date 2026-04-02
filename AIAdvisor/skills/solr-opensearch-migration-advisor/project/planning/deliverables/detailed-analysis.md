# OSC Deliverables: Detailed Analysis

Generated 2026-03-21, updated 2026-03-22 with deep upstream architecture analysis.

See also: [upstream-architecture.md](upstream-architecture.md) for full upstream internals.

**Sources:**
- Deliverables doc (Google Docs): https://docs.google.com/document/d/1aTR_E-0JwPtEkZQO5HA__afNwSlCS8_B-WgyPUIYn_Y/
- Upstream repo: https://github.com/opensearch-project/opensearch-migrations
- O19s fork (Jeff's agent code): https://github.com/o19s/opensearch-migrations/tree/main/AIAdvisor/solr-opensearch-migration-advisor
- Local knowledge base: this repo (agent99)

---

## 1. Knowledge Base [P0]

### 1.1 Incompatibility Catalog

**What:** Documents cataloging known gaps, unsupported features, and behavioral differences between Solr and OpenSearch so the advisor can flag them early in a migration conversation.

**Current state in agent99:** Partially covered across `08-edge-cases-and-gotchas.md` (30+ curated external links, long-tail issues), `solr-concepts-reference.md` (feature audit, equivalence map, complexity matrix), and the "9 Critical Differences" table in SKILL.md. The `consulting-concerns-inventory.md` has ~200 items across 20 risk groups.

**What Jeff's code needs:** `skill.py` tracks incompatibilities in `facts.incompatibilities` with categories: Breaking, Behavioral, Unsupported. The steering docs need to feed into this programmatic detection — not just be human-readable.

**Gap:** The knowledge base is strong for human consumption but needs to be structured for **programmatic pattern matching** by the agent. The agent needs to detect incompatibilities from schema XML and query patterns, not just describe them.

**Upstream context:** The Migration Assistant already has metadata migration tooling ([MetadataMigration/](https://github.com/opensearch-project/opensearch-migrations/tree/main/MetadataMigration)) that handles Elasticsearch → OpenSearch index settings/templates. The Solr advisor fills the gap where no automated Solr tooling exists upstream.

### 1.2 Single-Query Translation

**What:** Steering for converting individual Solr queries — DisMax, eDisMax, function queries, facets, spatial, MLT, spellcheck — into equivalent OpenSearch Query DSL.

**Current state in agent99:** SKILL.md has a query translation quick-reference table. `sources/opensearch-migration/` has detailed mapping docs. Jeff's `query_converter.py` does programmatic conversion.

**Known gaps documented in Jeff's SKILL.md:** eDisMax phrase boost (`pf/pf2/pf3`), streaming expressions, graph traversal, XCJF (cross-collection join), payload scoring. These are explicitly listed as "no direct equivalent."

**Key concern from deliverables doc:** Target is the 80% of query API that is "straightforward to translate." The remaining 20% needs clear incompatibility flagging, not silent failure.

**Upstream context:** The Traffic Replayer ([TrafficCapture/](https://github.com/opensearch-project/opensearch-migrations/tree/main/TrafficCapture)) captures and replays HTTP traffic for ES→OS migrations. For Solr, there's no equivalent — query translation is manual/advisory, which is exactly what this tool provides.

### 1.3 Index Design Steering

**What:** Guidance on mapping Solr schemas (schema.xml field types, analyzers, copyField, dynamic fields) to OpenSearch index mappings and analysis chains.

**Current state:** `03-target-design.md` in agent99 covers this conceptually. Jeff's `schema_converter.py` does programmatic conversion from both `schema.xml` and Solr Schema API JSON to OpenSearch mapping JSON.

**Critical detail:** Solr's `fieldType` inheritance model (e.g., `solr.TextField` with analyzer chains) maps to OpenSearch's flat `analysis` block with named analyzers. This is a frequent source of subtle bugs — tokenizers and filters don't always have 1:1 equivalents.

**Upstream context:** The upstream [MetadataMigration/](https://github.com/opensearch-project/opensearch-migrations/tree/main/MetadataMigration) handles ES schema migration but has zero Solr awareness. Our schema converter is net-new capability.

### 1.4 Sizing & Capacity Planning

**What:** Heuristics for translating Solr cluster topologies (shard counts, replica factors, JVM configs, ZooKeeper overhead) into appropriately sized OpenSearch deployments.

**Current state in agent99:** `aws-opensearch-service.md` reference covers AWS instance types, sizing, cost models. `06-operations.md` covers monitoring, ISM, DR. SKILL.md has quick-decision tables (provisioned vs serverless, instance types).

**Critical difference to highlight:** Solr allows shard+replica colocation on the same node; OpenSearch forbids it. This means a 3-node Solr cluster with RF=2 may need 6+ OpenSearch nodes. This is called out in SKILL.md's "9 Critical Differences" but needs to be part of the automated sizing logic.

**Gap:** The agent needs **computable heuristics**, not just prose. Jeff's code doesn't yet have a sizing calculator — this is likely a P1 feature but the knowledge base inputs (the heuristics) are P0.

### 1.5 User Customization Question Sets

**What:** Curated questions the advisor should pose to uncover custom request handlers, plugins, authentication schemes, and operational constraints.

**Current state in agent99:** Extremely strong. `playbook/intake-template.md` has 59 structured questions across 9 blocks. `playbook/assessment-kit/` has 11 reusable templates including `assessment-intake-questionnaire.md`, `artifact-request-checklist.md`, `consumer-inventory-template.md`.

**How this feeds the agent:** Jeff's `skill.py` `handle_message()` routes conversations through a 7-step workflow (Steps 0-7) that includes stakeholder identification, schema acquisition, customization assessment. The question sets from agent99 need to be integrated into this flow.

**Upstream context:** The Migration Console ([migrationConsole/](https://github.com/opensearch-project/opensearch-migrations/tree/main/migrationConsole)) is interactive but oriented toward ES migrations. There's no Solr-aware questionnaire upstream.

### 1.6 Steering Docs as Bundled Data Files

**What:** Steering documents must be bundled alongside the core as data files, not baked into code, so the knowledge base can be updated independently of the agent.

**Current state:** Jeff's code loads steering docs from `steering/` and `references/` directories at init time in `skill.py`. The agent99 repo's skill is already packaged as a `.skill` zip file (`zip -r solr-to-opensearch-migration.skill SKILL.md references/`).

**This is architecturally sound.** The key requirement is that the packaging step for each deployment target (Migration Assistant, MCP, Kiro, web app) bundles these files as data, and the core discovers them via a configurable path — not hardcoded.

---

## 2. Agent System

### 2.1 [P0] Transport-Agnostic Core

**What:** A Python library with a simple call interface (`message` + `session_id` → `response`) that encapsulates all reasoning. No HTTP, MCP, or protocol awareness.

**Current state in Jeff's code:** `skill.py` defines `SolrToOpenSearchMigrationSkill` as a facade class with `handle_message(message, session_id)`. This is the core. `mcp_server.py` is a thin adapter that wraps it. This architecture is **correct and matches the deliverables doc**.

**Key methods to verify/extend:**
- `handle_message(message, session_id)` — main conversational entry
- `convert_schema_xml(schema_xml)` — schema conversion
- `convert_schema_json(schema_api_json)` — Schema API conversion
- `convert_query(solr_query)` — query translation
- `generate_report(session_id)` — migration report
- `get_migration_checklist()` — static checklist
- `get_field_type_mapping_reference()` — type mapping table

**Source:** [skill.py](https://github.com/o19s/opensearch-migrations/blob/main/AIAdvisor/solr-opensearch-migration-advisor/scripts/skill.py)

### 2.2 [P0] Pluggable Storage Interface

**What:** A defined storage contract (load, save, list sessions) so each deployment target can supply its own backend.

**Current state:** Jeff's `storage.py` defines a `StorageBackend` base and a `FileStorage` implementation that persists sessions as JSON files in `sessions/<session_id>.json`.

**What needs to happen:** The contract needs additional implementations (or at minimum, documented extension points) for:
- S3 backend (for Migration Assistant / AWS deployment)
- Database backend (for web app)
- In-memory backend (for testing)

**Session state schema** (from Jeff's code): conversation history, discovered facts, progress counters, incompatibilities, client integrations.

**Source:** [storage.py](https://github.com/o19s/opensearch-migrations/blob/main/AIAdvisor/solr-opensearch-migration-advisor/scripts/storage.py)

### 2.3 [P1] Persistent Memory Store

**What:** Session-resumable memory that preserves conversation state, discovered facts, and migration progress between sessions.

**Current state:** The `FileStorage` backend already does this — sessions serialize to JSON and reload. The deliverables doc says "how much we do here for the first release is up for debate."

**Key design question:** Is "memory" just session replay, or does it include **cross-session knowledge** (e.g., "this user's Solr cluster has 4 collections, learned in session A, available in session B")? The deliverables doc implies the latter ("preserves discovered knowledge").

**Upstream context:** The Migration Console uses AWS Parameter Store for configuration state ([deployment/cdk/opensearch-service-migration/lib/](https://github.com/opensearch-project/opensearch-migrations/tree/main/deployment/cdk/opensearch-service-migration/lib)). The advisor's session state could potentially integrate with this.

### 2.4 [P0] Migration Report

**What:** A generated report covering milestones, blockers, implementation points, front-end impact, and cost estimates.

**Current state:** Jeff's `report.py` generates reports. SKILL.md Step 7 defines the report structure. The agent99 repo has `examples/techproducts-demo/` as a worked example of what a report should look like (README, steering docs, requirements, design, tasks, MANIFEST).

**The deliverables doc specifies five report sections:**
1. Major milestones and suggested sequencing
2. Blockers (unsupported features, plugin dependencies, architectural mismatches)
3. Implementation points (code/config changes required)
4. Front-end integration assessment (client-side impact)
5. Cost estimates (infrastructure, effort, tooling/licensing)

**Gap to check:** Does Jeff's `report.py` cover all five? Cost estimation is particularly hard — this may need heuristic tables from the knowledge base rather than precise calculation.

**Source:** [report.py](https://github.com/o19s/opensearch-migrations/blob/main/AIAdvisor/solr-opensearch-migration-advisor/scripts/report.py)

### 2.5 Schema Conversion

**What:** Programmatic conversion of Solr schemas to OpenSearch index mappings.

**Current state:** Jeff's `schema_converter.py` handles both `schema.xml` and Schema API JSON input.

**Key field type mappings to verify are correct:**

| Solr | OpenSearch |
|------|-----------|
| `solr.StrField` | `keyword` |
| `solr.TextField` | `text` (with custom analyzer) |
| `solr.IntPointField` / `solr.TrieIntField` | `integer` |
| `solr.DatePointField` | `date` |
| `solr.LatLonPointSpatialField` | `geo_point` |
| `solr.BoolField` | `boolean` |

**Gotcha:** Solr's `copyField` → OpenSearch's `copy_to` is conceptually similar but syntactically different. Dynamic fields (`*_t`, `*_i`) → dynamic templates. These need thorough test coverage.

**Source:** [schema_converter.py](https://github.com/o19s/opensearch-migrations/blob/main/AIAdvisor/solr-opensearch-migration-advisor/scripts/schema_converter.py)

### 2.6 Query Conversion

**What:** Programmatic translation of Solr query syntax to OpenSearch Query DSL.

**Current state:** Jeff's `query_converter.py` handles this.

**Coverage needed per deliverables doc:**
- [x] DisMax → `multi_match` (type: `best_fields`)
- [x] eDisMax → `multi_match` with boosting
- [ ] Function queries → `function_score` / `script_score`
- [x] Facets → aggregations
- [ ] Spatial queries → geo queries
- [ ] MLT (More Like This) → `more_like_this` query
- [ ] Spellcheck → suggesters
- [ ] Highlighting → highlight API
- [ ] Grouping → `collapse` / `top_hits` aggregation

**Known no-equivalents** (from SKILL.md): streaming expressions, graph traversal, XCJF, payload scoring. These should generate incompatibility warnings.

**Source:** [query_converter.py](https://github.com/o19s/opensearch-migrations/blob/main/AIAdvisor/solr-opensearch-migration-advisor/scripts/query_converter.py)

### 2.7 Incompatibility Detection

**What:** Automated detection of features/patterns that will break or behave differently in OpenSearch.

**Current state:** Jeff's SKILL.md defines three categories:
- **Breaking** — feature doesn't exist in OpenSearch
- **Behavioral** — feature exists but works differently
- **Unsupported** — requires plugin or custom code

The skill tracks these in `facts.incompatibilities` per session.

**From agent99's knowledge base**, key incompatibilities include:
- TF-IDF → BM25 scoring change (30-40% ranking difference)
- Shard+replica colocation forbidden
- Atomic update semantics differ
- No equivalent for: streaming expressions, graph traversal, XCJF, payload scoring
- ZooKeeper-based coordination → embedded Raft
- Real-time Get semantics differ

### 2.8 Stakeholder-Aware Guidance

**What:** The advisor should tailor its output based on user role (developer, architect, ops, manager).

**Current state:** Jeff's SKILL.md Step 0 is "Stakeholder Identification." The deliverables doc says "the target user is minimally familiar with Solr" and "minimally familiar with OpenSearch."

**Implication:** Default guidance should assume low expertise. Advanced users should be able to skip basics. This is a UX concern for the conversational flow.

---

## 3. Packaging

### 3.1 [P0] OpenSearch Migration Assistant Integration

**What:** Deploy the advisor as a component of the Migration Assistant, accessible via a queryable endpoint.

**Upstream architecture:** The Migration Assistant deploys via AWS CDK ([deployment/cdk/opensearch-service-migration/](https://github.com/opensearch-project/opensearch-migrations/tree/main/deployment/cdk/opensearch-service-migration)) as an ECS cluster with services communicating over a VPC. The Migration Console is the CLI control hub.

**What this means for us:**
- The advisor needs to be containerized (Dockerfile)
- It needs a CDK construct that adds it to the existing stack (ECS service or sidecar)
- It needs an HTTP endpoint (REST API wrapping the transport-agnostic core)
- It may need to integrate with the Migration Console CLI as a subcommand

**Key upstream files to study:**
- [deployment/cdk/opensearch-service-migration/lib/](https://github.com/opensearch-project/opensearch-migrations/tree/main/deployment/cdk/opensearch-service-migration/lib) — CDK constructs
- [migrationConsole/](https://github.com/opensearch-project/opensearch-migrations/tree/main/migrationConsole) — Console architecture
- [docker-compose.yml](https://github.com/opensearch-project/opensearch-migrations/blob/main/docker-compose.yml) — Local dev stack

**Current gap:** Jeff's code is MCP stdio only. No HTTP adapter, no Dockerfile, no CDK construct yet.

### 3.2 [P0] MCP Server

**What:** Expose the agent core as an MCP server for any MCP-compatible AI tool or IDE.

**Current state:** Jeff's `mcp_server.py` already implements this using `FastMCP` from the `mcp` package. It registers 8 tools (+ 2 AWS integration tools) and runs on stdio transport.

**This is largely done.** Verification needed:
- [ ] All 8 core tools work end-to-end
- [ ] AWS knowledge search integration (`https://knowledge-mcp.global.api.aws`) works or fails gracefully
- [ ] Session persistence works across MCP tool calls
- [ ] Error handling is robust (malformed schema XML, invalid queries, etc.)

**Source:** [mcp_server.py](https://github.com/o19s/opensearch-migrations/blob/main/AIAdvisor/solr-opensearch-migration-advisor/scripts/mcp_server.py)

### 3.3 [P1] Kiro Power

**What:** Package the MCP server as a Kiro power for in-IDE migration assistance.

**Current state in agent99:** Already has a `kiro/` directory with Kiro Power configuration (symlinks to skill references). The MCP server config goes in `.kiro/settings/mcp.json`.

**What's needed:** The Kiro power should point to the MCP server (3.2) as its backend. Steering docs are already bundled behind the server. This is a thin packaging task once the MCP server is solid.

### 3.4 [P2] Standalone Web App

**What:** Lightweight web app with minimal chat interface.

**Current state:** Nothing built yet. This is lowest priority.

**Minimum viable version:** A FastAPI/Flask app with a WebSocket or SSE chat endpoint that wraps `SolrToOpenSearchMigrationSkill.handle_message()`. Static HTML/JS frontend. Could be as simple as ~200 lines.

**Upstream parallel:** The Migration Console is CLI-based, not web-based. A web UI for the advisor would be new territory relative to the upstream project.

---

## 4. Integration Concerns with Upstream

### 4.1 Contribution Pathway

The upstream `opensearch-project/opensearch-migrations` repo has **no `AIAdvisor/` directory yet**. Jeff's work exists only in the O19s fork. Key questions:

- What's the PR/contribution process for adding a new top-level directory?
- Does the upstream project have opinions on Python vs Java for new components? (The repo is 49.8% Java, 24.3% TypeScript, 16.2% Python — Python is precedented)
- Apache-2.0 licensing (Jeff's `pyproject.toml` already declares this — matches upstream)

### 4.2 CDK Stack Alignment

**Upstream CDK stack** ([deployment/cdk/opensearch-service-migration/](https://github.com/opensearch-project/opensearch-migrations/tree/main/deployment/cdk/opensearch-service-migration)) deploys:
- ECS Fargate cluster
- MSK (Kafka) for traffic capture
- OpenSearch domain
- VPC, security groups, IAM roles

**For Migration Assistant integration [P0]**, the advisor would need:
- An ECS task definition + service
- A security group rule allowing inbound from the Migration Console
- An IAM role with permissions to access session storage (S3 or DynamoDB)
- A CDK construct in `lib/` following the existing patterns

### 4.3 K8s Deployment

The upstream repo states K8s is the ["current and future development"](https://github.com/opensearch-project/opensearch-migrations/tree/main/deployment/k8s) direction. The advisor should have Helm chart / K8s manifests in addition to CDK.

### 4.4 Testing Standards

The upstream repo uses:
- Gradle for Java builds
- pytest for Python tests
- GitHub Actions CI

Jeff's code has `tests/unit/` with pytest. The agent99 repo has a multi-tier test suite. Both should align with upstream CI expectations for the contribution.

---

## 5. Jeff's Code: Detailed Gap Analysis (2026-03-22 update)

The SKILL.md in the O19s fork describes an 8-step (0-7) stakeholder-aware migration
workflow. The actual `handle_message()` is a **keyword router** that handles ~5 intents.
Steps 0, 2, 4, 5, and 6 are completely unimplemented. See
[upstream-architecture.md](upstream-architecture.md) §3 for the full step-by-step comparison.

**Module-level gaps:**
- `schema_converter.py` — no analyzer/tokenizer/filter conversion, no `copyField` → `copy_to`
- `query_converter.py` — no eDismax (`qf`/`pf`/`mm`/`bq`/`bf`), no `fq`, no facet→aggs, no spatial/MLT/spellcheck/highlighting/grouping
- `report.py` — structure is there but reports are hollow (nothing populates the data)
- `steering/` — loaded but never used by code; `stakeholders.md` is empty
- `references/` — placeholder only (`01-sample-reference.md`)

**What's solid:** `storage.py` (clean ABC, two backends, good tests), MCP server (10 tools), test suite (50+ tests).

---

## 6. Upstream Solr Work: Coordination Risk

Six active upstream PRs are adding Solr capabilities in Java (TrafficCapture layer).
Our Python advisory tools overlap but are naturally complementary: we advise and plan,
they detect and execute. See [upstream-architecture.md](upstream-architecture.md) §2.

---

## 7. Top Risks (updated 2026-03-22)

1. **The gap between SKILL.md and code is the #1 delivery risk** — the skill doc promises an 8-step workflow but the code is a keyword router. This needs to be closed before the advisor is credible.
2. **Migration Assistant integration [P0] has the most work remaining relative to its priority** — no HTTP adapter, Dockerfile, or CDK construct yet
3. **Knowledge base is strong for humans but needs restructuring for programmatic agent consumption** — the agent needs to detect incompatibilities from schema/query patterns, not just describe them in prose
4. **Upstream Solr work may create contradictions** — if upstream's Java query translation produces different results than our Python converter, users get conflicting advice. Need coordination with AndreKurait and nagarajg17.
5. **Upstream contribution pathway is undefined** — getting `AIAdvisor/` accepted into `opensearch-project/opensearch-migrations` is a dependency outside OSC's direct control
6. **Trust/debuggability patterns not yet adopted** — upstream uses audit logging, safety tiers, and graduated permissions. Our advisor has none of these yet.
