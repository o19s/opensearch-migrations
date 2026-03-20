# Migration Execution: The "Pass 1" Workflow

**Scope:** Schema-to-Mapping translation, bulk data migration, pipeline synchronization, and smoke testing.
**Audience:** Data Engineers, Search Platform Engineers.
**Last reviewed:** 2026-03-19 | **Reviewer:** [Initials]

---

## Key Judgements

- **The "Pass 1" is not production.** It is a discovery tool. Expect the first 3 migration attempts to fail due to data quality, mapping errors, or pipeline timeouts.
- **Bulk data movement is the easiest part; semantic migration is the hardest.** If your data is 5TB, you'll need parallel chunked loads (Logstash/Data Prepper) to finish in <24 hours.
- **Fail fast, log everything.** If a document fails to index, log the *reason* (e.g., mapping type mismatch) with the document ID. Do not just drop the doc and move on.
- **Schema-to-Mapping translation must be automated.** If you are manually writing thousands of lines of JSON, you are creating a "Legacy Mapping" that will be impossible to maintain.

---

## The "Pass 1" Workflow Checklist

1.  **Schema Audit**: Extract Solr `schema.xml` using the repo's migration helper at `01-sources/samples/northstar-enterprise-app/solr_to_opensearch.py` or an equivalent local script.
2.  **Mapping Generation**: Auto-generate initial OpenSearch JSON mappings.
3.  **Smoke Test**: Index 1,000 documents and verify all fields query correctly (e.g., do range queries work on `price`?).
4.  **Bulk Reindex**: Run parallel chunked exports (Solr `/export` → S3 → Logstash → OpenSearch).
5.  **Data Verification**: Run record counts for every collection: `count(Solr) == count(OpenSearch)`.

---

## Common Pitfalls: War Stories

- **The "Date Format" Mismatch:** A client had Solr dates in a non-standard `yyyy-MM-dd'T'HH:mm:ss'Z'` variant. OpenSearch's strict date parsing rejected 50% of the collection. **Lesson:** Always use a "Date Histogram" aggregation on your source Solr data *before* migrating to verify your formats.
- **The "Field Type Exploit":** A client didn't specify a type, and dynamic mapping chose `text` (analyzed) for a field that should have been `keyword`. All their filters/facets failed. **Lesson:** You *must* define an explicit mapping template.

---

## Next Steps

1.  **Tool Setup**: Ensure the migration helper you are using is available and executable.
2.  **Schema Extraction**: Dump the current Solr schema from your target collection.
3.  **Dry Run**: Perform a "Dry Run" by exporting a sample of 1,000 docs and importing to OpenSearch.
4.  **Iterate**: Address any mapping errors from Step 3.
