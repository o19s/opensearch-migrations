---
name: solr-to-opensearch-migration
description: >
  Expert guidance for migrating Apache Solr (SolrCloud) collections to AWS OpenSearch Service.
  Use this skill whenever someone is working on: Solr-to-OpenSearch or Solr-to-Elasticsearch
  migration planning or execution; translating Solr queries (DisMax, eDisMax, Standard parser,
  fq, facet, group, mlt, spellcheck) to OpenSearch Query DSL; mapping Solr schema (schema.xml,
  fieldType, copyField, dynamic fields, analyzers) to OpenSearch index mappings; designing
  dual-write, shadow-traffic, or cutover migration strategies; diagnosing relevance differences
  after migration (BM25 vs TF-IDF); configuring AWS OpenSearch Service (provisioned or serverless,
  SigV4, VPC, FGAC, ISM, snapshots);
  or applying consulting methodology for a search migration engagement. Also trigger when
  someone asks about SolrCloud, configsets, ZooKeeper (in search context), collection management,
  SolrJ client migration, or search engine comparison questions involving Solr.
compatibility: Requires MCP tools for guided workflow (schema/query conversion, session management, report generation). Knowledge references work standalone.
metadata:
  author: opensearch-search-consulting
  version: "0.3.0"
---

# Solr → OpenSearch Migration Skill

## How to Use This Skill

**If you are an LLM agent** (Claude via MCP, Kiro, Bedrock): Follow the "Guided Migration
Workflow" section below. It tells you how to drive the conversation, which tools to call,
and what to record at each step.

**If you are a human or a non-LLM client**: Use the reference lookup table below. The
quick-reference tables in this file handle most common questions. For deeper work, load
the appropriate reference file.

| User needs | Read |
|------------|------|
| Migration strategy, phases, dual-write, cutover | `references/migration-strategy.md` |
| Source audit, readiness, complexity scoring | `references/02-pre-migration.md` |
| Relevance validation, go/no-go, shadow traffic, rollback posture | `references/05-validation-cutover.md` |
| Approval model, safety tiers, human gates, escalation | `references/09-approval-and-safety-tiers.md` |
| Playbook structure, review gates, artifact expectations | `references/10-playbook-artifact-and-review.md` |
| AWS service config, sizing, auth, snapshots, cost | `references/aws-opensearch-service.md` |
| Solr feature audit / what survives migration | `references/solr-concepts-reference.md` |
| Query translation (DisMax → Query DSL, facets → aggs) | `sources/opensearch-migration/query-syntax-mapping.md`* |
| Schema translation (schema.xml → mappings) | `sources/opensearch-migration/schema-field-type-mapping.md`* |
| Project process, roles, risks, relevance methodology | `references/consulting-methodology.md` |
| Team shape, role gaps, escalation triggers | `references/roles-and-escalation-patterns.md` |
| Business/Discovery concerns, risk inventory | `references/consulting-concerns-inventory.md` |
| **Drupal migration (Search API Solr → OpenSearch)** | **`references/scenario-drupal.md`** |
| **Small business / Low resource (the "Daphne" persona)** | **`references/scenario-drupal.md`** |
| Edge cases, obscure gotchas, long-tail issues | `references/08-edge-cases-and-gotchas.md` *(secondary)* |

---

## Guided Migration Workflow (LLM-Driven)

When you are an LLM agent (Claude via MCP, Kiro, Bedrock, or similar) guiding a user
through a migration, follow this 8-step workflow. You own the conversation flow — the
Python tools handle the domain logic. Your job is to ask good questions, call the right
tools, record findings, and produce a useful report.

**Key principles:**
- Be suggestive, not enforcing. If the user pastes a schema at Step 0, convert it immediately.
- Flag breaking incompatibilities the moment you detect them — don't wait for the report.
- Record everything in session state so the report has real data, not templates.
- Tailor depth to the stakeholder: developers want code, managers want timelines, architects want trade-offs.

### Available Tools

Use these MCP tools throughout the workflow:

