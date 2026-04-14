# Solr copyField → OpenSearch Multi-Fields

## Key Rule
Solr `copyField` with a differently-analyzed destination field becomes an
OpenSearch **multi-field** (`fields:` in the mapping), NOT `copy_to`.

OpenSearch `copy_to` copies the raw source value to another field, but does
NOT re-analyze it with a different analyzer. For synonym, idiom, or
language-specific variants, you MUST use multi-fields.

## TMDB Example
Solr schema:
```xml
<copyField source="title" dest="title_bidirect_syn"/>
<copyField source="title" dest="title_en"/>
<copyField source="title" dest="title_idioms"/>
```

OpenSearch mapping:
```json
{
  "title": {
    "type": "text",
    "analyzer": "text_general",
    "fields": {
      "bidirect_syn": {
        "type": "text",
        "analyzer": "synonym_bidirectional"
      },
      "en": {
        "type": "text",
        "analyzer": "english"
      },
      "idioms": {
        "type": "text",
        "analyzer": "idiom_aware"
      }
    }
  }
}
```

Query the sub-fields as `title.en`, `title.bidirect_syn`, etc.
