# Agent99 and opensearch-migrations

## Status

Proposed working position as of 2026-03-21.

## Decision

Treat `Agent99` and `opensearch-project/opensearch-migrations` as complementary but distinct layers.

- `Agent99` is the AI guidance, governance, and review-artifact layer.
- `opensearch-migrations` is the migration execution and orchestration layer.

Do not describe `Agent99` as a direct implementation of the current `opensearch-migrations` runtime framework. Describe it as a companion-oriented control layer that can feed, guide, or wrap that framework.

## Context

The current upstream `opensearch-migrations` repository is centered on executable migration tooling:

- migration console
- workflow CLI
- declarative workflow specs
- metadata migration
- snapshot-based backfill
- traffic capture and replay
- transformation logic
- deployment paths for local and AWS environments

The current `Agent99` repository is centered on advisory and governance assets:

- installable AI skills
- migration reference content
- intake and assessment methodology
- success-definition, consumer-inventory, and go/no-go templates
- worked artifact chains for approval and cutover control
- eval and integrity tests for docs and artifacts

This distinction is explicit in the companion demo: `Agent99` demonstrates reviewable artifacts and approval flow without claiming to be the runtime execution system.

## Why This Position Fits Best

### What maps cleanly

There is strong conceptual alignment between the two repositories:

- both care about staged migration rather than naive lift-and-shift
- both care about validation, approval gates, and rollback posture
- both assume migration work should be bounded by explicit artifacts
- both are moving toward a model where AI helps drive the operator experience

This is especially true for the direction described in upstream issue `#2444`, where the AI is the interface and the playbook is the governing artifact.

### What does not map cleanly

`Agent99` does not currently implement:

- executable workflow YAML generation for upstream runtime submission
- EKS/Argo deployment automation
- live migration control surfaces
- runtime telemetry querying against active migration infrastructure
- persistent operator state across sessions in the way a packaged companion runtime would

Conversely, upstream `opensearch-migrations` does not currently look like a mature expert-guidance knowledge base with reusable approval-grade artifacts and agent-skill packaging as its primary output.

## Recommended Product Framing

Use this framing in docs and conversations:

`Agent99` is the companion brain and review surface. `opensearch-migrations` is the execution engine.

More explicitly:

- before approval, `Agent99` leads with assessment, design reasoning, and artifact generation
- at approval gates, `Agent99` provides the evidence package and decision framing
- after approval, `opensearch-migrations` executes the approved migration mechanics
- during execution, `Agent99` can eventually interpret telemetry and update decision artifacts, but should not be confused with the runtime itself

## Integration Seams

The likely seams between the two layers are below.

### 1. Assessment to workflow input

`Agent99` should produce structured outputs that can inform upstream workflow configs:

- source/target inventory
- migration scope
- risk posture
- stage boundaries
- validation thresholds
- approval requirements

Near-term reality:

- today these are mostly prose-first markdown artifacts
- later they could be exported to machine-readable config fragments

### 2. Playbook narrative to executable workflow

`Agent99` playbooks are currently review artifacts.

Upstream playbooks are executable workflow definitions.

The long-term seam is a translation layer from:

- reviewable migration plan

to:

- executable workflow config bounded by the same scope, approvals, and stop conditions

### 3. Approval objects to runtime gates

`Agent99` already defines approval-ready artifacts:

- success definition
- risk register
- go/no-go review
- approval record
- cutover checklist

The integration target is to bind those artifacts to upstream runtime gates so that:

- a reviewer approves a specific artifact version
- the executed workflow references that approval scope
- execution outside that scope is blocked or escalated

### 4. Validation evidence to operational status

`Agent99` currently describes validation in human-readable terms:

- judged relevance
- functional smoke checks
- operational thresholds
- cutover readiness

The natural integration path is to let upstream execution emit the operational facts and let `Agent99` summarize them into updated decision artifacts.

### 5. Telemetry interpretation

The upstream direction is AI-mediated observability.

`Agent99` should fit here as the interpretation layer:

- explain replay lag, bulk failures, cluster health, and result regressions
- connect signals back to approval thresholds and rollback triggers
- update go/no-go posture in plain language

That is a better fit than moving `Agent99` down into the mechanics of log collection or workflow scheduling.

## Practical Implications

### What to keep doing in Agent99

- deepen migration guidance and decision heuristics
- improve approval-grade artifact templates
- strengthen evidence expectations around validation and cutover
- keep companion demos realistic and reviewable
- add eval coverage for advice quality and artifact-chain coherence

### What not to over-claim

- that this repo is already the migration runtime
- that markdown playbooks are equivalent to upstream executable workflows
- that local demos are the same thing as upstream deployment and execution paths

### What to prepare for next

- define a minimal machine-readable schema for stage plans and approvals
- map `Agent99` playbook sections to upstream workflow fields
- define traceability from artifact version to execution run
- define how runtime telemetry updates companion artifacts after stage completion

## Short Version

`Agent99` is not the current `opensearch-migrations` framework itself.

`Agent99` is a companion-oriented guidance and governance layer that fits best above, beside, and eventually into the future companion experience envisioned for `opensearch-migrations`, especially the issue `#2444` direction.
