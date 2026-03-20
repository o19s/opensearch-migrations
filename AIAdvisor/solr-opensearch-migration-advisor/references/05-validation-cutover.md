# Validation and Cutover: Relevance Methodology

**Scope:** Quepid/RRE relevance testing, gold query sets, cutover safety, traffic shadowing.
**Audience:** Search Engineers, Relevance Strategists, QA Leads.
**Last reviewed:** 2026-03-19 | **Reviewer:** [Initials]

---

## Key Judgements

- **If you aren't testing relevance, you're just moving bits.** Migration is an opportunity to improve quality, not just switch engines. If your post-migration search quality is worse than pre-migration, you have failed the business.
- **The "Gold Query Set" is your only defense against subjective QA.** Without a set of queries that you test repeatedly, "search quality" is just the loudest stakeholder's opinion.
- **BM25 vs. TF-IDF is not a bug; it's a feature.** Do not attempt to force OpenSearch to return identical scores to Solr's TF-IDF. Instead, validate that the *ordering* of results meets the user's information need.
- **"Silent failures" are more dangerous than crashes.** A search that returns 0 results is a bug. A search that returns "OK" results for the wrong queries is a business disaster.
- **Traffic shadowing is the "Gold Standard" of cutover.** If your scale allows it, nothing beats observing how real users interact with the new engine before turning off the old one.

---

## Decision Heuristics: Relevance & Validation

| Situation | Heuristic |
|:---|:---|
| **No Query Logs** | You can't build a gold set from scratch if you have zero history. Start by mining search logs and manually judging the top 100 queries by volume. |
| **Stakeholder Panic** | When they say "the results look different," have the Gold Set metrics ready. "The top 10 results have an 85% overlap with Solr, and the 15% difference is due to improved handling of [X]." |
| **Parity Divergence** | If results look "wrong" in OpenSearch, first check if the Solr index was even using the intended analyzer chain. You might have been matching "junk" in Solr and are now matching "truth" in OS. |
| **"When is it done?"** | You are "done" when the Gold Query Set metrics (e.g., NDCG or Precision@K) are stable or improved compared to the Solr baseline. |

---

## Common Pitfalls: War Stories

- **The "Alphabetical Sort" Bug:** A client migrated and found their products were sorted alphabetically by default. They blamed the "new search engine." It turned out their old Solr index had been broken for years (no relevance score), and the application layer had silently defaulted to an alphabetical sort. The new engine was actually returning *relevance-based* scores, which the client hated because it "didn't look the same."
- **The "Slow Facet" Surprise:** After cutover, the faceted navigation was 10x slower on the new cluster. They had imported the Solr schema but missed that Solr's `fieldCache` was hiding the performance cost of high-cardinality facets. OpenSearch required `doc_values` to be explicitly managed for those fields.

---

## Next Steps

1.  **Baseline Generation:** Before doing anything, run your top 100 queries against the current Solr production system and capture the results. This is your "Baseline."
2.  **Gold Query Set Creation:** Use **Quepid** to import these queries and add human ratings (1–5) to the results.
3.  **Automated Tuning Loop:** Once you have the baseline, iterate on your OpenSearch `schema` and `settings` until the relevance metrics (NDCG) meet or exceed the baseline.
