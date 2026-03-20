# Requirements: Northstar Enterprise Demo

All requirements use EARS-style wording and focus on the core migration behaviors for the
Northstar enterprise sample.

---

## FR-1: Multi-Type Enterprise Search

**Story:** As a support user, I want one search experience across products, parts, manuals,
bulletins, and cases so I can solve customer issues without switching tools.

**Acceptance Criteria:**

**GIVEN** the Northstar sample index contains all five document types  
**WHEN** I search for "NX-4400 seal kit"  
**THEN** I should receive results from at least the `part` and `product` types  
**AND** exact part or model matches should rank above broad text-only matches

---

## FR-2: Entitlement-Aware Filtering

**Story:** As a dealer user, I want search results filtered to my access level so I do not see
internal-only content.

**Acceptance Criteria:**

**GIVEN** a dealer-context search request  
**WHEN** I search for "maintenance manual"  
**THEN** results with `visibility_level=internal` must be excluded  
**AND** dealer-eligible content must remain visible

**GIVEN** an internal user-context search request  
**WHEN** I execute the same search  
**THEN** internal manuals and support cases may be returned

---

## FR-3: Region-Constrained Search

**Story:** As a regional service user, I want results scoped to my operating region so I do not
see irrelevant or unusable documents.

**Acceptance Criteria:**

**GIVEN** a search with `region=EMEA`  
**WHEN** I query for "E41 overheating"  
**THEN** EMEA bulletin content should be returned  
**AND** non-EMEA-only results should be excluded unless explicitly global

---

## FR-4: Facets For Enterprise Navigation

**Story:** As a parts or support user, I want facets for document type, product line, and region
so I can narrow the result set quickly.

**Acceptance Criteria:**

**GIVEN** a broad query such as "NX-4400"  
**WHEN** facet requests are included  
**THEN** the response must include counts for `doc_type`, `product_line`, and `region`

**GIVEN** active filters on the query  
**WHEN** facets are returned  
**THEN** the facet counts must reflect the filtered result set, not the entire index

---

## FR-5: Freshness Boost For Bulletins

**Story:** As a support user, I want recent service bulletins ranked strongly for issue queries so
I see the latest operational guidance first.

**Acceptance Criteria:**

**GIVEN** a bulletin-oriented query such as "overheating fault E41"  
**WHEN** the search executes  
**THEN** recent bulletin documents should be boosted above older generic content  
**AND** the ranking logic should remain explainable in the target design

---

## FR-6: Part And Model Number Precision

**Story:** As a parts specialist, I want exact part-number and model-number matches to rank first
so I can find the correct item quickly.

**Acceptance Criteria:**

**GIVEN** a query for `SK-2209`  
**WHEN** I search the target index  
**THEN** the matching part record should appear in the top results  
**AND** exact identifier fields should outrank fuzzy text matches

---

## FR-7: Document-Type Filtering

**Story:** As a service user, I want to filter by document type so I can focus on manuals,
bulletins, or cases depending on the task.

**Acceptance Criteria:**

**GIVEN** a query for "startup pressure drop" with `doc_type=case`  
**WHEN** the search runs  
**THEN** only case documents should be returned  
**AND** other content types should be excluded from hits

---

## FR-8: Source-To-Target Field Fidelity

**Story:** As a migration engineer, I want critical Solr fields mapped to correct OpenSearch
types so filters, sorting, and retrieval remain valid.

**Acceptance Criteria:**

**GIVEN** the source schema fields `title`, `summary`, `body`, `part_number`, `product_line`,
`region`, `visibility_level`, `dealer_tier`, `published_at`  
**WHEN** documents are indexed into OpenSearch  
**THEN** textual fields must support search  
**AND** keyword fields must support exact filtering and aggregation  
**AND** date fields must support freshness-based ranking

---

## FR-9: CopyField Replacement

**Story:** As a migration engineer, I want Solr catch-all text behavior reproduced in a controlled
way so broad enterprise queries continue to work.

**Acceptance Criteria:**

**GIVEN** source fields such as `title`, `summary`, and `body`  
**WHEN** documents are indexed  
**THEN** their content should contribute to a catch-all target search field  
**AND** broad keyword queries should search across those combined fields

---

## FR-10: Bulk Reindex Workflow

**Story:** As a migration engineer, I want to bulk-load the Northstar sample corpus so I can run
repeatable demo migrations.

**Acceptance Criteria:**

**GIVEN** the Northstar sample documents  
**WHEN** I run the reindex workflow  
**THEN** all documents should be indexed successfully  
**AND** the final document count should equal the source sample count  
**AND** the workflow should be repeatable without manual cleanup steps

---

## FR-11: Query Translation Transparency

**Story:** As a search engineer, I want each major Solr query pattern translated into explicit
OpenSearch DSL so the migration behavior is reviewable.

**Acceptance Criteria:**

**GIVEN** the representative Solr query set in the sample source material  
**WHEN** the target design is produced  
**THEN** each major query type must have a corresponding OpenSearch strategy  
**AND** the design should identify any areas that require approximation rather than 1:1 parity

---

## FR-12: Demo Validation Baseline

**Story:** As a demo team member, I want a small, defensible validation plan so I can show the
migration is behaving correctly.

**Acceptance Criteria:**

**GIVEN** a defined set of sample enterprise queries  
**WHEN** the demo validation runs  
**THEN** result ranking, facet correctness, and entitlement filtering must be checked  
**AND** the validation plan must be simple enough to run during a demo session
