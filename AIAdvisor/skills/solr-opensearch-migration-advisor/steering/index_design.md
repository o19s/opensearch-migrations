# Solr to OpenSearch Index Design Steering

## Schema Mapping
- Solr `uniqueKey` → OpenSearch `_id`.
- Solr `multiValued="true"` → OpenSearch arrays are native, no special mapping needed.
- Solr `stored="true"` → OpenSearch `store: true` (rarely used, defaults to `_source`).
- Solr `indexed="true"` → OpenSearch `index: true` (default).
- Solr `docValues="true"` → OpenSearch `doc_values: true` (default for most types).

## Field Types
- `solr.TextField` → `text`.
- `solr.StrField` → `keyword`.
- `solr.IntField`, `solr.LongField` → `integer`, `long`.
- `solr.FloatField`, `solr.DoubleField` → `float`, `double`.
- `solr.DateField` → `date`.
- `solr.BoolField` → `boolean`.

## Analysis
- Solr Tokenizers/Filters → OpenSearch Analysers/Tokenizers/Filters.
- `copyField` → `copy_to`.

## Analyzer Chain Conversion Examples

### 1. Standard text analysis (most common)
Solr (`schema.xml`):
```xml
<fieldType name="text_general" class="solr.TextField">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.StopFilterFactory" words="stopwords.txt"/>
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.StopFilterFactory" words="stopwords.txt"/>
    <filter class="solr.SynonymGraphFilterFactory" synonyms="synonyms.txt"/>
  </analyzer>
</fieldType>
```
OpenSearch mapping:
```json
{
  "settings": {
    "analysis": {
      "filter": {
        "my_stop": { "type": "stop", "stopwords_path": "stopwords.txt" },
        "my_synonyms": { "type": "synonym_graph", "synonyms_path": "synonyms.txt" }
      },
      "analyzer": {
        "text_general_index": {
          "tokenizer": "standard",
          "filter": ["lowercase", "my_stop"]
        },
        "text_general_search": {
          "tokenizer": "standard",
          "filter": ["lowercase", "my_stop", "my_synonyms"]
        }
      }
    }
  }
}
```
Note: OpenSearch expects synonym/stopword files in the `config/` directory on each node (or use inline lists for small sets).

### 2. Edge n-gram for autocomplete
Solr:
```xml
<fieldType name="text_autocomplete" class="solr.TextField">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.EdgeNGramFilterFactory" minGramSize="2" maxGramSize="15"/>
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
  </analyzer>
</fieldType>
```
OpenSearch:
```json
{
  "analysis": {
    "filter": {
      "autocomplete_filter": { "type": "edge_ngram", "min_gram": 2, "max_gram": 15 }
    },
    "analyzer": {
      "autocomplete_index": {
        "tokenizer": "standard",
        "filter": ["lowercase", "autocomplete_filter"]
      },
      "autocomplete_search": {
        "tokenizer": "standard",
        "filter": ["lowercase"]
      }
    }
  }
}
```
Note: Use `search_analyzer` on the field mapping to apply different analyzers at index vs. query time.

### 3. Stemming with Porter stemmer
Solr:
```xml
<fieldType name="text_en" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
    <filter class="solr.PorterStemFilterFactory"/>
  </analyzer>
</fieldType>
```
OpenSearch:
```json
{
  "analysis": {
    "analyzer": {
      "text_en": {
        "tokenizer": "standard",
        "filter": ["lowercase", "porter_stem"]
      }
    }
  }
}
```

### 4. Snowball stemmer (language-specific)
Solr:
```xml
<filter class="solr.SnowballPorterFilterFactory" language="German"/>
```
OpenSearch:
```json
{ "type": "snowball", "language": "German" }
```

