# Implementation Tasks: Techproducts Migration

This is the ordered checklist for building the migration. Tasks are grouped by phase with dependencies marked. Estimated effort in person-days.

## Phase 1: Setup (Days 1-3)

Foundation: AWS infrastructure, index creation, mapping validation.

### 1.1 Provision AWS OpenSearch Service
- [ ] Create OpenSearch domain (2.x, 1-AZ, 1 data node, t3.small sufficient for demo)
- [ ] Configure VPC security group (allow 9200 from app security group)
- [ ] Enable Dashboards (included; not required but useful for debugging)
- [ ] Document endpoint, auth credentials
- **Effort:** 0.5 days | **Owner:** DevOps/Infrastructure
- **Good first issue:** No

### 1.2 Create Spring Boot 3.5 + Kotlin 1.9 Project
- [ ] Initialize Gradle project with spring-boot-starter-web
- [ ] Add opensearch-java:2.10.0 dependency
- [ ] Add spring-data-opensearch:1.3.0 dependency
- [ ] Add AWS SDK for SigV4 (opensearch, auth modules)
- [ ] Add TestContainers for testing
- [ ] Verify build succeeds: `./gradlew build`
- **Effort:** 0.5 days | **Owner:** Senior engineer
- **Good first issue:** Yes

### 1.3 Create OpenSearchConfig.kt Spring Bean
- [ ] Implement @Configuration class
- [ ] Profile-based client creation (dev = local HTTP, aws = SigV4)
- [ ] Test client connection to OpenSearch
- [ ] Verify credentials work (IAM role or explicit keys)
- **Effort:** 0.5 days | **Owner:** Platform engineer
- **Good first issue:** Yes

### 1.4 Create Index with Mapping
- [ ] Save mapping JSON from design.md to resources/opensearch-mapping.json
- [ ] Implement IndexManager.createIndex() to apply mapping via API
- [ ] Test: `POST /techproducts` with full mapping
- [ ] Verify index status: `GET /techproducts` returns GREEN
- [ ] Spot-check: `GET /techproducts/_mapping` shows all 15 explicit fields
- **Effort:** 1 day | **Owner:** Search engineer
- **Good first issue:** Yes

### 1.5 Validate Analyzer Configuration
- [ ] Test text_general_index analyzer: "Hard DRIVE" → ["hard", "drive"]
- [ ] Test text_general_query analyzer: "hd" → ["hard", "drive"] (synonym expansion)
- [ ] Test stopword removal: "the quick brown" → ["quick", "brown"]
- [ ] Verify synonym file is included in resources/synonyms.txt
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

---

## Phase 2: Indexing Pipeline (Days 4-6)

Data movement: Solr → transform → OpenSearch.

### 2.1 Create ProductDocument.kt (Kotlin data class)
- [ ] Define @Document(indexName = "techproducts")
- [ ] Map all 15 explicit fields with @Field annotations
- [ ] Implement @Id on id field
- [ ] Handle manu.keyword and cat.keyword multi-fields
- [ ] Add _text_ field with copy_to logic noted in docstring
- [ ] Test: instantiate ProductDocument with sample data
- **Effort:** 0.5 days | **Owner:** Data engineer
- **Good first issue:** Yes

### 2.2 Create SolrExporter.kt
- [ ] Add SolrJ dependency (9.x)
- [ ] Implement export(solrUrl) that queries Solr /select?qt=export
- [ ] Parse JSON response; transform each doc to ProductDocument
- [ ] Handle field mappings (Solr → Kotlin types)
- [ ] Test with local Solr instance (use official demo if available)
- [ ] Verify 7 documents exported correctly
- **Effort:** 1 day | **Owner:** ETL engineer
- **Good first issue:** No

### 2.3 Create MigrationService.kt (Bulk Indexing)
- [ ] Implement bulkIndex(List<ProductDocument>) function
- [ ] Set refresh_interval = -1 before indexing
- [ ] Create BulkRequest, add 7 documents
- [ ] Execute bulk and log failures (if any)
- [ ] Force refresh_interval = 1s after bulk
- [ ] Call OpenSearch refresh API
- **Effort:** 1 day | **Owner:** Platform engineer
- **Good first issue:** Yes

### 2.4 Create ProductRepository.kt
- [ ] Extend Spring Data OpenSearch Repository<ProductDocument, String>
- [ ] Implement findAll()
- [ ] Add custom finder: findByManu(String) → List
- [ ] Add custom finder: findByInStock(Boolean) → List
- [ ] Test: insert sample doc, retrieve by id, verify fields
- **Effort:** 0.5 days | **Owner:** Data engineer
- **Good first issue:** Yes

### 2.5 Implement Full Reindex Workflow
- [ ] Create main entry point: reindexFromSolr(solrUrl: String)
- [ ] Call SolrExporter.export(solrUrl) → List<ProductDocument>
- [ ] Call MigrationService.bulkIndex(docs)
- [ ] Verify count: countResponse.count() == 7
- [ ] Log summary: "Indexed 7 documents in Xs"
- **Effort:** 0.5 days | **Owner:** Platform engineer
- **Good first issue:** No

