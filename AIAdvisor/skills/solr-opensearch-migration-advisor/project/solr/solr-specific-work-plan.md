# Solr-Specific Work Plan

Date: 2026-03-23

This note is a practical starting plan for covering the "Solr-specific material" lane in the
OSC/Amazon query-translation conversation.

It is intentionally narrow: the goal is not to become the owner of the entire upstream transform
stack. The goal is to represent the parts of Solr behavior that are most likely to cause migration
drift, false confidence, or advisor/runtime inconsistency.

Important boundary:

- do not conflate generic migration transforms with Solr query-semantic coverage
- the active Solr query path currently appears to live primarily under
  `TrafficCapture/SolrTransformations/...`
- the separate `transformation/standardJavascriptTransforms/src` area looks more like generic
  metadata/settings/index-shape transform infrastructure

## Primary Goal

Advise on whether upstream query-translation work is prioritizing the Solr features that matter
most in real migrations, with particular attention to:

- semantic fidelity
- ranking drift risk
- filter behavior
- integrated request behavior
- clear unsupported/partial-support signaling

## Start Here

Read these first, in this order:

1. [upstream-query-translation-assessment.md](/opt/work/OSC/agent99/project/upstream/upstream-query-translation-assessment.md)
2. [upstream-query-translation-overview.md](/opt/work/OSC/agent99/project/upstream/upstream-query-translation-overview.md)
3. upstream `#2458`
4. upstream `#2434`, `#2461`, and `#2478`
5. [query_converter.py](/opt/work/OSC/agent99/scripts/query_converter.py)
6. [test_query_converter.py](/opt/work/OSC/agent99/tests/unit/test_query_converter.py)
7. [test_bridge_golden_scenarios.py](/opt/work/OSC/agent99/tests/integration/test_bridge_golden_scenarios.py)

Why this order:

- the first two docs frame the upstream priority question
- the upstream parser/transform/orchestrator path is the real Amazon-facing target
- `#2458` is the most important currently open semantics PR
- the local converter/tests make the semantic tradeoffs concrete after the upstream contract is clear
- the bridge tests show which scenario behaviors we already consider important enough to encode

## Suggested Reading Order For Upstream PRs

Read the upstream PRs in dependency order, not in Slack order:

1. `#2287` E2E framework
2. `#2399` query-engine skeleton
3. `#2434` PEG parser
4. `#2461` transformer stage
5. `#2478` orchestrator
6. `#2458` standard query parser translation
7. `#2435` sort
8. `#2379` JSON term facets
9. `#2396` range facets
10. `#2383` highlighting
11. `#2417` cursor pagination

Why this order:

- it separates architecture from feature coverage
- it makes it easier to judge whether a feature PR is adding meaningful semantics or only surface shape
- it helps you see where the warning/fallback contract is actually implemented

## Top Solr-Specific Questions To Drive

These are the main questions to keep asking while reading PRs and replying to Amazon.

### 1. What real Solr behavior is preserved?

Do not stop at "there is a translation."

Ask:

- does this preserve filtering semantics or only request shape?
- does this preserve ranking behavior or only produce syntactically valid DSL?
- does this preserve integrated request meaning when combined with other params?

### 2. What is silently wrong vs explicitly warned?

This matters as much as raw feature support.

Ask:

- when parsing fails, what warning is returned?
- when transformation is partial, what contract does the caller get?
- does the advisor describe the same limitation the engine exposes?

### 3. Is the work prioritizing common migration blockers?

The highest-value Solr topics are usually:

- `q`
- `fq`
- `edismax`
- boosts
- facet behavior under filters
- highlighting behavior under analyzer/mapping differences

Lower-frequency features still matter, but not equally.

Also ask:

- is this actually query-semantic work, or is it generic transform plumbing being counted as progress?

### 4. Is this tested as a real request?

A parameter-by-parameter PR can still miss production behavior.

Ask:

- where is the combined request test?
- what happens when `q`, `fq`, `sort`, `fl`, and facets appear together?
- what happens when highlighting is layered on top of translated query behavior?

## Best First Deep-Dive Topics

If time is limited, start here.

### Topic 1: `fq`

Reason:

- one of the most central Solr request surfaces
- easier to reason about and pressure-test quickly than full `edismax`
- often combined with facets, sorting, and pagination
- a good first place to push on non-scoring semantics and integrated request behavior

Focus questions:

- when does upstream produce non-scoring filter clauses?
- how are multiple `fq` params composed?
- what are the known semantic differences, if any?

