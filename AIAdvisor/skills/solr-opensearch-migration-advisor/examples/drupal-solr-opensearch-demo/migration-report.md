# Drupal Solr to OpenSearch Demo Migration Report

This report compares the sample Drupal Solr schema to the demo OpenSearch mapping in:

- [schema.xml](/opt/work/OSC/agent99/sources/samples/drupal-solr8/conf/schema.xml)
- [solrconfig.xml](/opt/work/OSC/agent99/sources/samples/drupal-solr8/conf/solrconfig.xml)
- [opensearch-index.json](/opt/work/OSC/agent99/examples/drupal-solr-opensearch-demo/opensearch-index.json)

## Executive Summary

The sample Drupal Solr schema can be translated into a reasonable first-pass OpenSearch demo using:
- explicit `keyword` and `date` mappings for core fields
- `dynamic_templates` for Drupal field prefixes
- custom analyzers for English text and n-gram fields
- `copy_to` to preserve the Solr `spell` catch-all behavior

The demo is directionally correct for architecture review and proof-of-concept use. It is not the preferred production migration path for a real Drupal site. In production, Drupal should reindex into OpenSearch through its Search API backend rather than migrate the Solr index directly.

## Source Schema Summary

The sample Solr schema includes:
- primitive field types: `string`, `boolean`, `int`, `float`, `long`, `double`, `date`
- English text type: `text_en`
- n-gram text type: `text_ngram`
- explicit fields: `id`, `index_id`, `timestamp`, `site`, `hash`, `spell`
- dynamic fields for Drupal Search API naming conventions
- copy-field rules from English text fields into `spell`

## Field-by-Field Translation

| Solr element | Demo OpenSearch mapping | Notes |
|---|---|---|
| `id` as `string` | `keyword` | Correct for exact document ID and stable `_id` use. |
| `index_id` as `string` | `keyword` | Correct for exact filtering and grouping. |
| `site` as `string` | `keyword` | Preserves exact site identity. |
| `hash` as `string` | `keyword` | Preserves exact matching and duplicate detection use. |
| `timestamp` as `date` | `date` with `strict_date_optional_time||epoch_millis` | Appropriate OpenSearch date mapping. |
| `spell` as `text_en` | `text` with English analyzer and search analyzer | Preserves the catch-all searchable bucket concept. |
| `ss_*` as `string` | `keyword` via dynamic template | Correct for single-valued exact-match Drupal fields. |
| `sm_*` as `string` multivalued | `keyword` via dynamic template | OpenSearch arrays work without special multivalue mapping. |
| `is_*` as `int` | `integer` via dynamic template | Straightforward translation. |
| `im_*` as `int` multivalued | `integer` via dynamic template | Straightforward translation. |
| `bs_*` as `boolean` | `boolean` via dynamic template | Straightforward translation. |
| `bm_*` as `boolean` multivalued | `boolean` via dynamic template | Straightforward translation. |
| `ds_*` as `date` | `date` via dynamic template | Straightforward translation. |
| `dm_*` as `date` multivalued | `date` via dynamic template | Straightforward translation. |
| `ts_X3_en_*` as `text_en` | `text` with `drupal_text_en` analyzer and `copy_to: spell` | Correct first-pass mapping for English text fields. |
| `tm_X3_en_*` as `text_en` multivalued | `text` with `drupal_text_en` analyzer and `copy_to: spell` | Correct first-pass mapping for English multivalue text fields. |
| `tw_*` as `text_ngram` | `text` with index/search n-gram analyzers | Good demo approximation for partial matching. |

## Analyzer Translation

### `text_en`

Solr index analyzer:
- standard tokenizer
- English stopwords
- lowercase
- English possessive handling
- keyword marker
- Porter stemming

Solr query analyzer:
- same as above, plus synonym graph filter

Demo OpenSearch translation:
- `drupal_text_en`
- `drupal_text_en_search`

Preserved:
- standard tokenization
- lowercase normalization
- English stopword removal
- possessive English handling
- Porter stemming

Not preserved in this demo:
- explicit synonym file support
- protected-word handling from `protwords.txt`

Judgment:
- good first-pass analyzer match
- not full fidelity

