# Schema and Field Type Mapping: Solr to OpenSearch

**Source**: https://bigdataboutique.com/blog/schema-migration-from-solr-to-elasticsearch-opensearch-a0072b

---

## Executive Summary

Schema migration is the critical first step before data migration. Solr's XML-based schema differs fundamentally from OpenSearch's JSON-based mappings and settings. This document provides detailed field type mappings, analyzer chain translations, and handling of Solr-specific constructs like dynamic fields and nested documents.

---

## Field Type Mapping Table

### Primitive Types

| Solr Field Type | OpenSearch Type | Comment | Example |
|-----------------|-----------------|---------|---------|
| `string` | `keyword` | Exact matching, no analysis | Brand name, SKU |
| `int` | `integer` | 32-bit signed integer | Product ID |
| `long` | `long` | 64-bit signed integer | Timestamp in milliseconds |
| `float` | `float` | 32-bit IEEE 754 | Price in dollars |
| `double` | `double` | 64-bit IEEE 754 | Precise calculation result |
| `boolean` | `boolean` | True/false | Is published |
| `pdate` | `date` | Indexed date with optional time | Publication date |
| `pdates` | `date` (array) | Multiple dates | Event dates |

### Text Types

| Solr Field Type | OpenSearch Type | Strategy | Notes |
|-----------------|-----------------|----------|-------|
| `text_general` | `text` | Use standard analyzer | Default text analysis |
| `text_en` | `text` + English analyzer | Configure index settings | Language-specific analysis |
| `text_ws` (whitespace) | `text` + whitespace tokenizer | Custom analyzer in settings | No analysis, whitespace split |
| `text_ja` (Japanese) | `text` + Kuromoji analyzer | Install analysis-icu plugin | CJK text |
| Custom analyzer types | `text` + custom analyzer | Define in settings | Multi-step analysis chains |

### Specialized Types

| Solr Field Type | OpenSearch Type | Strategy |
|-----------------|-----------------|----------|
| `location` (LatLon) | `geo_point` | Can accept "lat,lon" or object format |
| `geo_rpt` (spatial) | `geo_shape` | For complex polygon/line queries |
| `binary` | `binary` | Raw binary data (rare) |
| `currency` | `float` (scaled) or `keyword` | Store as float, apply exchange rates at query time |
| `analyzed` (parent type) | Not applicable | OpenSearch text fields are always analyzed |

---

## Analyzer Chain Translation

Analyzers define how text is processed during indexing and querying. Solr uses XML chains; OpenSearch uses JSON configuration.

### Simple Standard Analyzer

**Solr** (implicit, text_general):
```xml
<fieldType name="text_general">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
  </analyzer>
</fieldType>
```

**OpenSearch**:
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "standard_lowercase": {
          "type": "standard",
          "stopwords": []
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard_lowercase"
      }
    }
  }
}
```

**Key differences**:
- Solr: Analyzers are defined once, applied to multiple fields via `type` attribute
- OpenSearch: Analyzers are named and defined globally; fields reference them by name

---

### Complex Analyzer with Stemming

**Solr**:
```xml
<fieldType name="text_en_stem">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.StopFilterFactory" words="stopwords.txt" ignoreCase="true"/>
    <filter class="solr.PorterStemFilterFactory"/>
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.StopFilterFactory" words="stopwords.txt" ignoreCase="true"/>
    <!-- No stemming at query time for precision -->
  </analyzer>
</fieldType>
```

**OpenSearch**:
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "text_en_stem_index": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop_en", "porter_stem"]
        },
        "text_en_stem_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop_en"]
        }
      },
      "filter": {
        "stop_en": {
          "type": "stop",
          "stopwords": "_english_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "description": {
        "type": "text",
        "analyzer": "text_en_stem_index",
        "search_analyzer": "text_en_stem_query"
      }
    }
  }
}
```

**Mapping principle**:
- Solr's `analyzer type="index"` → OpenSearch's `analyzer`
- Solr's `analyzer type="query"` → OpenSearch's `search_analyzer`
- Both applied to the same field

---

### Common Analyzer Components

#### Tokenizers

| Solr Tokenizer | OpenSearch Equivalent | Use Case |
|----------------|----------------------|----------|
| `StandardTokenizer` | `standard` | Default: splits on whitespace and punctuation |
| `WhitespaceTokenizer` | `whitespace` | Simple whitespace splitting (no punctuation) |
| `KeywordTokenizer` | `keyword` | No tokenization (entire input = one token) |
| `PatternTokenizer` | `pattern` | Regex-based splitting |
| `PathHierarchyTokenizer` | Custom pattern | File paths, hierarchies |
| `EdgeNGramTokenizer` | `edge_ngram` | Auto-complete on typed characters |
| `NGramTokenizer` | `ngram` | Substring matching |
| `CJKBigramTokenizer` | `cjk_bigram` | East Asian text (requires plugin) |