### 5. WordDelimiterGraphFilter (complex)
Solr:
```xml
<filter class="solr.WordDelimiterGraphFilterFactory"
        generateWordParts="1" generateNumberParts="1"
        catenateWords="1" catenateNumbers="1"
        splitOnCaseChange="1" preserveOriginal="1"/>
```
OpenSearch:
```json
{
  "type": "word_delimiter_graph",
  "generate_word_parts": true,
  "generate_number_parts": true,
  "catenate_words": true,
  "catenate_numbers": true,
  "split_on_case_change": true,
  "preserve_original": true
}
```
Note: Defaults differ between Solr and OpenSearch — always explicitly set every option you rely on.

### 6. ICU folding (Unicode normalization)
Solr:
```xml
<filter class="solr.ICUFoldingFilterFactory"/>
```
OpenSearch:
```json
{ "type": "icu_folding" }
```
Note: Requires the `analysis-icu` plugin. Install via `bin/opensearch-plugin install analysis-icu`. On AWS Managed OpenSearch, the ICU plugin is pre-installed.

### 7. Phonetic filter
Solr:
```xml
<filter class="solr.PhoneticFilterFactory" encoder="DoubleMetaphone" inject="true"/>
```
OpenSearch:
```json
{ "type": "phonetic", "encoder": "double_metaphone", "replace": false }
```
Note: Requires the `analysis-phonetic` plugin. Solr `inject="true"` (keep original token) maps to OpenSearch `replace: false`.

### 8. Pattern tokenizer
Solr:
```xml
<tokenizer class="solr.PatternTokenizerFactory" pattern="[,;\s]+"/>
```
OpenSearch:
```json
{ "type": "pattern", "pattern": "[,;\\s]+" }
```

### 9. KeywordTokenizer + LowerCase (exact match, case-insensitive)
Solr:
```xml
<fieldType name="text_ci" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.KeywordTokenizerFactory"/>
    <filter class="solr.LowerCaseFilterFactory"/>
  </analyzer>
</fieldType>
```
OpenSearch:
```json
{
  "analysis": {
    "normalizer": {
      "lowercase_normalizer": {
        "type": "custom",
        "filter": ["lowercase"]
      }
    }
  }
}
```
Note: For keyword-like behavior with case folding, use a `normalizer` on a `keyword` field rather than a text analyzer. This preserves exact-match semantics.

### 10. Synonym handling with SolrSynonymParser format
Solr:
```xml
<filter class="solr.SynonymGraphFilterFactory" synonyms="synonyms.txt"
        format="solr" expand="true"/>
```
OpenSearch:
```json
{ "type": "synonym_graph", "synonyms_path": "synonyms.txt", "expand": true }
```
Note: OpenSearch supports the Solr synonym file format natively. The `expand` parameter works the same way. Always apply synonym filters at query time, not index time, unless you have a specific reason (reindex cost).

## Dynamic Fields

Solr `dynamicField` rules map to OpenSearch `dynamic_templates`:

Solr:
```xml
<dynamicField name="*_s" type="string" indexed="true" stored="true"/>
<dynamicField name="*_txt" type="text_general" indexed="true" stored="true"/>
<dynamicField name="*_i" type="pint" indexed="true" stored="true"/>
```

OpenSearch:
```json
{
  "dynamic_templates": [
    { "strings": { "match": "*_s", "mapping": { "type": "keyword" } } },
    { "texts": { "match": "*_txt", "mapping": { "type": "text", "analyzer": "text_general_index", "search_analyzer": "text_general_search" } } },
    { "integers": { "match": "*_i", "mapping": { "type": "integer" } } }
  ]
}
```

## copyField

Solr `copyField` directives map to OpenSearch `copy_to` on the source field:

Solr:
```xml
<copyField source="title" dest="text"/>
<copyField source="description" dest="text"/>
```

OpenSearch:
```json
{
  "properties": {
    "title": { "type": "text", "copy_to": "text" },
    "description": { "type": "text", "copy_to": "text" },
    "text": { "type": "text" }
  }
}
```
Note: Unlike Solr where `copyField` is declared globally, OpenSearch `copy_to` is declared per-field. Multi-target copy (one source → multiple destinations) uses an array: `"copy_to": ["text", "all_fields"]`.
