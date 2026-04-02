# Requirements: Techproducts Migration

All requirements are written in **EARS format** (Easy Approach to Requirements Syntax). Each has a user story and GIVEN/WHEN/THEN acceptance criteria.

---

## FR-1: Keyword Search Across Multiple Fields

**Story:** As a customer, I want to search for products by typing keywords so I can find relevant items quickly.

**Acceptance Criteria:**

**GIVEN** the techproducts index is populated with 7 sample products
**WHEN** I search for "hard drive"
**THEN** I should see at least 2 results (SP2514N and 6H500F0) in the top 5 ranked by relevance

**GIVEN** a search query "ipod"
**WHEN** I execute a multi-field search against (name^2, features^1, cat^0.5)
**THEN** results should include products with "iPod" in name (IW-02, MA147LL/A) ranked above category-only matches

**GIVEN** the query "portable music"
**WHEN** I search
**THEN** the query should execute in < 100ms and return at least one result (iPod products)

---

## FR-2: Filter Search by Stock Status

**Story:** As a customer, I want to filter results to show only products in stock so I don't purchase unavailable items.

**Acceptance Criteria:**

**GIVEN** a keyword search for "electronics" with filter inStock=true
**WHEN** I execute the query
**THEN** results should exclude 6H500F0, IW-02, F8V7067-APL-KIT, 0579B002 (all inStock=false)
**AND** results should include SP2514N, MA147LL/A, 9885A004 (all inStock=true)

**GIVEN** an inStock filter applied to a search
**WHEN** the result set is reduced
**THEN** facet counts should be recalculated to reflect only in-stock products

---

## FR-3: Filter Search by Price Range

**Story:** As a customer, I want to filter by price range so I can find products within my budget.

**Acceptance Criteria:**

**GIVEN** a search with price filter (minimum=50, maximum=300)
**WHEN** I execute the query
**THEN** results should include SP2514N (92.0), F8V7067-APL-KIT (19.95)
**AND** results should exclude IW-02 (399.0), MA147LL/A (399.0), 9885A004 (479.95)