### `text_ngram`

Solr index analyzer:
- standard tokenizer
- lowercase
- n-gram filter with `3..15`

Solr query analyzer:
- standard tokenizer
- lowercase

Demo OpenSearch translation:
- `drupal_ngram_index`
- `drupal_ngram_search`

Judgment:
- close conceptual translation
- acceptable for demo autocomplete or partial-term behavior

## Copy Field Translation

Solr uses:
- `copyField source="tm_X3_en_*" dest="spell"`
- `copyField source="ts_X3_en_*" dest="spell"`

Demo OpenSearch uses:
- `copy_to: "spell"` on the matching English text dynamic templates

Judgment:
- this is the correct OpenSearch equivalent for the sample behavior

## `solrconfig.xml` Translation Notes

The sample `solrconfig.xml` contains settings that do not translate directly into index mappings.

### Preserved conceptually

| Solr config element | OpenSearch treatment |
|---|---|
| `/select` request defaults | Move into the application query layer |
| `/terms` handler | Replace with suggester or separate autocomplete design |
| auto commit / soft commit | Approximate with `refresh_interval` |
| filter/query/document cache tuning | Not directly migrated in this demo |

### Not directly migrated

| Solr config element | Reason |
|---|---|
| cache classes and warmers | OpenSearch has a different caching model |
| request handler definitions | OpenSearch uses query DSL and application-side request shaping |
| update log configuration | No direct equivalent in this demo |
| Solr-specific dispatcher settings | Not relevant to OpenSearch index definition |

## Sample Document Validation

The sample docs include:
- English fields: `tm_X3_en_title`, `tm_X3_en_body`
- Spanish fields: `tm_X3_es_title`, `tm_X3_es_body`

Important mismatch:
- the sample schema only explicitly defines English `tm_X3_en_*` and `ts_X3_en_*` patterns
- the sample documents include Spanish `tm_X3_es_*` fields

Demo response:
- added generic `tm_*` and `ts_*` templates using a lowercase-only analyzer

Judgment:
- this prevents the Spanish sample data from being dropped
- this is a demo convenience, not a real multilingual content design

## Risks and Gaps

### Gap 1: Multilingual analysis is incomplete

Impact:
- non-English content will index, but language-specific stemming and stopword behavior are not preserved

Recommendation:
- model language-specific analyzers explicitly if multilingual search quality matters

### Gap 2: Synonyms are not migrated

Impact:
- recall and query expansion may differ from Solr

Recommendation:
- convert the synonym asset into OpenSearch synonym or synonym_graph configuration during the next pass

### Gap 3: Protected-word behavior is not migrated

Impact:
- stemming behavior may diverge for protected terms

Recommendation:
- review whether protected word lists materially affect the Drupal site

### Gap 4: Autocomplete is only implied

Impact:
- the `tw_*` n-gram mapping is only a first-pass text analysis strategy

Recommendation:
- validate autocomplete behavior separately, especially if Drupal uses `search_api_autocomplete`

### Gap 5: Drupal runtime behavior is outside this demo

Impact:
- this demo does not validate Views integration, Facets integration, module compatibility, or Search API tracking behavior

Recommendation:
- perform the real migration by configuring a Drupal OpenSearch backend and reindexing from Drupal

## Recommended Real-World Migration Posture

For a real Drupal migration:

1. do not attempt Lucene-level or raw-index migration
2. use Drupal to define the new backend
3. compare the module-generated mapping to this demo mapping
4. reindex from Drupal
5. validate top queries, faceting, autocomplete, and Views-based pages

## E1: Demo Execution Status

Attempted local endpoint:
- `http://localhost:9200`

Current status:
- no local OpenSearch endpoint is reachable in this environment right now

Command result:
- connection refused on port `9200`

When a cluster is available, use:

```bash
curl -X PUT http://localhost:9200/drupal_demo \
  -H 'Content-Type: application/json' \
  --data-binary @examples/drupal-solr-opensearch-demo/opensearch-index.json
```

```bash
curl -X POST 'http://localhost:9200/_bulk?refresh=true' \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @examples/drupal-solr-opensearch-demo/sample-bulk.ndjson
```

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

