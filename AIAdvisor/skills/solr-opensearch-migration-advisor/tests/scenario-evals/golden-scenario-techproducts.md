# Golden Test Scenario: TechProducts

A complete walk-through of the 8-step migration workflow using Solr's bundled
TechProducts example. Tests the advisor's technical depth: schema conversion,
query translation, analyzer chains, and incompatibility detection.

**Persona:** Alex, a search engineer migrating a Spring Boot app from Solr to OpenSearch.
**Complexity:** 2/5 (simple schema, small data, standard features).
**Expected report quality:** Precise field mappings, all 8 query patterns translated,
analyzer chain fully converted, no false incompatibilities.

---

## Step 0 — Stakeholder Identification

**User input:**
> I'm a search engineer. We're migrating our product catalog from Solr to OpenSearch on AWS.
> The catalog uses the TechProducts schema — pretty standard stuff.

**Expected advisor behavior:**
- Record `stakeholder_role: search_engineer`
- Tailor responses toward relevance impact, analyzer chains, scoring differences
- Respond with something like: "I'll focus on relevance impact and analyzer conversion. Let's start with your schema."

**Facts recorded:**
```json
{"stakeholder_role": "search_engineer"}
```

---

## Step 1 — Schema Acquisition

**User input:**
> Here's our schema. We have 15 explicit fields and 7 dynamic patterns:
>
> Explicit fields: id (string), name (text_general), manu (text_general),
> manu_exact (string), cat (text_general), features (text_general),
> includes (text_general), weight (pfloat), price (pfloat), popularity (pint),
> inStock (boolean), manufacturedate_dt (pdate), store (location),
> description (text_general), comments (text_general)
>
> Dynamic fields: *_s (string), *_i (pint), *_f (pfloat), *_l (plong),
> *_b (boolean), *_dt (pdate), *_p (location)
>
> Copy fields: name → _text_, manu → _text_, features → _text_,
> includes → _text_, description → _text_, comments → _text_
>
> Analyzers for text_general:
> Index: StandardTokenizer → LowerCaseFilter → StopFilter (English)
> Query: StandardTokenizer → LowerCaseFilter → StopFilter → SynonymGraphFilter
>   Synonyms: "hard disk" ↔ "hard drive", "hd" ↔ "hard drive",
>   "ipod" ↔ "portable music player", "camera" ↔ "photo device"

**Expected advisor behavior:**
- Call `convert_schema_xml()` or process the description
- Map all 15 fields correctly:
  - `id` → keyword
  - `name`, `manu`, `cat`, `features`, `includes`, `description`, `comments` → text
  - `manu_exact` → keyword
  - `weight`, `price` → float
  - `popularity` → integer
  - `inStock` → boolean
  - `manufacturedate_dt` → date
  - `store` → geo_point
- Convert 7 dynamic patterns to dynamic_templates
- Convert copyField directives to copy_to on source fields
- Convert analyzer chains to OpenSearch analysis block:
  ```json
  {
    "analysis": {
      "analyzer": {
        "text_general_index": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop"]
        },
        "text_general_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop", "techproducts_synonyms"]
        }
      },
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "techproducts_synonyms": {
          "type": "synonym_graph",
          "synonyms": [
            "hard disk, hard drive",
            "hd, hard drive",
            "ipod, portable music player",
            "camera, photo device"
          ]
        }
      }
    }
  }
  ```
- Flag: synonym file needs to be accessible to OpenSearch nodes (inline OK for demo, file-based for production)
- Record `schema_migrated: true`

**Incompatibilities to flag:**
- SCORING-001: TF-IDF → BM25 default similarity (Behavioral, high) — expect 30-40% ranking difference
- Note: no breaking incompatibilities in this simple schema

**Facts recorded:**
```json
{
  "schema_migrated": true,
  "field_count": 15,
  "dynamic_field_count": 7,
  "has_analyzers": true,
  "has_copy_fields": true,
  "has_synonyms": true
}
```

---

## Step 2 — Schema Review

**User input:**
> Looks good. The synonym expansion is important — we rely on "hd" matching "hard drive"
> results. Will that still work?

