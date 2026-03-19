# Technical Design: minti9 Techproducts Migration

This design document records the architecture and specific OpenSearch configurations used for the `minti9` migration.

## Index Mapping (JSON)

The following mapping was applied directly to `http://minti9:19200/techproducts`.

```json
{
  "settings": {
    "index": { "number_of_shards": 1, "number_of_replicas": 0 },
    "analysis": {
      "filter": {
        "english_stop": { "type": "stop", "stopwords": "_english_" },
        "synonym_graph": {
          "type": "synonym_graph",
          "synonyms": ["hard disk,hard drive", "hd,hard drive", "ipod,portable music player"]
        }
      },
      "analyzer": {
        "text_general_index": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop"]
        },
        "text_general_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop", "synonym_graph"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": { "type": "text", "analyzer": "text_general_index", "search_analyzer": "text_general_query", "copy_to": "_text_" },
      "manu": { "type": "text", "analyzer": "text_general_index", "copy_to": ["_text_", "manu_exact"], "fields": { "keyword": { "type": "keyword" } } },
      "manu_exact": { "type": "keyword" },
      "cat": { "type": "text", "analyzer": "text_general_index", "copy_to": "_text_", "fields": { "keyword": { "type": "keyword" } } },
      "features": { "type": "text", "analyzer": "text_general_index", "copy_to": "_text_" },
      "price": { "type": "float" },
      "popularity": { "type": "integer" },
      "inStock": { "type": "boolean" },
      "store": { "type": "geo_point" },
      "manufacturedate_dt": { "type": "date" },
      "_text_": { "type": "text", "analyzer": "text_general_index" }
    }
  }
}
```

## Migration Commands

### Export/Import Script (Shell + jq)
Used for the one-time migration of 4 documents:

```bash
curl -s "http://minti9:18983/solr/techproducts/select?q=*:*&rows=1000&wt=json" | \
jq -c '.response.docs[] | {index: {_index: "techproducts", _id: .id}}, .' | \
curl -X POST "http://minti9:19200/_bulk" -H "Content-Type: application/x-ndjson" --data-binary @-
```

## Known Operational Configurations

- **Cluster Blocks:** The setting `cluster.blocks.create_index` was manually set to `false` to override percentage-based disk watermarks.
- **Disk Watermarks:** Overridden with transient settings (Low: 95, High: 98, Flood: 99) due to host disk utilization.

---
**Version:** 1.0
**Date:** 2026-03-18
