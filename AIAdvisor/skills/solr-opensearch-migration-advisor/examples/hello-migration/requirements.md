# Requirements: `hello` Migration

[ASSUMED: EARS-format user stories reflecting the scope in product.md]

## Functional Requirements

### FR-1: Keyword Search (Primary Query Path)

**As a** search client calling the API,
**I want** to submit a text query that searches across `title` and `body` fields with title-weighted relevance,
**so that** the most relevant documents surface at the top of results.

**Acceptance Criteria:**

```
GIVEN a non-empty query string
WHEN the query is submitted to POST /search
THEN OpenSearch returns documents matching the query
AND title matches are boosted over body matches [ASSUMED: qf=title^3 body^1]
AND phrase matches in title are additionally boosted [ASSUMED: pf=title^5 slop=2]
AND minimum_should_match of 75% is applied for multi-term queries [ASSUMED: mm=75%]
```

**Notes:** If the actual `qf` field weights differ from the assumed `title^3 body^1`,
the query template in `design.md` must be updated before this requirement is testable.

---

### FR-2: Category Faceting

**As a** search UI or API consumer,
**I want** to receive a breakdown of result counts by `category`,
**so that** users can filter and narrow their search.

**Acceptance Criteria:**

```
GIVEN any search request (query or browse)
WHEN the request includes facets=true
THEN the response includes a `by_category` aggregation
AND each bucket contains a category name and document count
AND buckets are sorted by document count descending
AND the top 20 categories are returned [ASSUMED: facet.limit=20]
```

---

### FR-3: Category Filter

**As a** search client,
**I want** to restrict results to a single category via a filter parameter,
**so that** browse-by-category queries work correctly.

**Acceptance Criteria:**

```
GIVEN a search request with category=<value>
WHEN the query is executed
THEN only documents with category exactly matching <value> are returned
AND the filter is applied in the non-scoring context (OpenSearch bool.filter)
AND facet counts still reflect the filtered view
```

---

### FR-4: Date Range Filtering

**As a** search client,
**I want** to filter results by `publishedDate` range,
**so that** time-bounded queries return only documents within the specified window.

**Acceptance Criteria:**

```
GIVEN a search request with dateFrom=<ISO8601> and/or dateTo=<ISO8601>
WHEN the query is executed
THEN results are restricted to documents whose publishedDate falls within [dateFrom, dateTo]
AND open-ended ranges (only from or only to) are supported
AND invalid date formats return HTTP 400 with a descriptive error
```

---

### FR-5: Pagination

**As a** search client,
**I want** to paginate through results using `from` and `size` parameters,
**so that** large result sets can be retrieved in chunks.

**Acceptance Criteria:**

```
GIVEN from=0, size=20 (defaults)
THEN the first 20 results are returned

GIVEN from=20, size=20
THEN results 21-40 are returned

GIVEN from + size > 10000
THEN the API returns HTTP 400 with guidance to use search_after pagination
```

**Note (FR-5a):** Deep pagination beyond 10,000 documents requires `search_after`.
[ASSUMED: current usage does not exceed 10K offset; verify with analytics before cutover]

---

### FR-6: Schema Fidelity

**As a** migration engineer,
**I want** every field from `schema.xml` to have a semantically equivalent mapping in OpenSearch,
**so that** no field behavior is lost in migration.

**Acceptance Criteria:**

```
GIVEN the Solr schema.xml with N explicit field definitions
WHEN the OpenSearch index is created using hello-mapping.json
THEN the OpenSearch _mapping API returns N equivalent properties
AND each field has the correct type (keyword, text, date, integer, float)
AND copyField destinations are implemented as copy_to
AND dynamicField patterns are implemented as dynamic_templates
AND stored=false fields are mapped with "store": false [ASSUMED: no stored=false fields; verify]
```

---

### FR-7: Full-Text Relevance Parity

**As a** product owner,
**I want** the top-5 search results to match Solr's top-5 results for our most common queries,
**so that** users experience no degradation after migration.

**Acceptance Criteria:**

```
GIVEN a judgment set of 20 representative queries [ASSUMED: judgment set will be built in Phase 2]
WHEN both Solr and OpenSearch are queried with identical query strings
THEN ≥ 90% of queries have identical top-5 result sets [ASSUMED: parity threshold]
AND for queries that differ, the differences are documented and accepted by product
```

