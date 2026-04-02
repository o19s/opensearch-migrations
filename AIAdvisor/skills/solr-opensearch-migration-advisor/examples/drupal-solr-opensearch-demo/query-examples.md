# Query Examples

These examples show how the sample Drupal Solr behavior maps into first-pass OpenSearch queries for the demo index `drupal_demo`.

## 1. Basic Keyword Search

Equivalent intent:
- search English title and body fields
- boost title over body
- include the `spell` catch-all field

```json
{
  "query": {
    "multi_match": {
      "query": "widgets",
      "fields": [
        "tm_X3_en_title^3",
        "tm_X3_en_body",
        "spell"
      ],
      "type": "best_fields"
    }
  }
}
```

## 2. Search with Drupal-Like Status Filter

Equivalent intent:
- query content text
- filter to published content

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "widget",
            "fields": [
              "tm_X3_en_title^3",
              "tm_X3_en_body",
              "spell"
            ]
          }
        }
      ],
      "filter": [
        {
          "term": {
            "bs_status": true
          }
        }
      ]
    }
  }
}
```

## 3. Language-Scoped Search

Equivalent intent:
- limit results to a Drupal Search API language code

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "tienda",
            "fields": [
              "tm_X3_es_title^3",
              "tm_X3_es_body"
            ]
          }
        }
      ],
      "filter": [
        {
          "term": {
            "ss_search_api_language": "es"
          }
        }
      ]
    }
  }
}
```

## 4. Facet-Like Aggregation on Tags

Equivalent intent:
- approximate Drupal Facets behavior using terms aggregations

```json
{
  "size": 0,
  "query": {
    "term": {
      "bs_status": true
    }
  },
  "aggs": {
    "tags": {
      "terms": {
        "field": "sm_vid_tags",
        "size": 10
      }
    }
  }
}
```

## 5. Sort by Created Date

Equivalent intent:
- recent content first

```json
{
  "query": {
    "match_all": {}
  },
  "sort": [
    {
      "ds_created": {
        "order": "desc"
      }
    }
  ]
}
```

## Translation Notes

- Solr `/select` defaults such as `q.op=AND` should be implemented in the query layer, not in index settings.
- Solr `/terms` is not ported directly here; for a fuller Drupal demo, autocomplete should be handled separately.
- The `spell` field is preserved as a catch-all demo field via `copy_to` from English `tm_X3_en_*` and `ts_X3_en_*` fields.
- The Spanish sample fields are handled by a generic `tm_*` fallback. That is a demo convenience, not a full multilingual design.