**GIVEN** a price range filter combined with keyword search
**WHEN** I search for "camera" with price < 300
**THEN** results should be empty (cheapest camera is 210.0, but it's marked inStock=false; next is 479.95)

---

## FR-4: Faceted Navigation by Category

**Story:** As a customer, I want to see category facets so I can narrow search results by product type.

**Acceptance Criteria:**

**GIVEN** a search for "electronics" (or any broad query)
**WHEN** I request facets on the `cat` field
**THEN** I should see facet counts:
  - electronics: 7 (all products)
  - hard drive: 2 (SP2514N, 6H500F0)
  - music: 2 (IW-02, MA147LL/A)
  - camera: 2 (0579B002, 9885A004)
  - connector: 1 (F8V7067-APL-KIT)

**GIVEN** facet counts for category
**WHEN** the query executes
**THEN** facet counts must match source Solr exactly (no rounding errors)

---

## FR-5: Faceted Navigation by Stock Status

**Story:** As a customer, I want to see how many products are in stock vs. out of stock.

**Acceptance Criteria:**

**GIVEN** any product search
**WHEN** I request facets on the `inStock` boolean field
**THEN** I should see:
  - true: 3 (SP2514N, MA147LL/A, 9885A004)
  - false: 4 (6H500F0, IW-02, F8V7067-APL-KIT, 0579B002)

**GIVEN** facet counts for inStock
**WHEN** a filter is applied (e.g., cat=camera)
**THEN** facet counts should update to reflect filtered set:
  - true: 1 (9885A004)
  - false: 1 (0579B002)

---

## FR-6: Price Range Facets

**Story:** As a customer, I want to see products grouped into price buckets so I can browse by affordability.

**Acceptance Criteria:**

**GIVEN** a search with price range facets (buckets: $0-$100, $100-$250, $250-$500)
**WHEN** I request facets
**THEN** I should see:
  - 0-100: 2 (SP2514N 92.0, F8V7067-APL-KIT 19.95)
  - 100-250: 1 (0579B002 210.0)
  - 250-500: 2 (IW-02 399.0, MA147LL/A 399.0)
  - 500+: 1 (6H500F0 350.0... wait, recalc) → Actually: 500+: 1 (9885A004 479.95)

**GIVEN** a price range facet
**WHEN** results span multiple buckets
**THEN** counts must be accurate and sum to total documents

---

## FR-7: Geo Search by Location and Distance

**Story:** As a customer, I want to find products near me so I can check store availability.

**Acceptance Criteria:**

**GIVEN** a geo search centered at latitude=37.77, longitude=-122.41 (San Francisco) with radius=10km
**WHEN** I execute the query
**THEN** I should return products where the `store` field (geo point) is within the distance
**AND** the query must not error (even if no products match the exact distance requirement, the query structure must be valid)

**GIVEN** a geo search with a valid geo point and distance
**WHEN** I execute the query
**THEN** results should be sorted by distance (nearest first)

---

## FR-8: Combined Filters and Facets

**Story:** As a customer, I want to search, filter, and navigate facets simultaneously so I can refine results quickly.

**Acceptance Criteria:**

**GIVEN** a search for "electronics" with:
  - Filter: inStock=true
  - Filter: cat=camera
  - Facet: by inStock (boolean)
  - Facet: by category
**WHEN** I execute the query
**THEN** results should be: [9885A004] (only camera in stock)
**AND** inStock facet should show: true=1, false=0 (only visible in filtered set)
**AND** category facet should show: camera=1, others=0 (only visible in filtered set)

---

## FR-9: Bulk Document Indexing

**Story:** As a developer, I want to bulk-index documents from Solr so I can load the entire collection efficiently.

**Acceptance Criteria:**

**GIVEN** the 7 sample product documents exported from Solr
**WHEN** I execute a bulk index operation
**THEN** all 7 documents should be indexed successfully
**AND** document count should be exactly 7
**AND** index time should be < 5 seconds for 7 documents

**GIVEN** a bulk index operation
**WHEN** documents have duplicate IDs
**THEN** later documents should overwrite earlier ones (idempotent indexing)

---

## FR-10: Single Document Index and Retrieval

**Story:** As a developer, I want to index and retrieve individual documents so I can verify schema correctness.

**Acceptance Criteria:**

**GIVEN** a product document with all fields populated:
  - id: SP2514N
  - name: Samsung SpinPoint hard drive
  - manu: Samsung
  - cat: [electronics, hard drive]
  - price: 92.0
  - inStock: true
  - store: "37.7749, -122.4194"
**WHEN** I index this document
**THEN** the document should be retrievable via GET /index/_doc/SP2514N
**AND** all fields should be returned as indexed

**GIVEN** a document retrieval request
**WHEN** the document doesn't exist
**THEN** the request should return 404 (not found)

---

## FR-11: Field Type Preservation

**Story:** As a developer, I want all Solr field types to map correctly so data integrity is maintained.

**Acceptance Criteria:**

**GIVEN** the following Solr field types:
  - String fields (id, manu) → OpenSearch keyword
  - Text fields (name, features) → OpenSearch text
  - Float fields (weight, price) → OpenSearch float
  - Int fields (popularity) → OpenSearch integer
  - Boolean fields (inStock) → OpenSearch boolean
  - Date fields (manufacturedate_dt) → OpenSearch date
  - Geo fields (store) → OpenSearch geo_point
**WHEN** documents are indexed
**THEN** query results should preserve types:
  - Keyword searches on text fields must work (lowercased, tokenized)
  - Range queries on numeric fields must work (price: [50 TO 300])
  - Boolean filters must work (inStock: true)
  - Date queries must parse dates correctly
  - Geo queries must parse lat/lon correctly

---

## FR-12: CopyField Behavior (Catchall and Exact Match)

**Story:** As a developer, I want copyField behavior replicated so derived fields work correctly.

**Acceptance Criteria:**

**GIVEN** the Solr pattern:
  - copyField source=name dest=_text_
  - copyField source=features dest=_text_
  - copyField source=manu dest=_text_
  - copyField source=cat dest=_text_
  - copyField source=manu dest=manu_exact (string, not analyzed)
**WHEN** documents are indexed
**THEN** the _text_ field should contain concatenated, analyzed content from name, features, manu, cat
**AND** searches on _text_ should find products by searching any source field
**AND** manu_exact should be exact-match keyword (not tokenized)

---

## FR-13: Dynamic Field Pattern Handling

**Story:** As a developer, I want dynamic field patterns (*_s, *_i, *_f, etc.) to be handled so test documents can use any suffix.

**Acceptance Criteria:**

**GIVEN** Solr dynamic field patterns:
  - *_s → string (keyword in OpenSearch)
  - *_i → int (integer in OpenSearch)
  - *_f → float (float in OpenSearch)
  - *_l → long (long in OpenSearch)
  - *_b → boolean (boolean in OpenSearch)
  - *_t → text (text in OpenSearch)
  - *_dt → date (date in OpenSearch)
**WHEN** a test document includes a field matching a dynamic pattern (e.g., "custom_color_s")
**THEN** the field should be automatically typed according to the suffix
**AND** queries using that field should respect the assigned type

---

## FR-14: Analyzer Configuration (Text Analysis)

**Story:** As a developer, I want text analyzers to match Solr behavior so search relevance is preserved.

**Acceptance Criteria:**

**GIVEN** the Solr `text_general` analyzer:
  - Index: StandardTokenizer → StopFilter → LowerCaseFilter
  - Query: StandardTokenizer → StopFilter → SynonymGraphFilter → LowerCaseFilter
**WHEN** OpenSearch applies a custom analyzer with equivalent pipeline
**THEN** keyword search should work: "Hard DRIVE" should match "hard drive" (lowercased)
**AND** stopwords should be removed: "the quick brown fox" → "quick brown fox"
**AND** synonyms should expand: "hd" → "hard drive" if defined in synonym file

---

## FR-15: No Query Timeouts or Errors

**Story:** As a system, I want all queries to execute successfully without timing out so the service is reliable.

**Acceptance Criteria:**

**GIVEN** any query (keyword, filter, facet, geo)
**WHEN** I execute the query
**THEN** the request should complete in < 100ms
**AND** the response should be HTTP 200 (not 500, not timeout)
**AND** error logs should have zero "timeout" or "exception" entries

---

## FR-16: Reindex Without Downtime

**Story:** As a system operator, I want to reindex the collection without stopping reads so the service remains available.

**Acceptance Criteria:**

**GIVEN** a new index mapping or schema change
**WHEN** I create a new index (e.g., techproducts_v2)
**AND** bulk-load documents to the new index
**THEN** queries should continue against the old index (techproducts_v1)
**AND** after reindex completes, I can atomically switch the alias `techproducts` to point to `techproducts_v2`

**GIVEN** an alias-based reindex strategy
**WHEN** the cutover occurs
**THEN** there should be zero query downtime
**AND** document count should match before and after (7 documents exactly)

---

## FR-17: Search Parity with Solr

**Story:** As a QA team, I want search results to match between Solr and OpenSearch so the migration is validated.

**Acceptance Criteria:**

**GIVEN** a set of representative queries (keyword, filtered, faceted):
  - "hard drive"
  - "hard drive" with inStock=true
  - "camera" with price < 250
  - facets on cat and inStock
  - geo search near San Francisco
**WHEN** I execute each query against both Solr and OpenSearch
**THEN** top-10 result overlap should be ≥ 80%
**AND** facet counts should match exactly (within rounding)
**AND** query response time should be within ±15% between systems

---

## Acceptance Criteria Summary

| FR # | Title | Status |
|------|-------|--------|
| FR-1 | Keyword Search | ✓ Must pass |
| FR-2 | Filter by Stock | ✓ Must pass |
| FR-3 | Filter by Price Range | ✓ Must pass |
| FR-4 | Facets by Category | ✓ Must pass |
| FR-5 | Facets by Stock Status | ✓ Must pass |
| FR-6 | Price Range Facets | ✓ Must pass |
| FR-7 | Geo Search | ✓ Must pass |
| FR-8 | Combined Filters+Facets | ✓ Must pass |
| FR-9 | Bulk Indexing | ✓ Must pass |
| FR-10 | Single Document Indexing | ✓ Must pass |
| FR-11 | Field Type Preservation | ✓ Must pass |
| FR-12 | CopyField Behavior | ✓ Must pass |
| FR-13 | Dynamic Fields | ✓ Must pass |
| FR-14 | Analyzer Configuration | ✓ Must pass |
| FR-15 | No Timeouts/Errors | ✓ Must pass |
| FR-16 | Reindex Without Downtime | ✓ Nice to have (demo) |
| FR-17 | Search Parity | ✓ Must pass |

---

**Version:** 1.0
**Date:** 2026-03-17
**Owner:** Product & QA Teams
