# Five Demo Stories for Solr Migration

Date: 2026-03-23

This note defines five demo/user-story tracks for the Solr-specific lane.

The goal is not just to have five demos.
The goal is to have five demos that also act as a rough Solr functionality-coverage ladder.

They should help answer:

- what can we demo today?
- what parts of Solr migration do these demos cover?
- where are we strong vs still thin?

## Recommended Demo Ladder

The recommended order is:

1. Hello Migration
2. Drupal Site Migration
3. Mid-Market Enterprise Search
4. Legacy Global Search Platform
5. Stump-the-Chump

This order matters.

It teaches the audience how to interpret the tool:

- first as a helpful migration guide
- then as a practical advisor
- then as a deeper search-migration assistant
- then as a system that knows where the hard problems are
- finally as a system that can fail honestly instead of pretending everything is solved

---

## Story 1: Hello Migration

### Summary

A technical OpenSearch-savvy user with weak Solr background wants a quick first look at the migration
tool. They try one fast YOLO/Express interaction, then spend 10-15 minutes with the advisor to see
what kinds of questions and outputs the tool produces.

### Persona

- strong OpenSearch / AWS knowledge
- limited Solr experience
- technical enough to judge output quality quickly
- not ready to answer most migration-intake questions yet

### Demo goal

Show that the tool is useful even when the user can only answer a small fraction of the intake.

### Best source material

- [techproducts-demo](/opt/work/OSC/agent99/examples/techproducts-demo/README.md)
- [golden-scenario-techproducts.md](/opt/work/OSC/agent99/tests/evals/golden-scenario-techproducts.md)
- [demo_query_translation.py](/opt/work/OSC/agent99/scripts/demo_query_translation.py)

### Solr coverage

- basic schema translation
- analyzer chains
- copyField
- dynamic fields
- `fq`
- `edismax`
- facet.field
- basic integrated requests

### Suggested flow

1. Run a short YOLO/Express interaction.
2. Ask for a quick schema/query sketch.
3. Show a deterministic query translation example.
4. Show the advisor asking better migration questions than the user would have known to ask.

### Current readiness

`80-90%`

### Why it is strong now

- strongest current deterministic query-demo path
- strongest current “hello migration tool” story
- low complexity keeps the caveat burden manageable

### Main limitations

- not much operational depth
- does not prove advanced Solr parity

---

## Story 2: Drupal Site Migration

### Summary

A large Drupal site with moderate traffic wants to migrate off Solr. They do not currently have major
failover or scaling problems, but they want lower operational burden and a clearer future path.

### Persona

- web platform owner / lead developer
- some search familiarity, but not a search-infrastructure specialist
- wants practical answers about modules, field mapping, content behavior, and migration effort

### Demo goal

Show that the tool understands when the right answer is not raw Solr query translation alone.

### Best source material

- [drupal-solr-opensearch-demo](/opt/work/OSC/agent99/examples/drupal-solr-opensearch-demo/README.md)
- [golden-scenario-drupal.md](/opt/work/OSC/agent99/tests/evals/golden-scenario-drupal.md)

### Solr coverage

- Search API Solr integration patterns
- machine-generated field naming
- multilingual/content-model concerns
- client/framework migration
- advisory overconfidence avoidance

### Suggested flow

1. Start with intake and role identification.
2. Show the tool recognizing Drupal-specific migration concerns.
3. Emphasize module swap / integration-path guidance.
4. Show where raw schema/query conversion is secondary to architecture and platform fit.

### Current readiness

`75-85%`

### Why it is strong now

- very good worked artifact set already exists
- good example of the tool being useful without pretending full raw Solr parity

### Main limitations

- query-converter demo is less central here
- more advisory than “look at this exact translated request”

---

## Story 3: Mid-Market Enterprise Search

### Summary

A custom enterprise Solr deployment runs on 3 Solr nodes with 3 ZooKeeper nodes and supports three
languages: English, Spanish, and French. The application uses facets, boosting, `bq`, and some
MLT/spellcheck behavior.

### Persona

- search lead or senior engineer
- comfortable with Solr relevance knobs
- expects nuance around ranking, language analysis, and migration risk

### Demo goal

Show the transition from “basic migration helper” to “real search-migration advisor.”

### Proposed Solr coverage

- `edismax`
- `qf`
- boosts / `bq`
- facets
- i18n / multilingual design
- MLT
- spellcheck
- 3-node SolrCloud posture

### Suggested flow

1. Start with the top query patterns and language setup.
2. Show what the deterministic path can translate today.
3. Show what the advisor can reason about beyond current script coverage.
4. Highlight which features are partial, unsupported, or redesign-oriented.

### Current readiness

`50-65%`

### Why it is useful now

- exposes the current boundary honestly
- still demoable if presented as advisor + caveats, not automatic translation completion

### Main limitations

- deterministic support is still thin for `bq`, MLT, and spellcheck
- multilingual analyzers are more advisory than automated

---

## Story 4: Legacy Global Search Platform