---

## Phase 3: Query Layer (Days 7-12)

Search functionality: implement each query pattern from requirements.

### 3.1 Create ProductSearchService.kt
- [ ] Implement searchKeyword(query: String) → SearchResults
- [ ] Use multi_match with fields: name^2, features^1, cat^0.5
- [ ] Return top 10 results with scores
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

### 3.2 Implement Filter Queries
- [ ] Implement searchWithFilters(query, inStock?, priceMin?, priceMax?, categories?)
- [ ] Build bool query with must (keyword) + filter (facets)
- [ ] Test: each filter individually, then combined
- [ ] Verify filter reduces result count correctly
- **Effort:** 1 day | **Owner:** Search engineer
- **Good first issue:** Yes

### 3.3 Implement Category Facets
- [ ] Implement searchWithCategoryFacets(query: String)
- [ ] Add terms aggregation on cat.keyword
- [ ] Return top 20 categories with counts
- [ ] Test: facet counts match Solr (exactly, no rounding)
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

### 3.4 Implement Stock Status Facets
- [ ] Implement searchWithStockFacets(query: String)
- [ ] Add terms aggregation on inStock (boolean)
- [ ] Return true/false counts
- [ ] Test with and without filters (counts should update)
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

### 3.5 Implement Price Range Facets
- [ ] Implement searchWithPriceFacets(query: String, buckets: List<Range>)
- [ ] Add range aggregation on price field
- [ ] Support configurable buckets (e.g., 0-100, 100-250, 250-500)
- [ ] Test: counts are accurate and sum to total
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

### 3.6 Implement Geo Search
- [ ] Implement searchNearby(lat: Double, lon: Double, distanceKm: Double)
- [ ] Use geo_distance filter
- [ ] Sort by distance (nearest first)
- [ ] Test: at least query executes without error (may have 0 results)
- **Effort:** 1 day | **Owner:** Search engineer / Geo specialist
- **Good first issue:** No

### 3.7 Implement Combined Filters + Facets
- [ ] Implement searchComplex(query, filters, facets)
- [ ] Combine keyword search + filter context + multiple aggregations
- [ ] Test: facet counts reflect filtered set, not entire index
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

### 3.8 Create SearchController.kt (REST API)
- [ ] Endpoint: GET /api/search?q=...&filters=...&facets=...
- [ ] Endpoint: GET /api/search/geo?lat=...&lon=...&distance=...
- [ ] Return JSON responses matching expected format
- [ ] Log each request with timing
- **Effort:** 1 day | **Owner:** API engineer
- **Good first issue:** Yes (if team doing REST)

---

## Phase 4: Testing (Days 13-15)

Unit, integration, and validation testing.

### 4.1 Unit Tests: ProductSearchService
- [ ] Test searchKeyword returns results for "hard drive"
- [ ] Test searchWithFilters(inStock=true) excludes out-of-stock products
- [ ] Test searchWithFilters(price=[50,300]) returns correct range
- [ ] Mock repository; focus on query logic
- **Effort:** 1 day | **Owner:** QA/Test engineer
- **Good first issue:** Yes

### 4.2 Integration Tests: ProductRepository
- [ ] Use TestContainers to start OpenSearch container
- [ ] Insert 7 test products
- [ ] Test findByManu("Samsung") returns SP2514N
- [ ] Test findByInStock(true) returns 3 products
- [ ] Test edge cases (empty results, malformed geo)
- **Effort:** 1 day | **Owner:** QA/Test engineer
- **Good first issue:** Yes

### 4.3 Integration Tests: Full Migration Flow
- [ ] Start OpenSearch container
- [ ] Create index with mapping
- [ ] Bulk index 7 test documents
- [ ] Execute all 8 query patterns
- [ ] Verify results match expected counts
- [ ] Check performance: all queries < 100ms
- **Effort:** 1 day | **Owner:** QA/Test engineer + Search engineer
- **Good first issue:** No

### 4.4 Spot-Check Queries Against Solr
- [ ] Start local Solr instance with techproducts demo
- [ ] Run representative queries in both systems:
  - "hard drive"
  - "electronics" with inStock=true
  - "camera" with price < 250
  - Facets on cat, inStock, price ranges
- [ ] Compare top-10 result overlap (should be ≥ 80%)
- [ ] Compare facet counts (should match exactly)
- **Effort:** 0.5 days | **Owner:** Search engineer + QA
- **Good first issue:** No

---

## Phase 5: Validation & Documentation (Days 16-17)

Final verification, documentation, handoff.

### 5.1 Create Test Data File
- [ ] Document all 7 sample products in JSON format
- [ ] Include all fields (name, manu, cat, price, inStock, store, etc.)
- [ ] Save to `src/test/resources/test-products.json`
- [ ] Test loading: JSON parses without errors
- **Effort:** 0.5 days | **Owner:** QA/Test engineer
- **Good first issue:** Yes