| Tool | When to use |
|------|-------------|
| `convert_schema_xml(schema_xml)` | User provides schema.xml content |
| `convert_schema_json(schema_api_json)` | User provides Schema API JSON |
| `convert_query(solr_query)` | User provides a Solr query string |
| `generate_report(session_id)` | User wants the final migration report |
| `get_migration_checklist()` | User asks "what do I need to do?" |
| `get_field_type_mapping_reference()` | User asks about field type equivalents |
| `record_fact(session_id, key, value)` | Store any discovered information |
| `record_incompatibility(session_id, category, description, recommendation)` | Flag an issue |
| `record_client_integration(session_id, name, kind, notes)` | Record a consuming application |
| `get_session_summary(session_id)` | Check what's been collected so far |
| `aws_knowledge_search(query, topic)` | Look up AWS-specific guidance |
| `inspect_solr(collection, solr_url, session_id)` | Full inspection: schema + metrics + luke + system; stores findings in session |
| `inspect_solr_schema(collection, solr_url)` | Fetch live schema from running Solr |
| `inspect_solr_metrics(group, solr_url)` | Fetch metrics (cache, query rates, JVM) |
| `inspect_solr_luke(collection, solr_url)` | Index stats (doc count, field cardinality) |
| `inspect_solr_mbeans(collection, category, solr_url)` | Handler stats (request counts, latency) |
| `inspect_solr_collections(solr_url)` | List all collections or cores |
| `inspect_solr_system(solr_url)` | System info (version, JVM, heap, CPU) |

### Step 0 — Stakeholder Identification

**Goal:** Understand who you're talking to so you can tailor everything that follows.

Ask about the user's role. If they're a:
- **Developer** → focus on code changes, client library migration, query translation
- **Search engineer** → emphasize relevance impact, analyzer chains, scoring differences
- **DevOps/Platform** → focus on cluster sizing, infrastructure, operational differences
- **Architect** → cover full migration strategy, risk assessment, phasing, trade-offs
- **Manager** → emphasize timelines, effort estimates, risks, decision points

Record: `record_fact(session_id, "stakeholder_role", role)`

If the user doesn't want to answer or jumps straight to technical questions, that's fine —
record "unknown" and proceed. Don't block progress.

### Step 1 — Schema Acquisition

**Goal:** Get the Solr schema and convert it.

Ask the user for their schema in one of two formats:
- **schema.xml** — the full XML or at least the `<fields>` and `<fieldTypes>` sections
- **Schema API JSON** — output of `curl http://solr:8983/solr/COLLECTION/schema`

When received, call `convert_schema_xml()` or `convert_schema_json()`. Review the result:

1. Check the conversion output for any fields that defaulted to `keyword` (may indicate
   an unrecognized field type — the mapping table doesn't cover every custom Solr type)
2. Look for `<analyzer>` blocks in the schema — these are the most important part.
   If analyzers are present, explain the conversion and flag any tokenizers/filters that
   need manual review (see `data/analyzer-mappings.json` for the mapping table)
3. Look for `<copyField>` directives and explain the `copy_to` equivalent
4. Check for `<dynamicField>` patterns beyond `*_` prefix — non-standard patterns may
   need custom dynamic_templates

For each issue found: `record_incompatibility(session_id, category, description, recommendation)`

Record: `record_fact(session_id, "schema_migrated", true)`

If the user can't provide the schema yet, ask them to describe their setup (collection
count, approximate field count, notable field types) and note that you'll need the actual
schema later for accurate conversion.

### Step 2 — Schema Review

**Goal:** Walk the user through the conversion results and catch anything the converter missed.

Present a summary:
- Number of fields and field types converted
- Any incompatibilities flagged
- Analyzer chain conversions (if any)

Ask the user:
1. Do these field mappings look correct for your use case?
2. Are there any fields with special behavior I should know about?
3. (If analyzers present) Please review the tokenizer and filter mappings — this is where
   relevance differences are most likely.

This is a collaborative review step. The user knows their data better than you do.
Listen for corrections and update the session accordingly.

### Step 3 — Query Translation

**Goal:** Translate the user's most important Solr queries to OpenSearch Query DSL.

Ask for queries. Useful prompts:
- "What does your most common search request look like?"
- "Do you use DisMax or eDisMax? Can you share the request handler config from solrconfig.xml?"
- "Any filter queries (fq), facets, or boost functions?"

