# Index Design: Solr to OpenSearch Migration

When advising on index design migration, use these mappings and patterns.
Flag any conversion you are uncertain about rather than guessing.

## Field Type Mapping

### Primitive Types

| Solr Type | OpenSearch Type | Notes |
|-----------|----------------|-------|
| `solr.StrField` / `string` | `keyword` | Exact match, no analysis |
| `solr.IntPointField` / `int` | `integer` | 32-bit signed |
| `solr.LongPointField` / `long` | `long` | 64-bit signed |
| `solr.FloatPointField` / `float` | `float` | 32-bit IEEE 754 |
| `solr.DoublePointField` / `double` | `double` | 64-bit IEEE 754 |
| `solr.BoolField` / `boolean` | `boolean` | |
| `solr.DatePointField` / `pdate` | `date` | ISO 8601 format |
| `pdates` (multi-valued date) | `date` (array) | No mapping change needed |

### Text Types

| Solr Type | OpenSearch Strategy |
|-----------|---------------------|
| `text_general` | `text` with `standard` analyzer |
| `text_en` | `text` with custom English analyzer (stemmer + stopwords) |
| `text_ws` | `text` with `whitespace` tokenizer |
| `text_ja` / CJK types | `text` with `kuromoji` / `cjk_bigram` (requires analysis plugin) |
| Custom analyzed types | `text` with equivalent custom analyzer in index settings |

### Specialized Types

| Solr Type | OpenSearch Type | Notes |
|-----------|----------------|-------|
| `solr.LatLonPointSpatialField` / `location` | `geo_point` | Accepts `"lat,lon"` or object |
| `solr.SpatialRecursivePrefixTreeFieldType` | `geo_shape` | For polygons, complex spatial |
| `binary` | `binary` | Rare |
| `currency` | `scaled_float` or `float` | Apply exchange rates at query time |

### Deprecated Trie Types

If the Solr schema uses `TrieIntField`, `TrieLongField`, `TrieFloatField`, `TrieDoubleField`, or `TrieDateField`, map them the same as their Point equivalents above. Note that the Solr schema is using deprecated types and recommend the migration as an opportunity to modernize.

## Field Properties

| Solr Property | OpenSearch Equivalent | Default Behavior |
|---------------|----------------------|------------------|
| `indexed="true"` | `index: true` | Default for all searchable types |
| `indexed="false"` | `index: false` | Explicitly disable |
| `stored="true"` | Present in `_source` | Default; `_source` returns all fields |
| `stored="false"` | `store: false` | Field still in `_source` unless excluded |
| `docValues="true"` | `doc_values: true` | **Default for keyword, numeric, date, boolean, geo_point** |
| `docValues="false"` | `doc_values: false` | Must explicitly disable |
| `multiValued="true"` | No mapping needed | Arrays are native in OpenSearch |
| `required="true"` | No equivalent | Validate in application or ingest pipeline |
| `omitNorms="true"` | `norms: false` | Disable length normalization |
| `termVectors="true"` | `term_vector: "with_positions_offsets"` | Needed for fast-vector highlighting |

### docValues Behavior Difference

Solr: `docValues` defaults to `false` for most types; you must explicitly enable it.
OpenSearch: `doc_values` defaults to `true` for `keyword`, all numeric types, `date`, `boolean`, `ip`, and `geo_point`. Only `text` fields lack doc_values by default.

**Migration impact**: Most Solr schemas that explicitly set `docValues="true"` on keyword/numeric fields need no special handling -- OpenSearch already enables it. Schemas that set `docValues="false"` on these types need explicit `"doc_values": false` in OpenSearch.

## Analyzer Chain Translation

### Structure Mapping

- Solr: Analyzers defined in `<fieldType>` XML, applied via `type="fieldTypeName"`
- OpenSearch: Analyzers defined in `settings.analysis`, referenced by name in field mappings
- Solr `<analyzer type="index">` maps to OpenSearch `"analyzer"`
- Solr `<analyzer type="query">` maps to OpenSearch `"search_analyzer"`
- A single Solr `<analyzer>` (no type) maps to a single OpenSearch `"analyzer"` (used for both)

### Tokenizer Mapping