### Topic 2: `edismax`

Reason:

- probably the highest strategic real-world Solr migration gap in the listed roadmap
- central to relevance tuning in many production Solr apps
- easy for a migration effort to under-prioritize if it focuses on simpler parser/param wins

Focus questions:

- where are `qf`, `pf`, boosts, and `mm` expected to land?
- what support is planned vs explicitly out of scope?
- how will upstream distinguish placeholder translation from production-grade parity?

### Topic 3: Integrated request behavior

Reason:

- most production regressions show up in combined requests, not isolated params

Focus examples:

- `q + fq + sort + fl + rows/start`
- `edismax + qf + pf + mm`
- `q + fq + facets`
- `q + highlighting`

## Personal Deliverables For This Lane

You do not need to solve the whole upstream roadmap. The most useful artifacts you can produce are:

### 1. Solr coverage matrix

Keep a simple table with columns like:

- feature
- common in real Solr apps?
- migration-risk if wrong?
- upstream status
- OSC concern

Seed rows:

- standard parser `q`
- `fq`
- `edismax`
- boosts
- sort
- term facets
- range facets
- highlighting
- cursorMark
- function queries
- joins / graph queries
- MLT / spellcheck

### 2. Priority note back to Amazon

Your main value is not "more detail". It is useful prioritization pressure:

- what is high-frequency + high-risk?
- what is helpful but secondary?
- where should upstream be careful not to overclaim?

### 3. Test-shape suggestions

The best Solr-specific pushback is often:

- "show me the combined request case"
- "show me the warning/fallback behavior"
- "show me where ranking/filter semantics are being checked"

## Recommended Stance With Amazon

The tone should be:

- supportive about the architecture direction
- sharp about semantic-risk priorities
- explicit that partial support is acceptable if it is labeled honestly

Useful framing:

- foundation looks good
- query/filter fidelity should stay ahead of surface breadth
- `edismax` and `fq` deserve explicit high priority
- combined-request validation matters more than isolated param wins
- advisor messaging must match runtime reality

## If You Only Have One Working Session

Do this:

1. Read the "What Looks Under-Prioritized" section in [upstream-query-translation-assessment.md](/opt/work/OSC/agent99/project/upstream/upstream-query-translation-assessment.md)
2. Review upstream `#2458`, then `#2434`, `#2461`, and `#2478`
3. Scan for any explicit `fq` / `edismax` roadmap references
4. Write a one-page matrix for:
   - `q`
   - `fq`
   - `edismax`
   - facets
   - highlighting
5. Send back the priority message:
   - good foundation
   - do not confuse parser progress with Solr parity
   - prioritize `fq` and `edismax`
   - validate integrated requests

## Practical Bottom Line

The Solr-specific lane is really about protecting against false confidence.

The most useful thing you can do is keep the conversation anchored on:

- real Solr behavior
- integrated request semantics
- ranking/filter fidelity
- explicit caveats where support is partial

That is the highest-value OSC contribution in this slice.


## Appendix:
### ref links:  
*#2478* — *feat(solr-transforms): Implement orchestrator for query translation engine*
https://github.com/opensearch-project/opensearch-migrations/pull/2478

*#2458* — *Adding request translator for standard query parser*
https://github.com/opensearch-project/opensearch-migrations/pull/2458

*#2435* — *Adding request translator for sort parameter*
https://github.com/opensearch-project/opensearch-migrations/pull/2435

*#2417* — *feat(solr-transforms): Add cursor pagination (cursorMark → search_after)*
https://github.com/opensearch-project/opensearch-migrations/pull/2417

*#2383* — *Add Solr highlighting component translation transforms*
https://github.com/opensearch-project/opensearch-migrations/pull/2383

*CLOSED / MERGED IN THE LAST MONTH*

*#2461* — *feat(solr-transforms): Add transformer stage of the query translation engine* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2461

*#2434* — *feat(solr-transforms): Add PEG-based Solr query parser* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2434

*#2411* — *Adding request translator for field list parameter* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2411

*#2399* — *feat(solr-transforms): Add query engine skeleton with interfaces* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2399

*#2396* — *Added Translation for Range Facets* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2396

*#2395* — *Add rows and start query parameter translation to Solr select transform* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2395

*#2379* — *Added request translator for JSON based term facet* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2379

*#2287* — *Add Solr E2E testing framework: transformation shim, multi-target validation, and transform pipeline* — *merged*
https://github.com/opensearch-project/opensearch-migrations/pull/2287