---

#### Filters

| Solr Filter | OpenSearch Equivalent | Purpose |
|-------------|----------------------|---------|
| `LowerCaseFilter` | `lowercase` | Normalize to lowercase |
| `UpperCaseFilter` | `uppercase` | Normalize to uppercase |
| `StopFilter` | `stop` | Remove common words |
| `PorterStemFilter` | `porter_stem` | Reduce words to root form |
| `SynonymFilter` | `synonym` | Expand queries with synonyms |
| `RemoveDuplicatesFilter` | `remove_duplicates` | Remove duplicate tokens |
| `TrimFilter` | `trim` | Remove leading/trailing whitespace |
| `ReverseFilter` | `reverse` | Reverse token order |
| `NGramFilter` | `ngram` | Generate N-grams |
| `EdgeNGramFilter` | `edge_ngram` | Generate prefix N-grams |
| `ShingleFilter` | `shingle` | Create phrases from consecutive tokens |
| `MinLengthFilter` | `length` | Filter tokens by length |
| `UniqueFilter` | `unique` | Remove duplicates |
| `ApostropheFilter` | Custom char_filter | Handle apostrophes |

---

#### Character Filters

Character filters preprocess text before tokenization:

| Solr Char Filter | OpenSearch Equivalent | Purpose |
|------------------|----------------------|---------|
| `MappingCharFilter` | `mapping` | Replace characters/substrings |
| `HTMLStripCharFilter` | `html_strip` | Remove HTML tags |
| `PatternReplaceCharFilter` | `pattern_replace` | Regex character replacement |

**Example: HTML Strip**

**Solr**:
```xml
<analyzer>
  <charFilter class="solr.HTMLStripCharFilterFactory" escaped="false"/>
  <tokenizer class="solr.StandardTokenizerFactory"/>
  <filter class="solr.LowerCaseFilterFactory"/>
</analyzer>
```

**OpenSearch**:
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "html_strip_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip"],
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      }
    }
  }
}
```

---

## Dynamic Fields Mapping

Solr's dynamic fields use naming conventions (`*_s`, `*_i`) to auto-type fields. OpenSearch uses dynamic templates.

### Solr Dynamic Fields

```xml
<dynamicField name="*_s" type="string" indexed="true" stored="true"/>
<dynamicField name="*_t" type="text_general" indexed="true" stored="true"/>
<dynamicField name="*_i" type="int" indexed="true" stored="true"/>
<dynamicField name="*_f" type="float" indexed="true" stored="true"/>
<dynamicField name="*_b" type="boolean" indexed="true" stored="true"/>
<dynamicField name="*_d" type="pdate" indexed="true" stored="true"/>
<dynamicField name="*_l" type="location" indexed="true" stored="true"/>
```

### OpenSearch Dynamic Templates

```json
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keywords": {
          "match_mapping_type": "string",
          "match": "*_s",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "text_fields": {
          "match": "*_t",
          "mapping": {
            "type": "text",
            "analyzer": "standard"
          }
        }
      },
      {
        "integer_fields": {
          "match": "*_i",
          "mapping": {
            "type": "integer"
          }
        }
      },
      {
        "float_fields": {
          "match": "*_f",
          "mapping": {
            "type": "float"
          }
        }
      },
      {
        "boolean_fields": {
          "match": "*_b",
          "mapping": {
            "type": "boolean"
          }
        }
      },
      {
        "date_fields": {
          "match": "*_d",
          "mapping": {
            "type": "date"
          }
        }
      },
      {
        "geo_point_fields": {
          "match": "*_l",
          "mapping": {
            "type": "geo_point"
          }
        }
      }
    ]
  }
}
```

**Key differences**:
- Solr applies dynamic fields at document insertion
- OpenSearch applies templates at mapping definition time, but also at index time if `dynamic: true`
- OpenSearch templates can use regex patterns: `match_pattern: "^metrics_.*"` for more flexibility

---

### Disabling Dynamic Mapping

To prevent unmapped fields (security, storage):

**OpenSearch**:
```json
{
  "mappings": {
    "dynamic": false
  }
}
```

This rejects documents with unmapped fields. For strict schema enforcement, use `dynamic: "strict"`.

---

## CopyField Translation

CopyField combines multiple source fields into a target field for efficient multi-field search.

### Solr CopyField

```xml
<field name="title" type="text_general" indexed="true" stored="true"/>
<field name="body" type="text_general" indexed="true" stored="true"/>
<field name="search_text" type="text_general" indexed="true" stored="false"/>