| Solr Tokenizer | OpenSearch Equivalent |
|----------------|----------------------|
| `solr.StandardTokenizerFactory` | `standard` |
| `solr.WhitespaceTokenizerFactory` | `whitespace` |
| `solr.KeywordTokenizerFactory` | `keyword` |
| `solr.PatternTokenizerFactory` | `pattern` |
| `solr.UAX29URLEmailTokenizerFactory` | `uax_url_email` |
| `solr.PathHierarchyTokenizerFactory` | `path_hierarchy` |
| `solr.EdgeNGramTokenizerFactory` | `edge_ngram` |
| `solr.NGramTokenizerFactory` | `ngram` |

### Filter Mapping

| Solr Filter | OpenSearch Equivalent |
|-------------|----------------------|
| `LowerCaseFilterFactory` | `lowercase` |
| `UpperCaseFilterFactory` | `uppercase` |
| `StopFilterFactory` | `stop` |
| `PorterStemFilterFactory` | `porter_stem` |
| `SnowballFilterFactory` | `snowball` |
| `KStemFilterFactory` | `kstem` |
| `SynonymFilterFactory` | `synonym` |
| `SynonymGraphFilterFactory` | `synonym_graph` (preferred) |
| `EdgeNGramFilterFactory` | `edge_ngram` |
| `NGramFilterFactory` | `ngram` |
| `ShingleFilterFactory` | `shingle` |
| `TrimFilterFactory` | `trim` |
| `RemoveDuplicatesTokenFilterFactory` | `remove_duplicates` |
| `EnglishPossessiveFilterFactory` | `stemmer` with `language: "possessive_english"` |
| `WordDelimiterFilterFactory` | `word_delimiter` |
| `WordDelimiterGraphFilterFactory` | `word_delimiter_graph` (preferred) |
| `LengthFilterFactory` | `length` |
| `ASCIIFoldingFilterFactory` | `asciifolding` |

### Character Filter Mapping

| Solr Char Filter | OpenSearch Equivalent |
|------------------|----------------------|
| `HTMLStripCharFilterFactory` | `html_strip` |
| `MappingCharFilterFactory` | `mapping` |
| `PatternReplaceCharFilterFactory` | `pattern_replace` |

### Example: Asymmetric Analyzer (Index vs Query)

