# Migration Sample Catalog
**Scope:** A registry of available sample datasets and configurations for demo migrations.
**Usage:** When a user asks for a demo, use the paths below to load the source files.

---

## 1. Drupal 8/9/10 (Search API Solr)
**Location:** `sources/samples/drupal-solr8/`
**Files:**
- `conf/schema.xml`: The "Gold Standard" dynamic schema for Drupal sites.
- `conf/solrconfig.xml`: Standard request handler config.
- `sample-docs.json`: Representative JSON payload from Drupal's indexing process.

**Key Features:**
- **Dynamic Fields:** Heavily relies on `tm_X3_en_*` and `ss_*` patterns.
- **Multilingual:** Includes language-specific field prefixes (e.g., `es_`, `en_`).
- **Entity IDs:** Uses Drupal's `entity:node/1:en` ID format.

**Demo Scenario:**
"Migrating a small business Drupal Commerce site (Daphne's Widgets) to OpenSearch."

---

## 2. TechProducts (Classic Solr)
**Location:** `sources/samples/techproducts/` (Planned)
**Description:** The classic Solr tutorial dataset (electronics, hard drives).
**Status:** Placeholder.

---

## 3. Wikipedia (Text Heavy)
**Location:** `sources/samples/wikipedia/` (Planned)
**Description:** A subset of Wikipedia articles for relevance tuning demos.
**Status:** Placeholder.

---

## 4. Northstar Enterprise Search
**Location:** `sources/samples/northstar-enterprise-search/`
**Files:**
- `project-description.md`: Enterprise migration brief, scope, and success criteria.
- `client-team.md`: Sample Fortune 500 migration team with business, platform, and relevance roles.
- `source-system-overview.md`: Current Solr topology, access-control model, and pain points.
- `sample-queries.md`: Representative Solr query patterns for support and parts search.
- `conf/schema.xml`: Primary collection schema for the `atlas_search` collection.
- `conf/solrconfig.xml`: Request handlers, cache settings, and commit behavior.
- `sample-docs.json`: Representative source documents across product, part, manual, bulletin, and case types.

**Key Features:**
- **Enterprise search mix:** Product, parts, manuals, bulletins, and support cases in one search experience.
- **Query complexity:** eDisMax, facets, filters, field boosts, and freshness boosting.
- **Access control:** Query-time filtering by visibility, dealer tier, region, and business unit.
- **Managed-cloud target:** Explicitly framed as a migration to Amazon OpenSearch Service.

**Demo Scenario:**
"Migrating Northstar Industrial Systems' Atlas Knowledge Hub from in-house Solr to Amazon OpenSearch Service while preserving support and parts-search behavior for internal and dealer users."