When you receive a query, call `convert_query()`. Review the result:

1. **Check for eDisMax parameters** (`qf`, `pf`, `mm`, `bq`, `bf`) — these are the
   most common and most impactful. If present, explain the multi_match equivalent and
   flag any semantic differences (especially `mm` behavior — see `data/query-parameter-mappings.json`)
2. **Check for filter queries** (`fq`) — these become `bool.filter` clauses
3. **Check for facets** — explain the aggregation equivalent
4. **Check for boost values** (`^N`) — make sure they're preserved in the conversion
5. **Flag no-equivalent features**: streaming expressions, graph traversal, XCJF,
   payload scoring → these need architectural redesign, not translation

For each issue: `record_incompatibility(session_id, category, description, recommendation)`

Record: `record_fact(session_id, "queries_translated", count)`

### Step 4 — Customization Assessment

**Goal:** Discover custom Solr features that affect migration scope and risk.

Ask about:

**Request handlers & search components:**
- Custom request handlers beyond `/select` and `/update`?
- Custom SearchComponents (e.g., query elevation, custom highlighting)?

**Plugins:**
- Custom tokenizers, filters, or analyzers (Java classes)?
- Custom update processors (updateRequestProcessorChain)?
- Third-party plugins?

**Authentication & authorization:**
- How is Solr secured? (BasicAuth, Kerberos, custom, none)
- Document-level or field-level security requirements?

**Operational patterns:**
- SolrCloud or standalone?
- Streaming expressions, CDCR, Data Import Handler?
- Atomic updates (partial document updates)?

For each custom feature discovered, check the incompatibility catalog
(`data/incompatibility-catalog.json`) and record any issues. Common triggers:
- Streaming expressions → QUERY-007 (Breaking, high severity)
- CDCR → OPS-006 (Unsupported, high severity)
- Data Import Handler → OPS-008 (Unsupported, high severity)
- Custom update processors → OPS-007 (Unsupported, medium severity)
- Atomic updates → OPS-004 (Behavioral, high severity)
- Custom similarity → SCHEMA-005 (Unsupported, high severity)

Record: `record_fact(session_id, "customizations_assessed", true)`

### Step 5 — Infrastructure Assessment

**Goal:** Understand the current Solr topology and estimate OpenSearch sizing.

Ask about:

**Cluster topology:** node count, collection count, shard count, replica factor,
total index size (GB)

**Hardware:** instance type or specs, JVM heap size

**Traffic:** queries per second, indexing rate, peak/average ratio

**Target:** AWS managed vs self-managed, single or multi-region, SLA requirements

Use sizing heuristics from `data/sizing-heuristics.json`:
- Node count: `os_data_nodes = max(solr_nodes * 2, 3)` (replica co-location ban)
- Storage: 3x current index size per node for overhead
- Memory: JVM heap = min(RAM/2, 32GB)
- Add 3 dedicated master nodes for production

Present the sizing recommendation with explanation of why OpenSearch needs more nodes
(the replica co-location rule is the key insight).

Record facts: `solr_node_count`, `collection_count`, `total_index_size_gb`, `target_platform`, etc.

### Step 6 — Client Integration Assessment

**Goal:** Identify all applications and libraries that connect to Solr.

Ask about:

**Client libraries:** SolrJ (Java), pysolr (Python), RSolr (Ruby), Solarium (PHP), custom HTTP

**Frameworks:** Spring Data Solr, Drupal Search API Solr, Magento, custom

**Integration patterns:** Direct HTTP? Search abstraction layer? Multiple apps sharing Solr?

For each integration, record it and provide migration guidance:
- `record_client_integration(session_id, name, kind, migration_notes)`

Key guidance by client:
- **SolrJ → opensearch-java**: Query builders change significantly. Medium effort.
- **pysolr → opensearch-py**: API similar to elasticsearch-py. Medium effort.
- **Spring Data Solr → spring-data-opensearch**: Repository interfaces may need rewrite. High effort.
- **Drupal Search API Solr → Search API OpenSearch**: Module swap, field remapping. High effort.
- **Custom HTTP → updated endpoints**: URL patterns and request/response format change. Medium effort.