**Note:** BM25 (OpenSearch) vs TF-IDF (Solr) will produce differences. This requirement
defines the acceptable threshold. [ASSUMED: 90% — adjust with stakeholders]

---

### FR-8: Bulk Indexing

**As a** migration engineer,
**I want** to reindex all ~100K documents from Solr into OpenSearch in a single migration job,
**so that** the OpenSearch index is populated before dual-write begins.

**Acceptance Criteria:**

```
GIVEN a running Solr instance with the hello collection
WHEN MigrationReindexService.reindexAll() is called
THEN all documents are indexed to OpenSearch using the bulk API
AND documents are processed in batches of 500 [ASSUMED]
AND indexing completes without errors
AND a completion log reports total documents indexed and elapsed time
AND refresh_interval is set to -1 during bulk load and restored afterward
```

---

### FR-9: Dual-Write Mode

**As a** platform team,
**I want** all new indexing operations to write to both Solr and OpenSearch simultaneously,
**so that** the OpenSearch index stays current while Solr remains the production read path.

**Acceptance Criteria:**

```
GIVEN migration.dual-write.enabled=true in application config
WHEN a document is indexed via the application
THEN the document is written to OpenSearch first, then Solr
AND a failure in OpenSearch write causes a 500 error (fast fail)
AND a failure in Solr write is logged but does not cause a 500 (Solr is retiring)
AND dual-write can be disabled via config without code change
```

---

### FR-10: Traffic Cutover

**As a** platform team,
**I want** to gradually shift read traffic from Solr to OpenSearch using a feature flag,
**so that** I can validate OpenSearch quality at increasing traffic percentages before full cutover.

**Acceptance Criteria:**

```
GIVEN migration.read-target=opensearch|solr|split:<pct> in config
WHEN split:<pct> is set (e.g. split:25)
THEN 25% of requests are served by OpenSearch and 75% by Solr
AND response shapes are identical regardless of which backend served the request
AND the active backend is logged per request for comparison analysis
```

[ASSUMED: simple percentage split; production implementations may use a feature flag service]

---

### FR-11: OpenSearch Cluster Health Monitoring

**As a** DevOps engineer,
**I want** cluster health and key metrics exposed via a `/health` endpoint,
**so that** alerts can fire before users are impacted.

**Acceptance Criteria:**

```
GIVEN the application is running
WHEN GET /actuator/health is called
THEN OpenSearch cluster status (green/yellow/red) is reported
AND the response indicates degraded if status is yellow, down if red

GIVEN cluster disk usage exceeds 85% on any node
THEN an alert fires before the 90% hard watermark blocks index operations
```

---

## Non-Functional Requirements

### NFR-1: Search Latency
- P50 ≤ 50ms, P99 ≤ 200ms for queries returning ≤ 20 results [ASSUMED: based on typical Solr performance]
- Measured at the OpenSearch client layer (excludes application overhead)

### NFR-2: Index Throughput
- Bulk reindex completes at ≥ 500 docs/sec [ASSUMED]
- Dual-write overhead ≤ 20% additional latency vs single-write [ASSUMED]

### NFR-3: Availability
- No downtime during migration (dual-write + gradual cutover ensures this)
- OpenSearch cluster target: 99.9% uptime (AWS SLA for 2-node 2-AZ provisioned)

### NFR-4: Security
- All traffic to OpenSearch uses SigV4 signing
- OpenSearch endpoint is VPC-internal; no public access
- IAM role least-privilege: `es:ESHttpGet`, `es:ESHttpPost`, `es:ESHttpPut` only

## Acceptance Criteria Summary

| ID | Requirement | Gate |
|----|-------------|------|
| FR-1 | Keyword search with field weighting | Phase 3 (shadow traffic) |
| FR-2 | Category facets | Phase 2 (offline validation) |
| FR-3 | Category filter | Phase 2 |
| FR-4 | Date range filter | Phase 2 |
| FR-5 | Pagination (+ deep pagination guard) | Phase 2 |
| FR-6 | Schema fidelity (100% field coverage) | Phase 2 |
| FR-7 | Relevance parity ≥ 90% of top-5 | Phase 3 go/no-go gate |
| FR-8 | Bulk reindex | Phase 3 (before dual-write) |
| FR-9 | Dual-write mode | Phase 3 |
| FR-10 | Traffic cutover flag | Phase 4 |
| FR-11 | Health monitoring | Phase 1 (infra setup) |
