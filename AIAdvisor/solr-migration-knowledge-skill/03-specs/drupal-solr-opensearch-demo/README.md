# Drupal Solr to OpenSearch Demo Migration

This demo shows a first-pass migration of the sample Drupal Solr config in:

- `/opt/work/OSC/agent99/01-sources/samples/drupal-solr8/conf/schema.xml`
- `/opt/work/OSC/agent99/01-sources/samples/drupal-solr8/conf/solrconfig.xml`
- `/opt/work/OSC/agent99/01-sources/samples/drupal-solr8/sample-docs.json`

It is intentionally a `demo migration package`, not a production migration recipe.

## What This Demo Produces

- `opensearch-index.json`
  A Drupal-shaped OpenSearch index definition using `dynamic_templates`.
- `sample-bulk.ndjson`
  The sample Drupal documents converted into OpenSearch bulk format.
- `query-examples.md`
  Example OpenSearch queries that roughly match the sample Solr behavior.

## Core Migration Judgment

For a real Drupal site using `search_api_solr`, the preferred production approach is:

1. install a Drupal OpenSearch backend module such as `search_api_opensearch`
2. create a new Search API server in Drupal
3. point Drupal at OpenSearch
4. reindex from Drupal

That is the correct operational path because Drupal owns the indexing lifecycle and tracking tables.

This demo exists for architecture discussion, proof-of-concept setup, and translation review.

## What We Mapped from the Solr Sample

From `schema.xml`:
- explicit fields such as `id`, `index_id`, `timestamp`, `site`, `hash`, and `spell`
- dynamic string fields: `ss_*`, `sm_*`
- dynamic integer fields: `is_*`, `im_*`
- dynamic boolean fields: `bs_*`, `bm_*`
- dynamic date fields: `ds_*`, `dm_*`
- English text fields: `ts_X3_en_*`, `tm_X3_en_*`
- n-gram fields: `tw_*`
- copy-field behavior into `spell`

From `solrconfig.xml`:
- the `/select` request handler defaults are treated as `application query defaults`, not index settings
- the `/terms` handler is not ported directly; in OpenSearch this would usually be handled via a suggester or dedicated autocomplete field strategy

## Important Demo Assumptions

- The sample schema defines English dynamic text templates.
- The sample documents also include `tm_X3_es_*` fields.
- To avoid dropping those fields in the demo, the mapping includes a generic fallback for `tm_*` and `ts_*`.
- That fallback is a demo convenience, not a final multilingual analyzer strategy.

## Files

- [opensearch-index.json](/opt/work/OSC/agent99/03-specs/drupal-solr-opensearch-demo/opensearch-index.json)
- [sample-bulk.ndjson](/opt/work/OSC/agent99/03-specs/drupal-solr-opensearch-demo/sample-bulk.ndjson)
- [query-examples.md](/opt/work/OSC/agent99/03-specs/drupal-solr-opensearch-demo/query-examples.md)

## How to Run the Demo

Create the index:

```bash
curl -X PUT http://localhost:9200/drupal_demo \
  -H 'Content-Type: application/json' \
  --data-binary @03-specs/drupal-solr-opensearch-demo/opensearch-index.json
```

Bulk load the sample docs:

```bash
curl -X POST 'http://localhost:9200/_bulk?refresh=true' \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @03-specs/drupal-solr-opensearch-demo/sample-bulk.ndjson
```

Smoke-test a search:

```bash
curl -X GET http://localhost:9200/drupal_demo/_search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "multi_match": {
        "query": "widgets",
        "fields": ["tm_X3_en_title^3", "tm_X3_en_body", "spell"]
      }
    }
  }'
```

## What This Demo Does Not Solve

- Drupal module compatibility validation
- production-grade multilingual analysis
- suggest/autocomplete parity
- Views and Facets integration validation
- Drupal-side reindex orchestration
- relevance tuning beyond a first-pass analyzer match

## Recommended Next Step

If this demo looks directionally correct, the next phase should be:

1. validate the Drupal backend module choice
2. create the real Drupal Search API OpenSearch server
3. compare the module-generated mapping against this demo
4. reindex from Drupal and run side-by-side validation on top queries