<copyField source="title" dest="search_text"/>
<copyField source="body" dest="search_text"/>
```

### OpenSearch copy_to

```json
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "copy_to": "search_text"
      },
      "body": {
        "type": "text",
        "copy_to": "search_text"
      },
      "search_text": {
        "type": "text",
        "index": true,
        "store": false
      }
    }
  }
}
```

**Behavior**:
- Values from `title` and `body` are concatenated into `search_text`
- Search `search_text` returns docs matching any source field
- More efficient than disjunctive queries across multiple fields
- `store: false` saves disk space (OpenSearch can reconstruct from source)

---

## Unique Key Mapping

### Solr uniqueKey

```xml
<uniqueKey>id</uniqueKey>
```

### OpenSearch _id Field

```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      }
    }
  }
}
```

When indexing, use the `id` field as the document's `_id`:

```json
PUT /index/_doc/123
{
  "id": "123",
  "title": "My Document"
}
```

Or let OpenSearch auto-generate:

```json
POST /index/_doc
{
  "title": "My Document"
}
```

**Key difference**: Solr requires explicit uniqueKey; OpenSearch uses `_id` (which can be separate from document fields).

---

## Nested and Child Documents

### Solr Nested Documents

Solr supports nested documents (block join):

```json
{
  "id": "parent-1",
  "title": "Parent Document",
  "_childDocuments_": [
    {
      "id": "child-1",
      "type": "comment",
      "text": "First comment"
    },
    {
      "id": "child-2",
      "type": "comment",
      "text": "Second comment"
    }
  ]
}
```

Query using block join:
```
q={!parent which="type:parent" score=total v=$child}&child=type:comment AND text:important
```

### OpenSearch Nested Type

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "title": { "type": "text" },
      "comments": {
        "type": "nested",
        "properties": {
          "id": { "type": "keyword" },
          "type": { "type": "keyword" },
          "text": { "type": "text" }
        }
      }
    }
  }
}
```

Document structure:
```json
{
  "id": "parent-1",
  "title": "Parent Document",
  "comments": [
    {
      "id": "child-1",
      "type": "comment",
      "text": "First comment"
    },
    {
      "id": "child-2",
      "type": "comment",
      "text": "Second comment"
    }
  ]
}
```

Query nested:
```json
{
  "query": {
    "nested": {
      "path": "comments",
      "query": {
        "bool": {
          "must": [
            { "term": { "comments.type": "comment" } },
            { "match": { "comments.text": "important" } }
          ]
        }
      }
    }
  }
}
```

**OpenSearch nested vs Solr nested**:
- OpenSearch: Nested docs preserve parent-child association; queries return parent documents
- Solr: Block join queries explicitly manage parent/child relationship
- OpenSearch: Nested arrays expand to separate hidden documents (one per array element)
- Solr: Nested docs stored compactly within parent

---

## Multivalue Fields

### Solr Multivalue

```xml
<field name="tags" type="string" indexed="true" stored="true" multiValued="true"/>
```

Document:
```json
{
  "id": "doc-1",
  "tags": ["python", "solr", "search"]
}
```

### OpenSearch Multivalue