### Step 7 — Report Generation

**Goal:** Produce a comprehensive migration report from everything collected.

Before generating, summarize what's been collected:
- Stakeholder role
- Schema conversion status and incompatibilities
- Queries translated and issues flagged
- Customizations discovered
- Infrastructure assessment
- Client integrations identified

Ask: "Shall I generate the full migration report? I can also go back to any step first."

When confirmed, call `generate_report(session_id)`. The report should cover:
1. **Executive summary** (tailored to stakeholder role)
2. **Incompatibilities** (grouped by severity: breaking → behavioral → unsupported)
3. **Schema migration** (field mappings, analyzer changes)
4. **Query migration** (translated queries, flagged issues, relevance impact)
5. **Infrastructure recommendations** (sizing, topology, platform)
6. **Client integration changes** (per-library migration actions)
7. **Major milestones and sequencing** (from the 5-phase model)
8. **Risk assessment and blockers**
9. **Effort and cost estimates** (using heuristics from `data/sizing-heuristics.json`)

### Workflow Flexibility

**Users don't have to follow the steps in order.** Common patterns:

- **"I just want to convert this schema"** → Jump to Step 1, convert, present results
  with incompatibilities. Don't force the full workflow.
- **"Give me a quick assessment"** → Ask 3-4 key questions (schema available? eDisMax?
  custom plugins? cluster size?) and generate a preliminary report.
- **"Express mode"** → See the Express Mode section below. Generate everything with
  assumptions.
- **"Let's go deeper on queries"** → Spend multiple turns on Step 3. Translate several
  query patterns, discuss edge cases.
- **Returning user** → `get_session_summary(session_id)` to see where they left off.
  Resume from the appropriate step.

**The report can be generated at any point** with whatever data is available. Missing
steps produce sections that say "Not yet assessed" rather than blocking generation.

### Data Files Reference

These files in `data/` contain the domain knowledge that informs your guidance:

| File | Use it for |
|------|-----------|
| `data/analyzer-mappings.json` | Tokenizer/filter/char_filter Solr→OpenSearch mappings |
| `data/query-parameter-mappings.json` | DisMax/eDisMax/fq/facet parameter translation patterns |
| `data/incompatibility-catalog.json` | Structured list of all known incompatibilities with detection methods |
| `data/sizing-heuristics.json` | Cluster sizing formulas, effort estimation, cost heuristics |
| `data/workflow-step-prompts.json` | Step-by-step prompt text and fact recording templates |

---

## Core Mental Model

Solr and OpenSearch share the Apache Lucene foundation but diverge in almost every other layer.
**Full refactor beats lift-and-shift** because:

- Solr's DisMax/eDisMax has no 1:1 equivalent — queries must be redesigned using Query DSL
- Relevance scoring: Solr defaults to TF-IDF, OpenSearch defaults to BM25 — expect 30-40%
  ranking difference in top-10 results without explicit tuning
- XML configsets cannot be mechanically translated to JSON index settings
- ZooKeeper-based coordination is replaced by embedded Raft — operational model changes significantly
- Shard + replica co-location rules differ (OpenSearch forbids primary+replica on same node)

The migration is the opportunity to redesign search with OpenSearch idioms. A port is a missed opportunity and usually produces subtle bugs.

---

## Critical Differences Quick Reference

