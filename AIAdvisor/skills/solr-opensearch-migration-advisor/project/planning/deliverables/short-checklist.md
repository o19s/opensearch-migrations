# OSC Deliverables: Short Checklist

Generated 2026-03-21, updated 2026-03-22 with deep upstream architecture analysis.

## A. Knowledge Base [P0]

- [ ] Incompatibility catalog (feature gaps, behavioral differences, unsupported Solr features)
- [ ] Single-query translation steering (DisMax, eDisMax, function queries → Query DSL)
- [ ] Index design steering (schema.xml → mappings, analyzers, copyField → copy_to)
- [ ] Sizing & capacity planning heuristics (shards, replicas, JVM → OpenSearch cluster sizing)
- [ ] User customization question sets (request handlers, plugins, auth, operational constraints)
- [ ] Steering docs bundled as data files (not baked into code), independently updatable

## B. Agent System

- [ ] **[P0] Transport-agnostic core** — library with `handle_message(message, session_id)` interface, no protocol assumptions
- [ ] **[P0] Pluggable storage interface** — load/save/list sessions contract; file, DB, S3 backends
- [ ] **[P1] Persistent memory store** — session-resumable state: conversation history, discovered facts, migration progress
- [ ] **[P0] Migration report generation** — milestones, blockers, implementation points, front-end impact, cost estimates
- [ ] Schema conversion (XML and Schema API JSON → OpenSearch mappings)
- [ ] Query conversion (Solr query syntax → Query DSL)
- [ ] Incompatibility detection and tracking (breaking/behavioral/unsupported categories)
- [ ] Stakeholder-aware guidance (tailor output to user role)

## C. Packaging

- [ ] **[P0] OpenSearch Migration Assistant integration** — deploy as component, expose queryable endpoint
- [ ] **[P0] MCP server** — expose core as MCP server for any MCP-compatible tool/IDE
- [ ] **[P1] Kiro power** — package MCP server as Kiro power for in-IDE use
- [ ] **[P2] Standalone web app** — minimal chat interface

## D. Workflow Contract

- [ ] **[P0] Explicit phase model** — intake, assessment, design, planning, validation/approval, deployment handoff
- [ ] **[P0] Phase exit criteria** — each phase names what must be true before moving on
- [ ] **[P0] Durable artifact chain** — intake notes, readiness findings, conversion findings, playbook, approval record, cutover checklist
- [ ] **[P1] Manual fallback paths** — documented behavior when MCP, live LLM scoring, or AWS access is unavailable
- [ ] **[P1] Deployment-readiness gap output** — if execution details are missing, produce required inputs/gaps rather than pretending the plan is executable

## E. Testing and Evaluation Process

- [ ] **[P0] Evidence-backed evaluation path** — judged outputs increasingly tied to generated artifacts and scenario evidence
- [ ] **[P1] Clear distinction between deterministic CI fixtures and live judged runs**
- [ ] **[P1] Second-judge / alternate-model comparison path** — reduce single-judge overconfidence
- [ ] **[P1] Baseline refresh ownership/rules** — who promotes a baseline, when, and with what review note
- [ ] **[P1] Troubleshooting guidance for runtime modes** — MCP path, dependency path, packaging path

## F. Align with Upstream Patterns

- [ ] Adopt safety tier model (Observe/Propose/Execute) from upstream `kiro-cli/`
- [ ] Add audit logging (upstream hooks log every prompt, tool use, result)
- [ ] Match steering doc convention (`*.md` loaded by agent at runtime)
- [ ] Consider producing Argo-compatible workflow configs (`.wf.yaml`) from migration reports
- [ ] Register advisor in `migration_services.yaml` service discovery contract
- [ ] Expose via Migration Console REST API (`api/` module pattern)

## G. Coordinate with Upstream Solr Work

- [ ] Track upstream Solr PRs (#2457 cluster detection, #2478 query translation, #2458 schema conversion)
- [ ] Ensure our advisory output doesn't contradict upstream execution tooling
- [ ] Position OSC as "advise & plan" vs upstream "detect & execute"
- [ ] Coordinate with key contributors: AndreKurait, sumobrian, nagarajg17

## H. Contribution Pathway

- [ ] Align with Apache-2.0 licensing (already done)
- [ ] Match upstream Python conventions (pipenv, pytest)
- [ ] Add pre-commit hooks per `install_githooks.sh` pattern
- [ ] Prepare PR for `AIAdvisor/` directory in `opensearch-project/opensearch-migrations`
- [ ] Document release/versioning expectations for shared repo snapshots and artifacts
- [ ] Document supported operating modes and prerequisites in contributor-facing docs

## I. Gap Summary

| Deliverable | Status | Primary Gap |
|---|---|---|
| Knowledge base — incompatibility catalog | ~80% | Needs programmatic structure for agent consumption |
| Knowledge base — query translation | ~80% | Request-level placeholders now cover eDisMax/fq/facets; function queries, spatial, MLT, spellcheck still missing |
| Knowledge base — index design | ~80% | Analyzer chain edge cases |
| Knowledge base — sizing heuristics | ~50% | Computable heuristics, not just prose |
| Knowledge base — question sets | ~90% | Integration into agent workflow |
| Knowledge base — bundled data files | Done | Architecture is correct |
| Agent — transport-agnostic core | ~30% | Architecture correct, but handle_message() is a keyword router — Steps 0,2,4,5,6 unimplemented |
| Agent — pluggable storage | ~70% | FileStorage + InMemoryStorage exist; need S3 backend |
| Agent — persistent memory | ~40% | Cross-session knowledge not yet implemented |
| Agent — migration report | ~50% | Verify all 5 sections; cost estimation likely missing |
| Agent — schema conversion | ~70% | Edge cases (analyzer chains, dynamic fields) |
| Agent — query conversion | ~55% | Request-level `convert_request()` now covers eDisMax/fq/facets; still missing function queries, spatial, MLT, spellcheck, richer production semantics |
| Upstream alignment | ~10% | No audit hooks, no safety tiers, no workflow config output |
| Upstream Solr coordination | ~20% | Need to track 6 active PRs adding overlapping Solr capabilities |
| Packaging — Migration Assistant | ~10% | No HTTP adapter, Dockerfile, or CDK construct |
| Packaging — MCP server | ~80% | End-to-end verification needed |
| Packaging — Kiro power | ~60% | Config exists, needs MCP server as backend |
| Packaging — web app | 0% | Nothing built (P2) |
| Upstream contribution | 0% | PR process, directory structure, CI alignment |