### Summary

A large enterprise runs Solr across three data centers with large hardware footprints and years of
legacy relevance tuning. They rely on cache warming, complex synonyms, phrase synonyms, function
queries, JSON facets, and join/graph behavior.

### Persona

- architect or principal search engineer
- deeply aware of operational and semantic complexity
- wants risk clarity more than sales-demo smoothness

### Demo goal

Show that the tool can think like a migration architect even when full deterministic translation is
not realistic.

### Proposed Solr coverage

- multi-DC operational topology
- cache warming
- heavy synonym management
- phrase synonyms
- function queries
- JSON facets
- join / graph queries
- cutover / rollback / failover planning

### Suggested flow

1. Start with architecture and risk intake, not query translation.
2. Show the tool identifying high-risk areas early.
3. Use one or two request examples to show partial support boundaries.
4. End on migration strategy, not on a promise of full automated conversion.

### Current readiness

`35-50%`

### Why it is still worth demoing

- strong trust-building case if handled honestly
- demonstrates architectural value even where deterministic coverage is weak

### Main limitations

- weak deterministic translation for advanced query semantics
- more of a planning/risk demo than a translator demo

---

## Story 5: Stump-the-Chump

### Summary

A deliberately ugly migration scenario designed to push the system into ambiguity, unsupported
feature detection, and escalation behavior. This is not intended to be fully realistic. It is
intended to test honesty, structure, and triage quality.

### Persona

- skeptical technical reviewer
- wants to know whether the tool can avoid bluffing

### Demo goal

Show 60-80% success through structured triage, not fake completeness.

### Proposed Solr coverage

- custom plugins
- custom request handlers
- undocumented analyzer behavior
- legacy synonym files
- function queries
- joins / graph queries
- grouping
- MLT / spellcheck
- custom update processors
- ugly operational dependencies

### Suggested flow

1. Throw a lot of ugly facts at the tool quickly.
2. Watch whether it categorizes and prioritizes correctly.
3. Reward explicit caveats, escalations, and redesign recommendations.
4. Do not score it by “did it translate everything.”

### Current readiness

`40-60%` if judged on triage and risk surfacing

### Why it matters

- this is the best honesty test
- it helps prove the tool is not just a polished happy-path demo

### Main limitations

- deterministic translation is not the point here
- needs strong facilitation so the audience understands the scoring criteria

---

## Solr Coverage Matrix

| Capability / concern | Story 1 | Story 2 | Story 3 | Story 4 | Story 5 |
|---|---|---|---|---|---|
| Basic schema mapping | High | Medium | Medium | Medium | Medium |
| Analyzer chains | High | Medium | High | High | High |
| copyField / aggregate fields | High | Medium | Medium | High | High |
| `fq` | High | Low | High | Medium | High |
| `edismax` | High | Low | High | Medium | High |
| Facets / aggs | High | Low | High | High | High |
| Highlighting | Medium | Low | Medium | High | High |
| Integrated request composition | High | Low | High | High | High |
| Drupal / framework migration | Low | High | Low | Low | Medium |
| Multilingual/i18n | Low | Medium | High | High | High |
| MLT / spellcheck | Low | Low | Medium | Medium | High |
| Function queries | Low | Low | Low | High | High |
| Join / graph queries | Low | Low | Low | High | High |
| Operational topology / cutover | Low | Medium | Medium | High | High |
| Honest unsupported detection | Medium | High | High | High | Very High |

---

## Rough Readiness By Story

| Story | Readiness | Best current use |
|---|---|---|
| Hello Migration | `80-90%` | primary intro demo |
| Drupal Site Migration | `75-85%` | practical advisory demo |
| Mid-Market Enterprise Search | `50-65%` | partial-coverage + caveats demo |
| Legacy Global Search Platform | `35-50%` | architectural risk / planning demo |
| Stump-the-Chump | `40-60%` | trust / honesty / triage demo |

---

## Overall Readiness

### Advisory / guided migration value

`Strong`

The repo is in good shape for:

- intake and discovery
- migration questioning
- schema/query planning
- artifact generation
- risk surfacing
- honest caveats

### Deterministic translation value

`Moderate and improving`

The repo is in good shape for demo-level request translation of:

- `fq`
- `edismax` with `qf`
- `facet.field`
- basic highlighting request structure
- basic integrated request composition

It is not yet strong for:

- `mm`, `pf`, `bq`, `bf`
- function queries
- MLT
- spellcheck
- joins / graph
- advanced highlighting parity
- full schema-aware exact/filter behavior

### Best honest one-line summary

We are ready to demo introductory and moderate migrations convincingly, and ready to demo advanced
migrations as guided assessment and risk surfacing, not as full automatic translation.

---

## Practical Recommendation

If you only have time to show three stories, use:

1. Hello Migration
2. Drupal Site Migration
3. Mid-Market Enterprise Search

If you want the strongest trust-building finale, end with:

- Stump-the-Chump

That is the clearest way to show that the tool can handle hard scenarios without bluffing.
