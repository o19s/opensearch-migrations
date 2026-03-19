# Requirements: minti9 Techproducts Migration

The goal of this migration is to move the canonical Solr 8 `techproducts` collection to OpenSearch 2.12 with full functional parity.

## FR-1: Keyword Search Across Multiple Fields

**Acceptance Criteria:**
**GIVEN** the techproducts index is populated with 4 sample products
**WHEN** I search for "hard drive" against `name` and `features`
**THEN** I should see results including `6H500F0` and `SP2514N` ranked by relevance.

## FR-2: Field Type Preservation

**Acceptance Criteria:**
**GIVEN** the Solr schema fields: `cat`, `inStock`, `price`, `manufacturedate_dt`, `store`
**WHEN** documents are migrated
**THEN** OpenSearch should correctly type them as `text`/`keyword`, `boolean`, `float`, `date`, and `geo_point` respectively.

## FR-3: Analyzer Parity (Synonyms and Stopwords)

**Acceptance Criteria:**
**GIVEN** a query for "hd"
**WHEN** I execute the search in OpenSearch
**THEN** results should include "hard drive" matches (synonym expansion).

## FR-4: Cluster Operational Availability

**Acceptance Criteria:**
**GIVEN** a disk usage of 91% on `minti9`
**WHEN** creating the index
**THEN** the system must not block index creation (requires manual settings override).

---
**Version:** 1.0
**Date:** 2026-03-18