| Concept | Solr | OpenSearch | Migration note |
|---------|------|-----------|----------------|
| Cluster coordination | ZooKeeper + Overseer | Embedded Raft | ZK removed entirely — large ops win |
| Unit of organisation | Collection | Index | 1:1 rename, not 1:1 behavior |
| Config management | configset XML in ZK | JSON mappings + settings via API | Full rewrite required |
| Default similarity | TF-IDF (ClassicSimilarity) | BM25 | Re-tune boosts and field weights |
| Soft commit | Explicit (autoSoftCommit) | refresh_interval (default 1s) | Nearly equivalent, different knobs |
| Hard commit | Explicit (autoCommit) | fsync on flush | Less user-controlled in OpenSearch |
| Atomic updates | Yes, with _version_ | Partial update via `doc` | Different semantics — test carefully |
| Real-time Get | /get handler (tlog-based) | GET /_doc (consistent) | OpenSearch RTG is simpler |
| Nested documents | Block join, toParent/toChild | `nested` type OR `join` field | Block join → nested type is the path |
| Shard+replica colocation | Allowed | Forbidden | Plan for 2× node count minimum |
| Query language | LuceneQP, DisMax, eDisMax | Query DSL (JSON) | Must rewrite all queries |
| Facets | facet.field, facet.range, pivot | terms/range/date_histogram aggs | Conceptually same, syntax different |
| Grouping | group=true, group.field | collapse + top_hits (limited) | Reduced functionality — evaluate carefully |
| CDCR (cross-dc replication) | Yes | Cross-cluster replication (CCR) | Different model, AWS may not support CCR |
| Streaming expressions | Yes (full data pipeline) | No equivalent | Redesign needed for heavy users |

---

## Migration Phase Overview

```
Phase 1: Audit & Design (2–4 wks)
  ├─ Inventory: collections, schema, queries, traffic, special features
  ├─ Design: OpenSearch mappings, query equivalents, index strategy
  └─ Provision: AWS OpenSearch Service cluster + Dashboards

Phase 2: Build & Validate (2–4 wks)
  ├─ Implement index mappings and query translation layer
  ├─ Load representative data subset
  └─ Offline relevance comparison (Quepid/RRE) vs Solr baseline

Phase 3: Dual-Write (2–6 wks)
  ├─ Write to both Solr and OpenSearch in production
  ├─ Historical catchup: reindex all existing documents
  ├─ Shadow-traffic comparison: route % to OpenSearch, compare results
  └─ Tune until relevance KPIs meet SLO

Phase 4: Gradual Cutover (1–2 wks)
  ├─ 5% → 25% → 50% → 100% traffic shift
  ├─ Go/no-go gates: relevance, latency p99, error rate
  └─ Keep Solr warm for 30–60 days rollback window

Phase 5: Cleanup (2–4 wks)
  └─ Remove dual-write, decommission Solr + ZooKeeper, finalise docs
```

> For full strategy detail including decision trees and go/no-go criteria: `references/migration-strategy.md`

---

## Query Translation Quick Reference

### DisMax / eDisMax → multi_match

```json
// Solr: q=search terms&qf=title^3 body^1&mm=2<75%&pf=title^5&ps=2
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "search terms",
            "fields": ["title^3", "body^1"],
            "type": "best_fields",
            "minimum_should_match": "75%"
          }
        },
        {
          "match_phrase": {
            "title": { "query": "search terms", "boost": 5, "slop": 2 }
          }
        }
      ]
    }
  }
}
```

### Filter queries (fq) → bool.filter

```json
// Solr: fq=status:active&fq=price:[10 TO 100]
// OpenSearch: filter context = no scoring, cached
{
  "query": {
    "bool": {
      "must": { "multi_match": { "query": "...", "fields": ["title","body"] }},
      "filter": [
        { "term": { "status": "active" }},
        { "range": { "price": { "gte": 10, "lte": 100 }}}
      ]
    }
  }
}
```

### Facets → Aggregations

```json
// Solr: facet=true&facet.field=category&facet.range=price&facet.range.start=0&...
{
  "aggs": {
    "by_category": { "terms": { "field": "category", "size": 20 }},
    "by_price": {
      "range": {
        "field": "price",
        "ranges": [{"to": 25}, {"from": 25, "to": 100}, {"from": 100}]
      }
    }
  }
}
```

### Boost functions (bf/bq) → function_score

```json
// Solr: bf=recip(ms(NOW,date),3.16e-11,1,1)^2
{
  "query": {
    "function_score": {
      "query": { "multi_match": { "query": "...", "fields": ["title"] }},
      "functions": [{
        "gauss": { "date": { "origin": "now", "scale": "30d", "decay": 0.5 }},
        "weight": 2
      }],
      "boost_mode": "multiply"
    }
  }
}
```

### Pagination: start/rows → from/size and search_after

