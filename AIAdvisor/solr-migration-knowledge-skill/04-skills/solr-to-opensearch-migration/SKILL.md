---
name: solr-to-opensearch-migration
version: 0.2.1
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
---

# Solr → OpenSearch Migration Skill

## How to Use This Skill

Read the relevant reference file when the user's question falls in that domain. The SKILL.md
quick-reference tables handle most common questions. For deeper work, load the reference.

| User needs | Read |
|------------|------|
| Migration strategy, phases, dual-write, cutover | `references/migration-strategy.md` |
| AWS service config, sizing, auth, snapshots, cost | `references/aws-opensearch-service.md` |
| Solr feature audit / what survives migration | `references/solr-concepts-reference.md` |
| Query translation (DisMax → Query DSL, facets → aggs) | `references/query-syntax-mapping.md`* |
| Schema translation (schema.xml → mappings) | `references/schema-field-type-mapping.md`* |
| Project process, roles, risks, relevance methodology | `references/consulting-methodology.md` |
| Team shape, role gaps, escalation triggers | `references/roles-and-escalation-patterns.md` |
| Business/Discovery concerns, risk inventory | `references/consulting-concerns-inventory.md` |
| **Drupal migration (Search API Solr → OpenSearch)** | **`references/scenario-drupal.md`** |
| **Small business / Low resource (the "Daphne" persona)** | **`references/scenario-drupal.md`** |

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
> `references/query-syntax-mapping.md` in `01-sources/opensearch-migration/`

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
> `references/schema-field-type-mapping.md` in `01-sources/opensearch-migration/`

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
   `03-specs/techproducts-demo/`.

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
| `references/consulting-concerns-inventory.md` | 20KB | Discovery matrix: 200 items across 20 risk groups |

**Platform-specific integration** (client libraries, code patterns) is intentionally out of scope
for this skill — it belongs in a separate platform skill (Spring/Kotlin, Python, Rails, etc.).
Raw source material is available in `../../../01-sources/opensearch-fundamentals/` for reference.

**Full source corpus** (deeper reading, original context):
`../../../01-sources/` — 45 files across opensearch-migration, opensearch-best-practices,
aws-opensearch-service, opensearch-fundamentals, solr-reference, community-insights
