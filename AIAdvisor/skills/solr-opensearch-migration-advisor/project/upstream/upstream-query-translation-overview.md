# Upstream Query Translation Overview

Date: 2026-03-23

This note summarizes the recent `opensearch-project/opensearch-migrations` Solr query-translation
PRs from an OSC point of view.

Source thread context:

- Amazon asked OSC whether the team is prioritizing the right Solr query translations
- the same upstream translation source will also sit in the AI Advisor container/workspace
- therefore OSC cares about both priority and consistency

Important current-state correction:

- PR [#2478](https://github.com/opensearch-project/opensearch-migrations/pull/2478) was listed as open in Slack, but it merged on 2026-03-23

## Executive Read

The upstream team has made strong progress on the **translation engine foundation** and on a
useful first set of **request-parameter translations**:

- engine skeleton
- PEG parser
- transformer stage
- query orchestrator
- `fl`
- `rows/start`
- JSON term facets
- range facets
- sort
- highlighting
- cursor pagination
- E2E transform/validation harness

From OSC's perspective, that is a good foundation, but it is not yet the same thing as
"high-confidence migration coverage for real Solr workloads."

The main reason is that the biggest migration-risk surface is usually not field list or
pagination. It is **query semantics and ranking behavior**, especially:

- standard query parsing details
- boosting behavior
- `fq` behavior and filter composition
- `edismax` and related request semantics
- facet behavior in the presence of real query/filter combinations

## What OSC Cares About

OSC's priorities are:

1. **Behavior fidelity before surface breadth**
   A smaller number of high-fidelity translations is more valuable than many parameters that
   "translate" but drift meaningfully in ranking or filtering behavior.

2. **Real query combinations, not isolated params**
   Production Solr requests combine `q`, `fq`, `sort`, `fl`, `rows/start`, facets, and often
   highlighting. OSC cares about the integrated request, not just one parameter at a time.

3. **Warnings and unsupported-feature signaling**
   The translation engine should be explicit when it falls back, passes through, or only
   partially translates. Silent drift is worse than an explicit warning.

4. **Consistency with the AI Advisor**
   The advisor should describe the same boundaries and caveats the transform engine actually has.
   If upstream says a feature is partial, OSC should not describe it as production-ready.

5. **Priority on common migration blockers**
   In practice, `edismax`, `fq`, boosting, analysis/highlighting interactions, and facet/filter
   behavior matter more than some lower-frequency parameters.

## PR Summary

| PR | Current state on 2026-03-23 | What it adds | OSC view |
|---|---|---|---|
| [#2478](https://github.com/opensearch-project/opensearch-migrations/pull/2478) | merged | parser -> transformer orchestrator with warnings/fallback | important foundation; good consistency point for advisor messaging |
| [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458) | open | standard query parser translation: terms, ranges, phrases, booleans, boosts | highest-value open item because it starts touching real query semantics |
| [#2435](https://github.com/opensearch-project/opensearch-migrations/pull/2435) | open | `sort` translation | important and common, but usually lower risk than core query semantics |
| [#2417](https://github.com/opensearch-project/opensearch-migrations/pull/2417) | open draft | `cursorMark` -> `search_after` | useful, but more specialized; dual-target incompatibility needs clear warning posture |
| [#2383](https://github.com/opensearch-project/opensearch-migrations/pull/2383) | open | highlighting request/response transforms | useful and visible to users; correctness depends on mapping/analysis behavior too |
| [#2461](https://github.com/opensearch-project/opensearch-migrations/pull/2461) | merged | transformer stage | foundation, not direct feature coverage |
| [#2434](https://github.com/opensearch-project/opensearch-migrations/pull/2434) | merged | PEG-based Solr parser | important foundation, especially for consistent warning behavior |
| [#2411](https://github.com/opensearch-project/opensearch-migrations/pull/2411) | merged | `fl` translation | useful but not top migration risk |
| [#2399](https://github.com/opensearch-project/opensearch-migrations/pull/2399) | merged | query-engine skeleton/interfaces | foundation |
| [#2396](https://github.com/opensearch-project/opensearch-migrations/pull/2396) | merged | range facets | good coverage expansion; date/time gap still matters |
| [#2379](https://github.com/opensearch-project/opensearch-migrations/pull/2379) | merged | JSON term facet translation | solid, common feature area |
| [#2287](https://github.com/opensearch-project/opensearch-migrations/pull/2287) | merged | E2E shim, multi-target validation, transform pipeline | strategically important because it enables evidence-based validation |

## OSC Best-Guess Priority View

If OSC had to rank the next query-translation focus areas based on migration value:

1. `q` semantics and boosting: [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458)
2. `fq` composition and filter semantics: not explicit in the Slack list, but should be near the top
3. `edismax` semantics: also not explicit in this list, but likely one of the highest real-world priorities
4. `sort`: [#2435](https://github.com/opensearch-project/opensearch-migrations/pull/2435)
5. facets under realistic query/filter combinations: [#2379](https://github.com/opensearch-project/opensearch-migrations/pull/2379), [#2396](https://github.com/opensearch-project/opensearch-migrations/pull/2396)
6. highlighting: [#2383](https://github.com/opensearch-project/opensearch-migrations/pull/2383)
7. cursor pagination: [#2417](https://github.com/opensearch-project/opensearch-migrations/pull/2417)

## Short OSC Response Back To Amazon

The current direction looks broadly right, especially the parser/transform/orchestrator
foundation plus the E2E validation harness. From OSC's point of view, the highest-value
translation priorities are the ones that preserve actual query semantics and ranking behavior:
standard query parsing, boosting, `fq`, and especially `edismax`-style request behavior.

`sort`, facets, highlighting, and cursor pagination all matter, but they are secondary to
core query/filter fidelity. OSC would also strongly prefer explicit warnings/fallbacks over
silent partial translation, and we should keep the AI Advisor's messaging aligned with the
actual transform-engine boundaries so the two stay complementary and consistent.