```json
// Solr: start=0&rows=20  →  OpenSearch: "from": 0, "size": 20
// For deep pagination (avoid from/size beyond 10k):
{
  "size": 20,
  "sort": [{"date": "desc"}, {"_id": "asc"}],
  "search_after": ["2024-01-15T10:30:00Z", "doc-abc123"]
}
```

> For all 41 query patterns including MLT, spellcheck/suggesters, grouping, geo:
> `references/query-syntax-mapping.md` in `sources/opensearch-migration/`

---

## Schema Translation Quick Reference

### Field type mapping

| Solr fieldType | OpenSearch type | Notes |
|----------------|-----------------|-------|
| StrField | keyword | Exact match, no analysis |
| TextField | text | Requires explicit analyzer |
| IntPointField | integer | |
| LongPointField | long | |
| FloatPointField | float | |
| DoublePointField | double | |
| DatePointField | date | format: `strict_date_optional_time` |
| BoolField | boolean | |
| LatLonPointSpatialField | geo_point | |
| TrieIntField (legacy) | integer | Use Point fields in Solr 7+ |

### Dynamic fields → dynamic_templates

```json
// Solr: <dynamicField name="*_s" type="string" indexed="true" stored="true"/>
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keyword": {
          "match": "*_s",
          "mapping": { "type": "keyword" }
        }
      }
    ]
  }
}
```

### copyField → copy_to

```json
// Solr: <copyField source="title" dest="_text_"/>
//        <copyField source="body"  dest="_text_"/>
{
  "mappings": {
    "properties": {
      "title": { "type": "text", "copy_to": "_text_" },
      "body":  { "type": "text", "copy_to": "_text_" },
      "_text_": { "type": "text" }
    }
  }
}
```

### Index vs query analyzer

```json
// Solr: <analyzer type="index">...</analyzer> <analyzer type="query">...</analyzer>
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "my_index_analyzer",
        "search_analyzer": "my_query_analyzer"
      }
    }
  }
}
```

> For full mapping including nested docs, docValues, omitNorms, complex analyzer chains:
> `references/schema-field-type-mapping.md` in `sources/opensearch-migration/`

---

## Top 8 Production Gotchas

1. **Relevance shock** — BM25 vs TF-IDF differences surface as "search got worse" complaints.
   Build a relevance test harness (Quepid + judgment set) *before* migration. Measure the delta, don't guess.

2. **Shard co-location** — OpenSearch forbids primary + replica on the same node.
   A 2-node Solr cluster with 1 replica per shard needs *at least* 2 OpenSearch data nodes.
   Plan hardware before designing shard topology.

3. **Dynamic mapping landmines** — OpenSearch eagerly creates field types from the first doc seen.
   A numeric field sent as a string on doc 1 locks the type. Set `"dynamic": "strict"` in production mappings.

4. **Atomic update semantics differ** — Solr's atomic updates use the transaction log to merge fields;
   OpenSearch partial updates retrieve-merge-reindex. Under concurrent writes, behaviour differs.
   Test heavily if your indexing pipeline uses Solr's `set`/`add`/`inc` update modifiers.

5. **AWS version lag** — AWS OpenSearch Service trails open-source releases by 1-2 versions.
   Check feature availability against your *target AWS version*, not the open-source latest.

6. **`from`/`size` pagination cliff** — OpenSearch's default `index.max_result_window` is 10,000.
   Any query with `from + size > 10000` throws an error. Switch to `search_after` for deep pagination early.

7. **Refresh vs soft commit timing** — Solr's `autoSoftCommit` and OpenSearch's `refresh_interval`
   are conceptually similar (NRT visibility) but the defaults and interactions with bulk indexing differ.
   During bulk loads, set `refresh_interval: -1`, bulk index, then force refresh. Don't rely on defaults.

8. **Disk Watermark Blocks** — OpenSearch blocks index creation if disk usage exceeds **percentages** (e.g. High: 90%), even if hundreds of GB remain free.
   Always check `_cat/nodes?h=disk.used_percent` before a migration, especially in dense or shared environments. If blocked, you may need to relax `cluster.routing.allocation.disk.watermark.*` thresholds.

---

## AWS OpenSearch Service Quick Decisions