Solr pattern where index-time uses stemming but query-time does not:

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "text_en_index": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop", "porter_stem"]
        },
        "text_en_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stop"]
        }
      },
      "filter": {
        "english_stop": { "type": "stop", "stopwords": "_english_" }
      }
    }
  },
  "mappings": {
    "properties": {
      "description": {
        "type": "text",
        "analyzer": "text_en_index",
        "search_analyzer": "text_en_query"
      }
    }
  }
}
```

### Synonym and Stopword Files

Solr references files like `synonyms.txt` and `stopwords.txt` from the configset directory. In OpenSearch, these must be either:
- Inlined in the analyzer definition (small lists)
- Placed in `config/analysis/` on each node and referenced by path
- Managed via the `_analyze` API for validation before deployment

## copyField to copy_to

Solr `copyField` directives become `copy_to` on source fields:

```xml
<!-- Solr -->
<copyField source="title" dest="search_text"/>
<copyField source="body" dest="search_text"/>
```

```json
// OpenSearch
"title": { "type": "text", "copy_to": "search_text" },
"body":  { "type": "text", "copy_to": "search_text" },
"search_text": { "type": "text", "store": false }
```

Key differences:
- Solr `copyField` can use wildcards (`source="*_t"`); OpenSearch `copy_to` is per-field only
- OpenSearch `copy_to` target field must be declared in mappings
- `copy_to` fields are not in `_source` by default -- they are index-only

## Dynamic Fields to Dynamic Templates

Solr dynamic fields (`*_s`, `*_i`) map to OpenSearch `dynamic_templates`:

```json
{
  "mappings": {
    "dynamic_templates": [
      { "strings":  { "match": "*_s",  "mapping": { "type": "keyword" } } },
      { "text":     { "match": "*_t",  "mapping": { "type": "text", "analyzer": "standard" } } },
      { "integers": { "match": "*_i",  "mapping": { "type": "integer" } } },
      { "longs":    { "match": "*_l",  "mapping": { "type": "long" } } },
      { "floats":   { "match": "*_f",  "mapping": { "type": "float" } } },
      { "doubles":  { "match": "*_d",  "mapping": { "type": "double" } } },
      { "booleans": { "match": "*_b",  "mapping": { "type": "boolean" } } },
      { "dates":    { "match": "*_dt", "mapping": { "type": "date" } } },
      { "geopoints":{ "match": "*_ll", "mapping": { "type": "geo_point" } } }
    ]
  }
}
```

Key differences:
- Solr: first-match-wins ordering; OpenSearch: same (template order matters)
- OpenSearch templates support `match_pattern: "regex"` for complex patterns
- Recommend `"dynamic": "strict"` in production to prevent unintended field creation

## Nested / Child Documents

### Solr Block Join vs OpenSearch Nested

| Aspect | Solr | OpenSearch |
|--------|------|------------|
| Storage | Children in `_childDocuments_` array, flat index | Children in `nested` typed field, hidden docs |
| Query syntax | `{!parent which="type:parent"}child_field:val` | `{ "nested": { "path": "comments", "query": {...} } }` |
| Update granularity | Must re-index entire block | Must re-index entire document |
| Cross-level scoring | `score=total\|avg\|max\|min` in block join | `score_mode` in nested query |
| Max depth | Flat parent/child only | Arbitrary nesting depth |

### Migration Pattern

Solr block join with `_childDocuments_` becomes a `nested` field type:

```json
{
  "mappings": {
    "properties": {
      "comments": {
        "type": "nested",
        "properties": {
          "author": { "type": "keyword" },
          "text": { "type": "text" }
        }
      }
    }
  }
}
```

### When to Use join Instead

If the Solr schema has parent/child relationships that update independently (rare in Solr), consider OpenSearch `join` field type. However, `join` has severe performance costs -- prefer `nested` or denormalization for most cases.

## uniqueKey to _id

Solr `<uniqueKey>id</uniqueKey>` maps to OpenSearch `_id`. When indexing, pass the Solr unique key as the document ID: `PUT /index/_doc/{id}`. Store it as a `keyword` field too if the application queries by it.

## Anti-Patterns to Flag

### 1. Text Field Used for Exact Match
Solr `string` field migrated as `text` instead of `keyword`. Symptoms: faceting fails or returns tokenized fragments.
**Fix**: Map `solr.StrField` to `keyword`, not `text`.

### 2. Missing Analyzer Translation
Custom Solr analyzer chain dropped during migration, field falls back to `standard` analyzer. Symptoms: search recall/precision changes.
**Fix**: Translate every custom `<fieldType>` analyzer chain to OpenSearch `settings.analysis`.

### 3. Unnecessary doc_values Disable
Solr schema had no `docValues` (pre-default era), migrator explicitly sets `"doc_values": false`. Symptoms: sorting and aggregations fail.
**Fix**: Let OpenSearch defaults apply. Only set `"doc_values": false` if the Solr schema explicitly disabled them.

### 4. copyField Wildcard Not Migrated
Solr `<copyField source="*_t" dest="_text_"/>` silently dropped because OpenSearch `copy_to` does not support wildcards.
**Fix**: Either add `copy_to` to each matched field, or use an ingest pipeline with a script processor.

### 5. Nested Documents Flattened
Solr `_childDocuments_` converted to flat object arrays. Symptoms: cross-object matches (searching for author=A AND text=B matches when author=A is on one comment and text=B on another).
**Fix**: Use `nested` type, not default `object` type, when field isolation matters.

### 6. EdgeNGram Applied Globally
Solr autocomplete analyzer applied to all `*_t` dynamic fields. Symptoms: massive index bloat (3-5x).
**Fix**: Restrict edge_ngram to dedicated autocomplete fields via `copy_to`.

### 7. Synonym File Not Deployed
Solr `synonyms.txt` referenced but not placed on OpenSearch nodes. Symptoms: index creation fails or synonyms silently ignored.
**Fix**: Deploy synonym/stopword files to all data nodes before index creation.

### 8. Trie Field Types Not Updated
Deprecated `Trie*Field` types mapped without noting they are obsolete. Not a functional problem, but a missed opportunity.
**Fix**: Note deprecated types in the migration report; map to standard OpenSearch equivalents.
