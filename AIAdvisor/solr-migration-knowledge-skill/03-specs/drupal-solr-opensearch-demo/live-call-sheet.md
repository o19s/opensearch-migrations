# Live Call Sheet

**Use case:** 1-page guide for the first client call  
**Goal:** Get enough signal to decide whether to stay in discovery, move to PoC, or start strategic planning

---

## Must-Ask Questions

### Platform shape

1. Is this definitely SolrCloud?
2. What does the `1 TB` number actually represent?
3. How many collections matter for search migration?
4. Are any systems besides Drupal querying Solr directly?

### Indexing ownership

5. Does Drupal Search API own indexing, or do external pipelines feed Solr?
6. Can the search index be rebuilt fully from source systems?
7. Are attachments or enrichments involved in indexing?

### Business-critical behavior

8. What are the top 5-10 search behaviors or query types that must survive migration?
9. Are facets, autocomplete, multilingual search, or permission filtering critical?
10. Are there any custom boosts, synonyms, or "quirky but important" ranking behaviors?

### Risk and readiness

11. Are there custom Solr plugins, request handlers, or analyzers?
12. Who owns relevance today?
13. Who owns content access?
14. Who owns production operations and cutover sign-off?

---

## Red Flags

- nobody can explain the `1 TB` number
- nobody knows whether this is SolrCloud
- Solr cannot be rebuilt from source systems
- relevance is owned by nobody
- content ownership is unclear
- direct Solr consumers exist outside Drupal
- custom Solr plugins are present
- access control is handled by post-filtering in the app

---

## Minimum Output From Session 1

- confirmed or unconfirmed SolrCloud status
- clarified meaning of `1 TB`
- initial view of Drupal-owned vs external indexing
- top critical search behaviors listed
- top 3-5 risks named
- named owners for sponsor, product, content, relevance, and ops
- artifact follow-up list with owners

---

## Session Recommendation Codes

- `D1` Discovery only, major unknowns remain
- `D2` Discovery plus artifact review, not ready for planning
- `P1` Ready for strategic planning only
- `P2` Ready for PoC / proof-first migration work

---

## Suggested Closing Language

> Based on what we heard today, we should treat this as a structured assessment first. Before recommending an implementation path, we need to validate the current Solr topology, confirm whether Drupal fully owns indexing, clarify the real meaning of the reported 1 TB footprint, and review the current relevance and access-control model.