**Expected advisor behavior:**
- Confirm: synonym_graph filter at query time will expand "hd" → "hard drive", same as Solr
- Note: synonym expansion happens at query time only (matching Solr's setup), so index doesn't need rebuilding when synonyms change
- Caution: test with the `_analyze` API to verify token expansion:
  ```
  POST /techproducts/_analyze
  {
    "analyzer": "text_general_query",
    "text": "hd"
  }
  ```
  Expected output: tokens `["hard", "drive"]`
- Note: BM25 will score synonym-expanded terms differently than TF-IDF. A query for "hd" that expands to "hard drive" may rank results differently. This is expected and part of the 30-40% ranking difference.

**Facts recorded:**
```json
{"schema_reviewed": true, "synonym_expansion_critical": true}
```

---

## Step 3 — Query Translation

**User input:**
> Here are our main query patterns:
>
> 1. Keyword search: q=hard drive&qf=name^2 features^1 cat^0.5&defType=edismax
> 2. Stock filter: q=*:*&fq=inStock:true
> 3. Price range: q=*:*&fq=price:[50 TO 300]
> 4. Category facets: q=*:*&facet=true&facet.field=cat&rows=0
> 5. Combined: q=electronics&fq=inStock:true&fq=cat:camera&facet=true&facet.field=cat

**Expected advisor behavior:**
- Translate each query to OpenSearch Query DSL

**Query 1 — Keyword search (eDisMax):**
```json
{
  "query": {
    "multi_match": {
      "query": "hard drive",
      "fields": ["name^2", "features^1", "cat^0.5"],
      "type": "best_fields"
    }
  }
}
```
- Note: eDisMax `qf` maps cleanly to multi_match `fields` with boosts

**Query 2 — Stock filter:**
```json
{
  "query": {
    "bool": {
      "filter": [{"term": {"inStock": true}}]
    }
  }
}
```

**Query 3 — Price range:**
```json
{
  "query": {
    "bool": {
      "filter": [{"range": {"price": {"gte": 50, "lte": 300}}}]
    }
  }
}
```

**Query 4 — Category facets:**
```json
{
  "query": {"match_all": {}},
  "aggs": {
    "by_category": {"terms": {"field": "cat.keyword", "size": 20}}
  },
  "size": 0
}
```
- Note: facet.field on a text field needs `.keyword` sub-field. Recommend multi-field mapping for `cat`.

**Query 5 — Combined:**
```json
{
  "query": {
    "bool": {
      "must": [{"match": {"_text_": "electronics"}}],
      "filter": [
        {"term": {"inStock": true}},
        {"term": {"cat.keyword": "camera"}}
      ]
    }
  },
  "aggs": {
    "by_category": {"terms": {"field": "cat.keyword", "size": 20}}
  }
}
```

**Incompatibilities to flag:**
- SCHEMA-004: `cat` field used for both search AND faceting — needs multi-field mapping (text + keyword sub-field)
- QUERY-002: mm (minimum_should_match) not used here, but note for future if they add it

**Facts recorded:**
```json
{"queries_translated": 5}
```

---

## Step 4 — Customization Assessment

**User input:**
> Pretty standard setup. No custom plugins, no streaming expressions.
> We use the default /select handler. Basic auth on Solr, nothing fancy.
> SolrCloud with 1 collection.

**Expected advisor behavior:**
- Record: no custom plugins, no streaming, no CDCR, no DIH, no atomic updates
- Note: BasicAuth → need to decide between IAM+SigV4 and FGAC for OpenSearch
- Flag: no incompatibilities from customizations (this is a clean setup)
- Note: SolrCloud → embedded Raft in OpenSearch (operational model change but no code impact)

**Facts recorded:**
```json
{
  "customizations_assessed": true,
  "custom_plugins": [],
  "auth_method": "basic",
  "operational_patterns": ["solrcloud"],
  "streaming_expressions": false,
  "cdcr": false,
  "atomic_updates": false
}
```

---

## Step 5 — Infrastructure Assessment

**User input:**
> 3 Solr nodes (SolrCloud), 1 collection, 3 shards, RF=2.
> Each node: 4 vCPU, 16GB RAM, 8GB JVM heap.
> Index size about 500MB (just product catalog).
> About 200 QPS peak, minimal indexing (catalog updates a few times per day).
> We want to run on AWS managed OpenSearch.

**Expected advisor behavior:**
- Apply sizing heuristics:
  - Nodes: max(3 * 2, 3) = 6 data nodes (but this is overkill for 500MB)
  - For 500MB index, 200 QPS: 2 data nodes + 3 dedicated masters is plenty
  - Recommend: `r6g.large.search` (2 vCPU, 16GB) — search-heavy workload benefits from memory
  - 3-AZ for production availability
  - Storage: 500MB * 3 = 1.5GB per node (way under minimum; GP3 10GB minimum per node)
- Recommendation: this is a small cluster. Consider OpenSearch Serverless if cost is a concern.

**Incompatibilities to flag:**
- OPS-001: Replica co-location forbidden — but for 500MB this is a non-issue, just noting the principle

**Facts recorded:**
```json
{
  "infrastructure_assessed": true,
  "solr_node_count": 3,
  "collection_count": 1,
  "shard_count": 3,
  "replica_factor": 2,
  "total_index_size_gb": 0.5,
  "qps": 200,
  "target_platform": "aws_managed"
}
```

---

## Step 6 — Client Integration Assessment

**User input:**
> Spring Boot 3.x app using SolrJ. One application, direct HTTP calls for search.
> No other consumers.

**Expected advisor behavior:**
- Record client integration:
  - SolrJ → opensearch-java client (medium effort)
  - Spring Boot: consider spring-data-opensearch for repository pattern
- Note: query builders change significantly (Solr's `SolrQuery` → OpenSearch's `SearchRequest`)
- Note: URL patterns change (`/solr/collection/select` → `/_search`)
- Auth change: BasicAuth → SigV4 (if using IAM) or internal user DB

**Facts recorded:**
```json
{
  "integrations_assessed": true,
  "client_integrations": [
    {"name": "SolrJ", "kind": "library", "notes": "Spring Boot 3.x, direct HTTP", "migration_action": "Replace with opensearch-java. Query builders change significantly."}
  ]
}
```

---

## Step 7 — Report Generation

**User input:**
> Generate the report.

**Expected report sections:**

### Executive Summary
Small, clean migration. Complexity 2/5. 15 fields, 7 dynamic patterns, 5 query patterns, 1 client app. No custom plugins or complex features. Primary risk is relevance difference (BM25 vs TF-IDF).

### Incompatibilities (2 total)
| Category | Feature | Severity | Recommendation |
|----------|---------|----------|----------------|
| Behavioral | TF-IDF → BM25 scoring | High | Establish relevance baseline before migration. Measure top-10 overlap. |
| Behavioral | cat field needs multi-field mapping | Medium | Add .keyword sub-field for faceting |

### Schema Migration
- 15 explicit fields mapped (all straightforward)
- 7 dynamic templates created
- 6 copyField directives → copy_to on _text_
- Analyzer chain converted: text_general with index/query split, synonym expansion at query time

### Query Migration
- 5 query patterns translated to Query DSL
- eDisMax → multi_match (clean mapping)
- fq → bool.filter
- facet.field → terms aggregation
- No breaking query incompatibilities

### Infrastructure
- Current: 3 Solr nodes, 500MB index, 200 QPS
- Recommended: 2× r6g.large.search (3-AZ), or OpenSearch Serverless for cost optimization
- 3 dedicated t3.small.search master nodes

### Client Integration
- SolrJ → opensearch-java: medium effort, ~5 days
- Auth migration: BasicAuth → IAM SigV4

### Milestones
1. Provision OpenSearch cluster + create index with mapping (2 days)
2. Migrate SolrJ client to opensearch-java (5 days)
3. Reindex product catalog (1 day)
4. Validate queries and relevance parity (3 days)
5. Cutover with alias swap (1 day)

### Effort Estimate
- Base effort: 2-4 weeks (small migration)
- 0 breaking incompatibilities
- 1 client integration (5 days)
- Relevance tuning: 3 days (simple schema, limited tuning needed)
- Total: ~2.5 weeks including testing
- Infrastructure cost: ~$200-400/month (2× r6g.large + 3× t3.small masters)

---

## Evaluation Criteria

When scoring the advisor's output for this scenario:

| Criterion | Weight | What to check |
|-----------|--------|---------------|
| Schema accuracy | 25% | All 15 fields mapped correctly, dynamic templates correct, copy_to correct |
| Analyzer conversion | 20% | Index/query analyzer split preserved, synonym filter configured, stop filter correct |
| Query translation | 20% | All 5 queries produce valid DSL, multi-field faceting noted |
| Incompatibility detection | 15% | BM25 flagged, no false positives (no blocking issues in this simple schema) |
| Report completeness | 10% | All 9 sections present with real data |
| Actionability | 10% | Effort estimates reasonable, milestones sequenced correctly, client migration guidance specific |
