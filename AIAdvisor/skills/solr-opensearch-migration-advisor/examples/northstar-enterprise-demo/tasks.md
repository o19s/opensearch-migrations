# Implementation Tasks: Northstar Enterprise Demo

This is the phased task list for standing up a test migration and demo implementation for the
Northstar enterprise sample.

## Phase 1: Demo Foundation (Days 1-3)

### 1.1 Create Demo Spec Workspace
- [ ] Create the project skeleton described in `steering/structure.md`
- [ ] Copy sample source data into app resources
- [ ] Document environment variables for AWS and local execution
- **Effort:** 0.5 days | **Owner:** Senior engineer

### 1.2 Provision Demo OpenSearch Domain
- [ ] Create Amazon OpenSearch Service demo domain
- [ ] Configure VPC networking and access path for the demo app
- [ ] Verify Dashboards access for developers
- **Effort:** 1 day | **Owner:** AWS platform architect

### 1.3 Configure OpenSearch Client
- [ ] Add OpenSearch Java client and AWS auth dependencies
- [ ] Implement SigV4-based client configuration
- [ ] Verify connectivity from the app to the demo domain
- **Effort:** 0.5 days | **Owner:** Platform engineer

### 1.4 Create Target Index And Aliases
- [ ] Save target mapping JSON from `design.md`
- [ ] Create `atlas-search-v1`
- [ ] Attach `atlas-search-read` and `atlas-search-write` aliases
- [ ] Verify mappings and aliases via API
- **Effort:** 1 day | **Owner:** Search engineer

## Phase 2: Data Model And Indexing (Days 4-6)

### 2.1 Build Atlas Document Model
- [ ] Create `AtlasDocument` class for the shared target document shape
- [ ] Model fields for content type, entitlements, identifiers, and text
- [ ] Add tests for sample-doc parsing
- **Effort:** 0.5 days | **Owner:** Application engineer

### 2.2 Implement Source Loader
- [ ] Load Northstar sample documents from JSON
- [ ] Normalize into the target application model
- [ ] Log source count and per-type counts
- **Effort:** 0.5 days | **Owner:** Data integration engineer

### 2.3 Implement Bulk Reindex Service
- [ ] Disable refresh during bulk load
- [ ] Bulk index all sample docs through the write alias
- [ ] Restore refresh and trigger index refresh
- [ ] Verify target count matches source count
- **Effort:** 1 day | **Owner:** Platform engineer

### 2.4 Create Repeatable Reset Workflow
- [ ] Add admin action or CLI command to recreate the demo index
- [ ] Ensure demo re-runs are deterministic
- [ ] Document the reset procedure
- **Effort:** 0.5 days | **Owner:** Senior engineer

## Phase 3: Query Layer (Days 7-11)

### 3.1 Implement Enterprise Keyword Search
- [ ] Build `multi_match` query for title, summary, body, identifiers, and keywords
- [ ] Add query tests for part-number and model-number precision
- **Effort:** 1 day | **Owner:** Search engineer

### 3.2 Implement Filter Layer
- [ ] Add `doc_type`, `region`, `visibility_level`, `dealer_tier`, and `business_unit` filters
- [ ] Verify filters run in `bool.filter`
- [ ] Test internal vs dealer scenarios
- **Effort:** 1 day | **Owner:** Search engineer

### 3.3 Implement Aggregations
- [ ] Add aggregations for `doc_type`, `product_line`, and `region`
- [ ] Verify filtered facet counts
- **Effort:** 0.5 days | **Owner:** Search engineer

### 3.4 Implement Bulletin Freshness Boost
- [ ] Add `function_score` with recency decay on `published_at`
- [ ] Apply content-type-aware boosting for bulletin-oriented searches
- [ ] Validate with sample bulletin queries
- **Effort:** 0.5 days | **Owner:** Search engineer

### 3.5 Create Search API
- [ ] Expose a demo search endpoint
- [ ] Return hits, facets, and applied filters
- [ ] Include request timing in logs for demo use
- **Effort:** 1 day | **Owner:** API engineer

## Phase 4: Demo Validation (Days 12-14)

### 4.1 Build Query Validation Set
- [ ] Encode the representative sample queries into test fixtures
- [ ] Mark expected high-priority results per query
- **Effort:** 0.5 days | **Owner:** Relevance lead

### 4.2 Validate Entitlement Logic
- [ ] Run dealer and internal access scenarios
- [ ] Verify internal-only docs never leak to dealer flows
- **Effort:** 0.5 days | **Owner:** Security lead

### 4.3 Validate Facets And Counts
- [ ] Check facet counts for broad and filtered queries
- [ ] Verify doc-type, product-line, and region counts are stable
- **Effort:** 0.5 days | **Owner:** QA engineer

### 4.4 Validate Ranking
- [ ] Review top results for part lookup, bulletin freshness, and manual retrieval
- [ ] Capture any tuning gaps for the next pass
- **Effort:** 1 day | **Owner:** Relevance lead plus search engineer

## Phase 5: Demo Packaging (Days 15-16)

### 5.1 Prepare Demo Runbook
- [ ] Document setup, reset, indexing, and validation steps
- [ ] Add a short demo script for the main search flows
- **Effort:** 0.5 days | **Owner:** Technical lead

### 5.2 Prepare Demo Scenarios
- [ ] Create a support-agent scenario
- [ ] Create a dealer parts-lookup scenario
- [ ] Create a service-bulletin scenario
- **Effort:** 0.5 days | **Owner:** Product manager

### 5.3 Capture Follow-On Work
- [ ] List production-hardening gaps
- [ ] List relevance and access-control questions for deeper migration planning
- **Effort:** 0.5 days | **Owner:** Search engineering lead
