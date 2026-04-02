# Drupal Pre-Migration Assessment Starter

**Client shape assumed:** Drupal site or estate backed by a roughly 1 TB Solr deployment, likely SolrCloud rather than a single-core Solr server  
**Assessment status:** Starter / pre-discovery draft  
**Prepared:** 2026-03-19

---

## Executive Framing

This is the right kind of migration to assess carefully before discussing implementation.

A `~1 TB` Drupal Solr estate is large enough that:

- this is probably not a "module swap and reindex over lunch" project
- SolrCloud topology, shard layout, and indexing throughput matter
- content lifecycle and Drupal Search API ownership must be clarified early
- access control, multilingual analysis, autocomplete, and Views/Facets behavior may become redesign items

The working assumption should be:

1. the current search platform is **probably SolrCloud**
2. the preferred target posture is **OpenSearch reached through Drupal**, not raw Lucene-level migration
3. the migration should be treated as a **phased program** with assessment, proof-of-concept, validation, and cutover

---

## Initial Hypotheses To Validate

These are assumptions worth testing in the first client sessions.

| Hypothesis | Why it matters | What would change if false |
|---|---|---|
| The current Solr estate is SolrCloud | Shards, replicas, ZooKeeper, and ops model affect complexity | If it is single-node or standalone, complexity may be lower |
| Drupal owns indexing lifecycle through Search API | Preferred migration path is reindex-from-Drupal | If Solr is fed by custom ETL outside Drupal, migration shape changes materially |
| The 1 TB figure reflects indexed data, not raw source content | Sizing and reindex time estimates depend on this | If 1 TB is raw source size, OpenSearch sizing may differ sharply |
| There are multiple Drupal indexes / collections, not just one | Impacts inventory and target design | If only one index matters, assessment scope is narrower |
| Relevance logic lives partly in Drupal config and partly in Solr schema/analyzers | Knowledge capture is critical | If logic is mostly in custom code or plugins, redesign risk rises |
| There is no clean current relevance baseline | We need analytics before promising parity | If a baseline exists, planning can accelerate |

---

## First-Pass Risk View

Current risk posture from the limited information provided:

| Area | Initial rating | Why |
|---|---|---|
| Content access | Medium | Drupal content is usually accessible, but attachment handling and enrichments may not be |
| Query/relevance parity | High | BM25, analyzer differences, module behavior, and Drupal-specific query layers create drift risk |
| Platform migration complexity | High | A 1 TB Solr estate likely means sharding, replicas, operational history, and possibly direct Solr dependencies |
| Security/access control | Unknown | Drupal roles, entitlements, and query-time filters are often under-documented |
| Team readiness | Unknown | We do not yet know who owns content, relevance, or production ops |
| Cutover/rollback | High | Large reindex plus Drupal integration changes make rollback planning important |

---

## Immediate Discovery Questions

These are the first questions I would ask, in order.

### 1. Estate Shape

- Is this definitely SolrCloud?
- How many collections matter for customer-facing search?
- How many shards and replicas are in use today?
- What is the actual on-disk Solr index size versus raw source content size?
- What Drupal versions and modules are involved?

### 2. Ownership and Flow

- Does Drupal Search API own indexing, or does another pipeline feed Solr?
- Which Drupal modules are search-critical: `search_api_solr`, `facets`, `search_api_autocomplete`, custom Views integrations?
- Can the search index be fully rebuilt from Drupal/source systems without depending on Solr as a source of truth?

### 3. Behavior and Relevance

- What are the top 10 user query patterns?
- Which behaviors are business-critical: known-item lookup, autocomplete, faceting, multilingual search, permission filtering?
- Are there custom Solr analyzers, boosts, synonyms, or plugins in production?

### 4. Operational Readiness

- What is the acceptable reindex window for 1 TB?
- What is the acceptable lag between source update and search visibility?
- What are the rollback expectations if post-cutover search quality drops?

---

## Artifact Request List

Ask for these before or immediately after the first discovery call.