| Question | Guidance |
|----------|----------|
| Provisioned vs Serverless? | Provisioned for predictable workloads; Serverless for spiky/dev/unknown scale |
| Instance type? | r6g.large–2xlarge for search-heavy; m6g for balanced; c6g if CPU-bound |
| Need dedicated masters? | Yes if ≥10 data nodes or ≥10 indices with heavy traffic |
| 2-AZ or 3-AZ? | 3-AZ for production; 2-AZ only for dev/cost-sensitive |
| VPC or public? | VPC always for production |
| Auth model? | IAM + SigV4 for service-to-service; FGAC + internal DB for multi-tenant Dashboards |
| Snapshot for migration? | Manual snapshot of Solr data → S3 → restore into OpenSearch is the cleanest path |

> Full decision rationale and cost model: `references/aws-opensearch-service.md`

---

## Consulting Process Quick Reference

When leading a migration engagement, the non-negotiables are:

1. **Experiment-driven** — every relevance change is a hypothesis + measurement. No exceptions.
2. **Knowledge transfer first** — client must own the result. Document everything on a wiki.
3. **Challenge the premise** — if migration is political with no customer benefit, say so clearly.
4. **Content access is critical path** — get it on day one. This is the #1 cause of missed milestones.
5. **Baseline before tuning** — measure Solr relevance with the same tools you'll use for OpenSearch.
   "We can't beat a target we've never measured."
6. **Hello Search milestone** — get something running early. Team morale depends on visible progress.

> Full methodology including roles, risk register, common issues playbook, reporting culture:
> `references/consulting-methodology.md`

---

## Express Mode (YOLO)

### What This Is

Express mode generates a **complete migration specification package** from minimal input — as
little as a collection name and a schema.xml paste. The skill fills in every gap with its best
expert judgment rather than stopping to ask clarifying questions.

**Trigger phrases:** "express mode", "YOLO mode", "just do it", "generate a full spec",
"quick migration spec", "don't ask questions", or any clear signal the user wants output over dialogue.

### Output Banner

Every express-mode artifact **must** open with this banner (adapt the collection name):