OpenSearch handles arrays naturally—no special configuration needed:

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "tags": { "type": "keyword" }
    }
  }
}
```

Document:
```json
{
  "id": "doc-1",
  "tags": ["python", "solr", "search"]
}
```

**Query behavior**:
- Solr: `tags:python` matches if "python" is one of the tag values
- OpenSearch: `term: { tags: "python" }` matches same way
- Both support `terms` query for multiple values

---

## Field Properties Mapping

| Solr Property | OpenSearch Property | Purpose |
|---------------|--------------------| --------|
| `indexed="true"` | N/A (default for searchable fields) | Enable searching |
| `indexed="false"` | `index: false` | Disable searching, save space |
| `stored="true"` | N/A (enabled by default via _source) | Include in results |
| `stored="false"` | `store: false` | Exclude from storage, reconstruct from _source |
| `docValues="true"` | N/A (automatic for non-text) | Enable sorting/aggregation |
| `docValues="false"` | `doc_values: false` | Disable doc values, save memory |
| `multiValued="true"` | N/A (arrays are native) | Field can have multiple values |
| `required="true"` | N/A | Must be set (no validation) |
| `omitNorms="true"` | `norms: false` | Disable length normalization |
| `omitTermFreqAndPositions="true"` | N/A | No term frequency/position info |
| `termVectors="true"` | `term_vector: "with_positions_offsets"` | Store term vectors |

**Example with properties**:

**Solr**:
```xml
<field name="id" type="string" indexed="true" stored="true" required="true"/>
<field name="title" type="text_general" indexed="true" stored="true"/>
<field name="category" type="string" indexed="true" stored="true" docValues="true"/>
<field name="internal_notes" type="text_general" indexed="true" stored="false"/>
```

**OpenSearch**:
```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "title": {
        "type": "text"
      },
      "category": {
        "type": "keyword",
        "doc_values": true
      },
      "internal_notes": {
        "type": "text",
        "store": false
      }
    }
  }
}
```

---

## Complex Schema Example: E-commerce Product

### Solr Schema

```xml
<schema name="ecommerce" version="1.6">
  <uniqueKey>sku</uniqueKey>

  <fieldType name="text_general">
    <analyzer>
      <tokenizer class="solr.StandardTokenizerFactory"/>
      <filter class="solr.LowerCaseFilterFactory"/>
      <filter class="solr.StopFilterFactory"/>
    </analyzer>
  </fieldType>

  <fieldType name="text_en">
    <analyzer>
      <tokenizer class="solr.StandardTokenizerFactory"/>
      <filter class="solr.LowerCaseFilterFactory"/>
      <filter class="solr.StopFilterFactory" words="lang/english_stop.txt"/>
      <filter class="solr.PorterStemFilterFactory"/>
    </analyzer>
  </fieldType>

  <field name="sku" type="string" indexed="true" stored="true" required="true"/>
  <field name="title" type="text_en" indexed="true" stored="true"/>
  <field name="description" type="text_en" indexed="true" stored="true"/>
  <field name="category" type="string" indexed="true" stored="true" docValues="true" multiValued="true"/>
  <field name="price" type="float" indexed="true" stored="true" docValues="true"/>
  <field name="stock_qty" type="int" indexed="true" stored="true" docValues="true"/>
  <field name="in_stock" type="boolean" indexed="true" stored="true"/>
  <field name="published_date" type="pdate" indexed="true" stored="true" docValues="true"/>
  <field name="rating" type="float" indexed="true" stored="true" docValues="true"/>
  <field name="reviews_count" type="int" indexed="true" stored="true" docValues="true"/>
  <field name="tags" type="string" indexed="true" stored="true" multiValued="true"/>
  <field name="location" type="location" indexed="true" stored="true" docValues="true"/>

  <dynamicField name="*_s" type="string" indexed="true" stored="true"/>
  <dynamicField name="*_t" type="text_general" indexed="true" stored="true"/>
  <dynamicField name="*_i" type="int" indexed="true" stored="true"/>

  <copyField source="title" dest="text_all"/>
  <copyField source="description" dest="text_all"/>
  <copyField source="tags" dest="text_all"/>
</schema>
```

### OpenSearch Mapping

```json
{
  "settings": {
    "index": {
      "number_of_shards": 5,
      "number_of_replicas": 2
    },
    "analysis": {
      "analyzer": {
        "text_en": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop_en", "porter_stem"]
        }
      },
      "filter": {
        "stop_en": {
          "type": "stop",
          "stopwords": "_english_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "sku": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "text_en",
        "copy_to": "text_all"
      },
      "description": {
        "type": "text",
        "analyzer": "text_en",
        "copy_to": "text_all"
      },
      "category": {
        "type": "keyword",
        "doc_values": true
      },
      "price": {
        "type": "float",
        "doc_values": true
      },
      "stock_qty": {
        "type": "integer",
        "doc_values": true
      },
      "in_stock": {
        "type": "boolean"
      },
      "published_date": {
        "type": "date",
        "doc_values": true
      },
      "rating": {
        "type": "float",
        "doc_values": true
      },
      "reviews_count": {
        "type": "integer",
        "doc_values": true
      },
      "tags": {
        "type": "keyword",
        "copy_to": "text_all"
      },
      "location": {
        "type": "geo_point",
        "doc_values": true
      },
      "text_all": {
        "type": "text",
        "analyzer": "text_en",
        "store": false
      }
    },
    "dynamic_templates": [
      {
        "string_suffix": {
          "match": "*_s",
          "mapping": { "type": "keyword" }
        }
      },
      {
        "text_suffix": {
          "match": "*_t",
          "mapping": { "type": "text", "analyzer": "text_en" }
        }
      },
      {
        "int_suffix": {
          "match": "*_i",
          "mapping": { "type": "integer" }
        }
      }
    ]
  }
}
```

---

## Migration Validation Checklist

- [ ] All Solr field types mapped to OpenSearch types
- [ ] All custom analyzers translated to JSON settings
- [ ] Dynamic field templates created for auto-typing
- [ ] CopyField directives converted to `copy_to`
- [ ] MultiValued fields verified (arrays work natively)
- [ ] Nested documents mapped to nested type or join
- [ ] Doc values enabled for sorting/aggregation fields
- [ ] Storage options (`stored: false`) applied appropriately
- [ ] Custom filters/tokenizers available (check plugin requirements)
- [ ] Mapping created but not yet indexed
- [ ] Sample documents validated against mapping
- [ ] Index settings tuned (shards, replicas, refresh interval)