### P0

- Solr `schema.xml` or managed schema for each relevant collection
- Solr `solrconfig.xml` for each relevant collection
- Output of `CLUSTERSTATUS` or equivalent SolrCloud topology summary
- Sample query logs or analytics export
- Drupal module list
- Drupal Search API index/server configuration export
- Synonym files, stopword files, protected words, taxonomies

### P1

- Top query report with click or engagement data
- Sample documents for each major content type
- Current infrastructure sizing: node count, memory, disk, IOPS expectations
- Any architecture diagram showing Drupal ↔ Solr ↔ upstream systems
- Any custom code touching search request shaping or indexing

### P2

- Incident history involving search
- Existing acceptance/UAT checklist
- Peak-season timeline and blackout windows

---

## Recommended Session 1 Agenda

Use this as a 60-90 minute first call.

1. Confirm migration driver.
   Cost, supportability, cloud alignment, relevance goals, or platform consolidation.
2. Confirm estate shape.
   SolrCloud vs standalone, collection count, 1 TB meaning, Drupal/search module footprint.
3. Map indexing lifecycle.
   Source systems, rebuildability, enrichments, attachments, custom pipelines.
4. Map business-critical search flows.
   Search pages, Views, autocomplete, facets, multilingual content, permissions.
5. Map ownership.
   Sponsor, product owner, content owner, relevance owner, platform ops owner.
6. Identify top blockers.
   Missing analytics, custom plugins, unknown entitlements, no rebuild path, no content owner.

---

## Recommended Core Roles For This Client

For this client shape, I would want explicit named owners for:

- Sponsor / stakeholder
- Product owner
- Drupal application lead
- Content owner
- Search relevance owner
- Solr platform owner
- Platform Ops / SRE owner
- Security / compliance owner
- QA / acceptance owner

If two or more of those are missing, keep the engagement in discovery mode.

---

## Drupal-Specific Judgements For A 1 TB Estate

- **Do not assume the small-site Drupal migration pattern applies unchanged.** The module-swap guidance still matters, but scale changes the risk profile significantly.
- **Reindex-from-Drupal is still the preferred end-state posture, but you may need a phased proof first.** At 1 TB, proving rebuild speed and throughput is part of the assessment.
- **Autocomplete and facets deserve separate validation tracks.** They are often the first place where users notice behavioral drift.
- **Attachment extraction and multilingual analysis are common hidden multipliers.** If PDFs, Office docs, or multiple language analyzers are involved, call that out early.
- **A "same as Solr" promise would be reckless at this stage.** The correct commitment is to preserve critical behaviors, validate them with evidence, and redesign where necessary.

---

## First-Pass Recommendation

Based on the currently known facts, the next step should be:

`Proceed with discovery and assessment only. Do not begin implementation planning yet.`

Reason:

- the current topology is not confirmed
- the `1 TB` figure needs interpretation
- Drupal-vs-external indexing ownership is unknown
- relevance evidence is unknown
- specialist roles may be needed if the estate has custom plugins, entitlements, or multilingual complexity

---

## Suggested Language For The Client

You can say this plainly:

> We should treat this as a structured assessment first, not as a straightforward platform swap. For a Drupal search estate at roughly 1 TB, the key early questions are whether Drupal truly owns the indexing lifecycle, whether the current Solr deployment is SolrCloud, how much custom relevance and access-control behavior exists, and how long a full rebuild would take. Once we answer those, we can give you a credible migration posture, risk profile, and next-step plan.

---

## Best-Guess Complexity Rating

From current information only:

- **Migration complexity:** `4/5`
- **Confidence in that rating:** `low to medium`

This may drop to `3/5` if:

- Drupal cleanly owns indexing
- Solr features are mostly standard
- access control is simple
- multilingual and attachment handling are limited

This may rise to `5/5` if:

- there are custom Solr plugins
- Solr is acting as a source of truth
- multiple direct consumers query Solr
- entitlements are complex
- there is no clean rebuild path from source systems