```
╔══════════════════════════════════════════════════════════════════════╗
║  ⚡ EXPRESS MODE — GENERATED WITH ASSUMPTIONS ⚡                    ║
║                                                                      ║
║  This spec was generated in express ("YOLO") mode. The skill made    ║
║  its best expert guesses where information was missing. Every        ║
║  assumption is marked [ASSUMED: ...] for your review.                ║
║                                                                      ║
║  DO NOT execute this migration without reviewing assumptions.        ║
║  Express mode is a starting point, not a greenlight.                 ║
║                                                                      ║
║  Skill-Version: {version}                                            ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Default Assumptions

When information is missing, use these defaults. **Always** mark each with
`[ASSUMED: reason]` inline so the user can grep and review.

| Missing info | Default assumption | Risk level |
|---|---|---|
| Solr version | 8.x or 9.x (modern, Point fields) | Low |
| Collection count | Single collection | Low |
| Document count | 10K–500K (moderate) | Medium |
| Query patterns | eDisMax with basic facets | Medium |
| Platform/framework | Spring Boot 3.x / Kotlin | Low |
| AWS region | us-east-1 | Low |
| OpenSearch version | Latest AWS-supported (2.x) | Low |
| Instance type | r6g.large.search (2-node, 2-AZ) | Medium |
| Auth model | IAM + SigV4 | Low |
| Relevance requirements | Parity with current Solr behavior | **High** |
| Custom analyzers | Standard analyzer chain | **High** |
| Nested/join documents | None (flat documents) | **High** |
| Streaming expressions | Not in use | Medium |
| CDCR / replication | Not in use | Medium |
| Dual-write duration | 2–4 weeks shadow traffic | Medium |
| Rollback window | 30 days keep-Solr-warm | Low |

### Generation Rules

1. **Generate the full spec package** — README, steering docs (product.md, tech.md,
   structure.md), requirements.md, design.md, tasks.md, MANIFEST.txt — same structure as
   `examples/techproducts-demo/`.

2. **Mark every assumption** with `[ASSUMED: <what was assumed and why>]`. Place these inline
   near the affected content, not buried in a footnote.

3. **Include an assumptions summary** at the top of README.md listing all assumptions with
   their risk levels (Low / Medium / High). High-risk assumptions get a brief explanation of
   what could go wrong if the assumption is incorrect.

4. **Use real field names** from any schema.xml or config the user provides. Do not invent
   placeholder fields when real ones are available.

5. **Assign a complexity score** (1–5) based on whatever information is available. State what
   would change the score.

6. **Flag "must-verify" items** — things that are dangerous to get wrong even in a draft:
   - Custom similarity (TF-IDF tuning, custom scorers)
   - Nested/parent-child document structures
   - Streaming expressions or graph traversal
   - Multi-collection joins
   - Custom update processors in the indexing chain

7. **Don't sandbag the output.** The point of express mode is to show the skill's full
   capability. Generate detailed, concrete, copy-pasteable artifacts — not vague summaries
   with "TBD" placeholders.

### Post-Generation Guidance

After generating, tell the user:

> **Next steps:** Search this spec for `[ASSUMED:` to find every assumption I made.
> High-risk assumptions are flagged — review those first. The spec is designed to be
> edited, not executed blindly. When you're ready to refine, I can walk through any
> section interactively.

---

## References Index

| File | Size | Contents |
|------|------|----------|
| `references/migration-strategy.md` | 16KB | Strategy, dual-write, cutover, timelines, ETL decision tree |
| `references/aws-opensearch-service.md` | 23KB | AWS service config, sizing, auth, networking, cost model |
| `references/solr-concepts-reference.md` | 17KB | Solr feature audit, equivalence map, migration complexity scoring |
| `references/consulting-methodology.md` | 15KB | OSC playbook: roles, risks, process, relevance methodology |
| `references/02-pre-migration.md` | Expanded source-audit method: collection inventory, query/schema audit, readiness checks, complexity scoring, discovery prompts. |
| `references/05-validation-cutover.md` | Relevance validation, judged evaluation, evidence packs, go/no-go gates, staged rollout, cutover and rollback posture. |
| `references/09-approval-and-safety-tiers.md` | Observe / Propose / Execute governance, approval objects, never-autonomous actions, audit expectations, escalation rules. |
| `references/10-playbook-artifact-and-review.md` | Defines the migration playbook as the primary reviewable artifact, with minimum sections, approval gates, and reviewer checklists. |
| `references/consulting-concerns-inventory.md` | 20KB | Discovery matrix: 200 items across 20 risk groups |

### Secondary References

These files are loaded on demand when edge cases or uncommon features are relevant:

| File | Contents |
|------|----------|
| `references/08-edge-cases-and-gotchas.md` | Long-tail migration issues: obscure query translation traps, schema pitfalls, no-equivalent features, operational surprises. 30+ curated external source links. |

> **Primary vs Secondary:** Primary references (01–07) cover the core migration path — the
> 80% case that applies to most engagements. Secondary references cover the remaining 20%:
> edge cases, obscure Solr features, and issues that only surface in specific configurations.
> Secondary references are not loaded by default to keep context focused.

### Data Files (programmatic, for tool consumption)

| File | Contents |
|------|----------|
| `data/analyzer-mappings.json` | Solr→OpenSearch tokenizer, filter, char_filter mappings with parameter translation |
| `data/query-parameter-mappings.json` | DisMax/eDisMax/fq/facet/highlight/sort/pagination parameter mappings with examples |
| `data/incompatibility-catalog.json` | 30+ structured incompatibilities with detection methods, severity, and recommendations |
| `data/sizing-heuristics.json` | Cluster sizing formulas, effort estimation tables, cost heuristics |
| `data/workflow-step-prompts.json` | Step 0-7 prompt text, facts to record, skip conditions, next-step routing |

**Platform-specific integration** (client libraries, code patterns) is intentionally out of scope
for this skill — it belongs in a separate platform skill (Spring/Kotlin, Python, Rails, etc.).
Raw source material is available in `../../../sources/opensearch-fundamentals/` for reference.

**Full source corpus** (deeper reading, original context):
`../../../sources/` — 45 files across opensearch-migration, opensearch-best-practices,
aws-opensearch-service, opensearch-fundamentals, solr-reference, community-insights
