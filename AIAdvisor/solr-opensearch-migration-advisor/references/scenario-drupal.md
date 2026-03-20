# Scenario: Drupal (Solr → OpenSearch)
**Scope:** Migrating Drupal sites using the `search_api_solr` module to OpenSearch.
**Audience:** Small business owners (Daphne persona) and Drupal developers.
**Last reviewed:** 2026-03-19 | **Reviewer:** Gemini CLI

---

## Key Judgements (The "Daphne" Persona)

- **Prefer Modules over Code:** For a small business owner, the goal is "zero custom code." Use the `search_api_opensearch` community module rather than writing a custom integration layer.
- **The Schema Barrier:** Drupal's `search_api_solr` module generates highly complex, dynamic `schema.xml` files with hundreds of `tm_*` and `sm_*` fields. Do NOT attempt to manually map these; let the OpenSearch module handle the dynamic mapping generation.
- **Relevance Baseline:** Daphne doesn't have a data science team. Her "Relevance Validation" (Chunk 5) should focus on "Top 5 Queries" and "Side-by-Side Browser Testing" rather than complex nDCG metrics.
- **Cost is a Feature:** Small businesses are sensitive to AWS OpenSearch "Minimum Instance" costs. Recommend **OpenSearch Serverless** or the **t3.medium.search** (if 1-AZ is acceptable for non-critical sites) to keep the "Search Tax" low.

---

## Drupal-Specific Heuristics

### 1. The Module Swap
The primary task isn't "migrating data," it's "swapping the backend."
- **Solr Side:** Drupal uses `search_api_solr`.
- **OpenSearch Side:** Install `search_api_opensearch`.
- **Expert Tip:** You cannot "live-migrate" the index. You must set up the new Search API server in Drupal, point it to OpenSearch, and **re-index from Drupal**. This ensures Drupal's tracking tables stay in sync.

### 2. Dynamic Field Mapping
Drupal prefixes fields to denote type (e.g., `is_` for integer, `ts_` for text-stemmed).
- **In Solr:** These are handled by `<dynamicField>` tags.
- **In OpenSearch:** Use `dynamic_templates`. If using the Drupal OpenSearch module, it should provide these templates out of the box. **Verify the "Stemming" analyzer** matches what Daphne had in Solr (usually Snowball or Porter).

### 3. Views Integration
Daphne likely uses "Drupal Views" to display results.
- **Warning:** Complex Views filters (especially those using Solr-specific "Search API" extras) may break. 
- **Check:** Ensure "Facets" (via the Drupal Facets module) are compatible with the OpenSearch backend version.

---

## Decision Heuristics

| If... | Then... |
|-------|---------|
| Using `search_api_solr` | You **must** re-index from Drupal; do not try to sync at the Lucene level. |
| Budget is <$50/mo | Use a single `t3.small.search` or `t3.medium.search` in a single AZ. |
| Relevance is "Off" | Check the "Language Specific" analyzers. Drupal Solr often defaults to English; ensure OpenSearch isn't using the generic `standard` analyzer. |

## Common Mistakes

- **Trying to reuse the Solr `schema.xml`:** This is a rabbit hole. Drupal's Solr schema is a machine-generated beast. Let the Drupal OpenSearch module define its own mapping.
- **Forgetting "Autocomplete":** Daphne's users likely rely on the search bar's suggestions. Ensure the `search_api_autocomplete` module is reconfigured for the new backend.
- **Ignoring the "Solr Core" vs "OpenSearch Index" naming:** Drupal often hardcodes core names. Ensure the new OpenSearch index name matches the Drupal "Index Machine Name" to avoid confusion.

---

## Daphne's "Quick-Start" Checklist
1. [ ] Install `search_api_opensearch` module.
2. [ ] Provision smallest possible AWS OpenSearch instance (t3.small/medium).
3. [ ] Configure Drupal "Search Server" with OpenSearch Endpoint.
4. [ ] Create a "Search Index" in Drupal pointing to the new server.
5. [ ] **The "Big Re-Index":** Run `drush sapi-i` (re-index) overnight.
6. [ ] Side-by-side test the Top 10 queries.