### 5.2 Create Example Query Collection
- [ ] Document 8 representative queries (from design.md)
- [ ] For each query: Solr version + OpenSearch DSL version + expected results
- [ ] Save to `docs/query-examples.md`
- [ ] Verify all 8 execute against live OpenSearch without error
- **Effort:** 0.5 days | **Owner:** Search engineer
- **Good first issue:** Yes

### 5.3 Run Full Regression Suite
- [ ] Execute all unit tests: `./gradlew test`
- [ ] Execute all integration tests: `./gradlew integrationTest`
- [ ] Verify 0 failures, 0 skipped
- [ ] Check code coverage (target: > 70% for service layer)
- **Effort:** 0.5 days | **Owner:** QA/Test engineer
- **Good first issue:** Yes

### 5.4 Document Migration Procedure
- [ ] Create `docs/migration-runbook.md`:
  - Prerequisites (AWS OpenSearch endpoint, credentials)
  - Step-by-step: provisioning, index creation, reindexing
  - Verification checklist (count, sample queries)
  - Rollback procedure (re-index from scratch)
- **Effort:** 0.5 days | **Owner:** Technical writer
- **Good first issue:** Yes

### 5.5 Create README for Developers
- [ ] How to run locally (Docker + Spring Boot)
- [ ] How to run tests (unit vs. integration)
- [ ] Project structure overview
- [ ] Common troubleshooting (connection errors, auth issues)
- **Effort:** 0.5 days | **Owner:** Technical writer
- **Good first issue:** Yes

### 5.6 Final Validation Against Requirements
- [ ] Verify all 17 requirements pass (FR-1 through FR-17)
- [ ] Check EARS acceptance criteria for each
- [ ] Document any requirements that are deferred (mark as known limitations)
- [ ] Obtain sign-off from product/QA
- **Effort:** 1 day | **Owner:** QA + Search engineer
- **Good first issue:** No

### 5.7 Retrospective + Handoff
- [ ] Document lessons learned (what went smooth, what was hard)
- [ ] Note timing vs. estimate
- [ ] Identify reusable patterns for future migrations
- [ ] Brief operations team on running the application
- **Effort:** 0.5 days | **Owner:** Project manager + team
- **Good first issue:** No

---

## Timeline Summary

| Phase | Tasks | Effort (person-days) | Duration |
|-------|-------|----------------------|----------|
| 1. Setup | 1.1 - 1.5 | 3 | 3 days |
| 2. Indexing | 2.1 - 2.5 | 3.5 | 2-3 days |
| 3. Queries | 3.1 - 3.8 | 5.5 | 3-4 days |
| 4. Testing | 4.1 - 4.4 | 3.5 | 2-3 days |
| 5. Validation | 5.1 - 5.7 | 4 | 1-2 days |
| **TOTAL** | **22 tasks** | **19.5** | **1 sprint (2 weeks)** |

---

## Task Dependencies

```
1.1 Provision AWS ──┐
                    ├─→ 1.4 Create Index ──┐
1.2 Init Project ──┤                       ├─→ 2.2 Export Solr ──┐
                   ├─→ 1.3 Config ────────┤                      ├─→ 2.3 Bulk Load ──┐
1.5 Validate Analyzer ──────────────────────┘                    │                   ├─→ 3.x Query Layer
                                                                  │                   │
2.1 ProductDocument ─────────────────────────────────────────────┤                   │
                                                                  └──→ 2.4 Repository─┘
2.5 Reindex Workflow ← all of phase 2

3.1-3.8 Queries (parallelizable)

4.1-4.3 Tests (parallelizable, depend on 3.x)

5.1-5.7 Documentation & validation (parallelizable, depend on 4.x)
```

---

## Good First Issues (For Onboarding)

If you have new team members, assign these in order:

1. **1.2:** Create Spring Boot project skeleton
2. **1.5:** Test analyzer configuration
3. **2.1:** Create ProductDocument data class
4. **2.4:** Create ProductRepository
5. **3.1:** Implement searchKeyword
6. **3.2:** Implement filter queries
7. **3.3:** Implement category facets
8. **4.1:** Write unit tests for ProductSearchService
9. **4.2:** Write integration tests with TestContainers
10. **5.1:** Create test data file
11. **5.2:** Create example query collection
12. **5.4:** Document migration procedure

These are relatively self-contained and have clear acceptance criteria.

---

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| AWS auth fails | Test SigV4 locally with credentials file before deploying |
| Analyzer behavior differs | Manually test each analyzer step (tokenize, stopwords, synonyms) |
| Mapping type mismatches | Use strict dynamic mapping; catch errors on first bulk indexing |
| Query divergence | Compare Solr and OpenSearch results for each query pattern early (task 4.4) |
| Performance regression | Measure query latency baseline in task 3.1; establish p50/p99 before tuning |

---

**Version:** 1.0
**Date:** 2026-03-17
**Owner:** Search Platform Team
**Review:** Engineering Lead, QA Lead
