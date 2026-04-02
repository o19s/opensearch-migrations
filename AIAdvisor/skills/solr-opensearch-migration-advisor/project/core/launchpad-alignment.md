# Launchpad Alignment Notes

This note captures the most useful structure/process guidance from the OpenSearch Launchpad
project docs and makes explicit how this repo should adopt or adapt it.

Primary upstream references reviewed on 2026-03-23:

- `opensearch-project/opensearch-launchpad` `README.md`
- `opensearch-project/opensearch-launchpad` `DEVELOPER_GUIDE.md`

## Why this matters

The Launchpad docs are valuable less because they describe "more features" and more because
they make a few operating assumptions explicit:

- supported operating modes are named and documented
- prerequisites are stated up front
- the workflow is phase-based and each phase has a clear purpose
- there are explicit manual fallback paths when full MCP or client-side sampling is unavailable
- tests are categorized around architecture seams
- release/version discipline is documented as a normal part of contribution, not tribal knowledge

Our repo already covers much of the migration content itself, but those process assumptions
have been more implicit than explicit.

## Guidance worth carrying forward

### 1. Document operating modes, not just content structure

Launchpad is explicit about the difference between:

- direct skill use
- MCP-server use
- IDE-specific packaging/integration

For this repo, the equivalent supported modes should be described as:

- skill/reference mode: agent reads `skills/solr-to-opensearch-migration/`
- Python core mode: deterministic `handle_message()` and converters
- MCP mode: `scripts/mcp_server.py` tool surface for agent clients
- worked-engagement mode: consultants use `playbook/` plus `examples/`

This reduces confusion about whether the repo is "just docs", "just a skill", or a runtime.

### 2. Make phase contracts explicit

Launchpad's README makes its workflow legible through named phases. We should do the same for
the migration-advisor process:

1. Intake and artifact collection
2. Source-system assessment
3. Target design and query/schema translation
4. Migration playbook and implementation planning
5. Validation, cutover, and approval review
6. Deployment-readiness and handoff

Those phases already exist across the playbook and skill references, but the contract between
them has been under-documented.

### 3. Define phase artifacts and exit criteria

The most important Launchpad lesson for this repo is not "more automation". It is that each
phase should produce durable artifacts that the next phase consumes.

Minimum artifact chain we should treat as first-class:

- intake notes and artifact-request checklist
- risk/readiness assessment
- translated schema/query findings with incompatibilities
- target design and migration playbook
- consumer inventory and success definition
- go/no-go / approval record
- cutover checklist and validation evidence

### 4. Document manual fallback paths

Launchpad explicitly handles cases where client sampling or MCP capabilities are unavailable.
We should mirror that mindset:

- if MCP is unavailable, the skill/reference path remains usable
- if an LLM is unavailable, deterministic converters and report generation still provide the floor
- if live judge scoring is unavailable, emit eval tasks/results for later review instead of blocking
- if AWS deployment details are unavailable, require a deployment-readiness gap list instead of
  pretending the plan is execution-ready

### 5. Treat evaluation as evidence-backed, not prose-only

Launchpad's Phase 4.5 evaluation flow is grounded in executed queries and concrete evidence.
Our advanced-testing work should keep moving in that direction:

- scenario evals should increasingly connect judged outputs to real generated reports/artifacts
- regression policy should distinguish deterministic fixture checks from live judged runs
- manual review should remain explicit for baseline promotion and unstable judge behavior

### 6. Separate contribution guidance from project guidance

Launchpad cleanly separates:

- repo/project overview
- developer/contributor workflow
- runtime/MCP usage

We should keep doing the same and avoid stuffing contributor expectations into `README.md`.

### 7. Document release and packaging expectations

Launchpad's developer guide includes release steps, packaging behavior, and CI expectations.
For this repo, the equivalent missing process items are:

- how version changes should be recorded
- what needs verification before tagging or sharing artifacts broadly
- what packaging/integration targets are actually supported today vs aspirational

## Decisions adopted in this repo

The repo should now explicitly assume:

- multiple operating modes are supported and documented
- the migration-advisor workflow is phase-based
- each phase should name its required inputs, durable outputs, and exit criteria
- manual fallback paths are part of the design, not exceptions
- tests should keep clustering around architecture seams: core logic, MCP surface, artifact integrity,
  bridge behavior, and eval/regression workflows
- release/check-in discipline belongs in contributor docs

## Follow-on gaps still open

These items are still not fully solved just by documenting them:

- a single shared tracker for phase-level work and decisions
- a formal release checklist and versioning policy for repo snapshots
- deeper deployment-readiness artifacts for AWS-specific handoff
- clearer packaging guidance for non-Kiro/non-Claude consumers
- live multi-judge evaluation policy beyond the current basic scaffolding

## Practical takeaway

The upstream Launchpad docs push us toward a better shape:

- fewer implicit assumptions
- clearer supported modes
- stronger phase-to-artifact contracts
- better fallback behavior
- more explicit contribution and release discipline

That is the part worth importing into this repo.
