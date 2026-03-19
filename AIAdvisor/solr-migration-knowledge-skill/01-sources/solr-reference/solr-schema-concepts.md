# Solr Schema Design: Reference Guide for Engineers

## Table of Contents
1. [Schema Structure](#schema-structure)
2. [Field Types](#field-types)
3. [TextField: Analyzers & Filters](#textfield-analyzers--filters)
4. [Field Attributes](#field-attributes)
5. [SchemaAPI vs Static Schema](#schemaapi-vs-static-schema)
6. [Dynamic Field Patterns](#dynamic-field-patterns)
7. [CopyField Use Cases](#copyfield-use-cases)
8. [Nested Documents](#nested-documents)
9. [docValues vs Inverted Index](#docvalues-vs-inverted-index)
10. [Common Schema Anti-Patterns & Fixes](#common-schema-anti-patterns--fixes)

---

## Schema Structure

A Solr schema defines how documents are indexed and searched. It's stored in `schema.xml` (or managed via Schema API) and resides in ZooKeeper for SolrCloud.

### Basic Elements

#### fieldType

Defines how a field is indexed, stored, and queried. Reusable across multiple fields.

```xml
<fieldType name="string" class="solr.StrField" />

<fieldType name="text_general" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
  </analyzer>
</fieldType>
```

#### field

Declares a specific field with a type and attributes.

```xml
<field name="id" type="string" indexed="true" stored="true" required="true" />
<field name="title" type="text_general" indexed="true" stored="true" />
<field name="price" type="float" indexed="true" stored="true" />
```

#### dynamicField

Wildcard pattern matching multiple fields to a shared type.

```xml
<dynamicField name="*_s" type="string" indexed="true" stored="true" />
<dynamicField name="*_t" type="text_general" indexed="true" stored="true" />
<dynamicField name="*_i" type="int" indexed="true" stored="true" />
```

Incoming field `color_s` automatically becomes `string` type; `description_t` becomes `text_general`.

#### copyField

Copies the value of one field to another during indexing.

```xml
<copyField source="title" dest="_text_" />
<copyField source="description" dest="_text_" />
```

Searchable "catch-all" field that combines multiple source fields.

#### uniqueKey

The field that uniquely identifies each document. Required for updates and atomic operations.

```xml
<uniqueKey>id</uniqueKey>
```

---

## Field Types

### String & Keyword Types

#### StrField
Unanalyzed string; stored as-is, indexed as single token.

```xml
<fieldType name="string" class="solr.StrField" />
```

**Use for:**
- IDs, SKUs, product codes
- Exact-match filters (category, status)
- Faceting (very fast; no analysis overhead)
- Sorting (strings sort alphabetically)

**Searchability:** Only exact matches; `query=brand:Coleman` matches only if brand field is exactly "Coleman".

#### StrField with Optional Docvalues
```xml
<fieldType name="string" class="solr.StrField" docValues="true" />
```

Enables faceting and sorting without stored values; saves memory.

### Numeric Field Types

#### IntPointField, LongPointField
Integers, indexed as points for range and spatial queries.

```xml
<fieldType name="int" class="solr.IntPointField" />
<fieldType name="long" class="solr.LongPointField" />
```

**Use for:**
- Inventory counts, ratings
- Date representations (milliseconds since epoch)
- Any numeric filter or range query
- Sorting by numeric value

#### FloatPointField, DoublePointField
Floating-point numbers.

```xml
<fieldType name="float" class="solr.FloatPointField" />
<fieldType name="double" class="solr.DoublePointField" />
```

**Use for:**
- Prices, ratings, percentages
- Geospatial coordinates (latitude, longitude)

#### Performance note: "Point" suffix
Modern Solr uses `*PointField` classes (e.g., `IntPointField` instead of deprecated `TrieIntField`). Point fields are faster for range queries and use less memory.

### Date/Time Field Types

#### DatePointField (Modern)
ISO 8601 timestamps: `2025-03-17T14:30:00Z`

```xml
<fieldType name="date" class="solr.DatePointField" />
```

**Supports:**
- Range queries: `date:[2025-01-01 TO 2025-03-17]`
- Faceting by date granularity (via range facet)
- Sorting (chronological order)

**Storage:**
- Stored in UTC
- Input accepts: `2025-03-17T14:30:00Z`, `2025-03-17T14:30:00-07:00` (with timezone)

### Boolean Field Type

#### BoolField
Accepts true/false; stored as T/F internally.

```xml
<fieldType name="boolean" class="solr.BoolField" />
```

**Use for:**
- Feature flags (in_stock, is_featured)
- Attributes requiring boolean logic

### Spatial Field Types

#### LatLonPointSpatialField (Modern)
Two-dimensional geospatial point using latitude/longitude.

```xml
<fieldType name="location" class="solr.LatLonPointSpatialField" />
```

**Storage:** `"40.7128,-74.0060"` (latitude,longitude, comma-separated)

**Queries:**
- Proximity (radius): `fq={!geofilt sfield=location pt=40.7128,-74.0060 d=10}`
- Bounding box: `fq={!bbox sfield=location minX=-74.2 maxX=-73.8 minY=40.6 maxY=40.8}`
- Distance in sort: `sort=geodist() asc`

#### RPT (Recursive Prefix Tree)
Complex geospatial queries (polygons, shapes).

```xml
<fieldType name="location_rpt" class="solr.SpatialRecursivePrefixTreeFieldType" />
```

More feature-rich but slower than LatLonPointSpatialField.

### TextField

Analyzed text field; tokenized, filtered, suitable for full-text search.

```xml
<fieldType name="text_general" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
    <filter class="solr.StopFilterFactory" ignoreCase="true" words="stopwords.txt" />
  </analyzer>
</fieldType>
```

See [TextField: Analyzers & Filters](#textfield-analyzers--filters) section for details.

---

## TextField: Analyzers & Filters

TextFields are the most complex and powerful. They process text through an analyzer chain during indexing and querying.

### Analyzer Structure

```xml
<fieldType name="text_en" class="solr.TextField">
  <analyzer type="index">
    <!-- used at index time -->
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
    <filter class="solr.StopFilterFactory" ignoreCase="true" words="stopwords.txt" />
  </analyzer>
  <analyzer type="query">
    <!-- used at query time; usually matches index analyzer -->
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
  </analyzer>
</fieldType>
```

If only one `<analyzer>` is specified (no `type` attribute), it's used for both indexing and querying.

### Tokenizers

A tokenizer splits input text into individual tokens (words).

#### StandardTokenizer
Breaks on whitespace and punctuation; handles contractions (e.g., "don't" → "don", "t").

```xml
<tokenizer class="solr.StandardTokenizerFactory" />
```

**Good for:** English text, mixed-language content, general-purpose.

#### WhitespaceTokenizer
Splits only on whitespace; keeps punctuation.

```xml
<tokenizer class="solr.WhitespaceTokenizerFactory" />
```

**Use when:**
- Text is already well-tokenized (log files, URLs)
- Preserving punctuation matters (email addresses, code)

#### PatternTokenizer
Splits on regex pattern.

```xml
<tokenizer class="solr.PatternTokenizerFactory" pattern="[,;]" />
```

Useful for semicolon-delimited or comma-delimited fields.

#### UAX29URLEmailTokenizer
Like StandardTokenizer but preserves URLs and email addresses as single tokens.

```xml
<tokenizer class="solr.UAX29URLEmailTokenizerFactory" />
```

**Use for:** Content with URLs, emails (e.g., documentation, blog posts).

### Common Filters

Filters transform tokens after tokenization.

#### LowerCaseFilter
Converts all tokens to lowercase.

```xml
<filter class="solr.LowerCaseFilterFactory" />
```

Essential for case-insensitive search (nearly all text fields).

#### StopFilter
Removes common, low-value words (stop words).

```xml
<filter class="solr.StopFilterFactory" ignoreCase="true" words="stopwords.txt" />
```

**Stopwords (language-dependent):** English (a, the, is, and, or, ...), French (le, de, et, ...), etc.

**Trade-off:** Reduces index size (~10-20%) and noise, but prevents phrase searches like "The Rolling Stones" from matching the exact phrase.

#### SynonymFilter
Expands search to include synonyms.

```xml
<filter class="solr.SynonymFilterFactory" synonyms="synonyms.txt" ignoreCase="true" expand="true" />
```

**synonyms.txt:**
```
jump, leap, bound
quick, fast, rapid
```

**expand=true:** Query "jump" matches "jump", "leap", "bound".

**expand=false:** Only at index time; doesn't expand queries.

**Performance note:** Synonym expansion increases index size and query latency.

#### EdgeNGramFilter
Creates prefix tokens; enables prefix search (type-ahead).

```xml
<filter class="solr.EdgeNGramFilterFactory" minGramSize="3" maxGramSize="20" />
```

**Input:** "camping"
**Output:** "cam", "camp", "campi", ..., "camping"

**Use for:** Autocomplete, prefix search.

**Cost:** Index size increases ~3-5x.

#### NGramFilter
Creates substring tokens; enables infix search.

```xml
<filter class="solr.NGramFilterFactory" minGramSize="3" maxGramSize="4" />
```

**Input:** "camping"
**Output:** "cam", "amp", "mpi", "pin", "ing", "camp", "ampi", "mpin", "ping"

**Cost:** Index size increases 10-20x.

#### PorterStemFilter
Reduces words to root form.

```xml
<filter class="solr.PorterStemFilterFactory" />
```

**Examples:**
- "running" → "run"
- "runs" → "run"
- "camping" → "camp" (aggressive; may lose meaning)

**Use when:** Recall (finding all variants) is more important than precision.

#### SnowballFilter
Language-aware stemming (more accurate than Porter).

```xml
<filter class="solr.SnowballFilterFactory" language="English" />
```

#### EnglishPossessiveFilter
Removes possessive 's.

```xml
<filter class="solr.EnglishPossessiveFilterFactory" />
```

**Input:** "John's camping trip"
**Output:** "John camping trip"

#### KStemFilter
Keeps/Kelvin stemming; more conservative than Porter.

```xml
<filter class="solr.KStemFilterFactory" />
```

#### RemoveDuplicatesFilter
Removes adjacent duplicate tokens (side effect of stopword removal or stemming).

```xml
<filter class="solr.RemoveDuplicatesTokenFilterFactory" />
```

**Example:**
- Before: "jumping jumping" (after stemming)
- After: "jump"

### Analyzer Examples

#### General English Search
```xml
<fieldType name="text_general" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
    <filter class="solr.StopFilterFactory" ignoreCase="true" words="stopwords.txt" />
    <filter class="solr.PorterStemFilterFactory" />
  </analyzer>
</fieldType>
```

Maximizes recall; finds all stemmed variants.

#### Exact Phrase Search (Preserve Precision)
```xml
<fieldType name="text_exact" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
    <!-- no stemming, no stopword removal -->
  </analyzer>
</fieldType>
```

Useful for title, brand, specific phrases where stemming would be destructive.

#### Autocomplete
```xml
<fieldType name="text_autocomplete" class="solr.TextField">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
    <filter class="solr.EdgeNGramFilterFactory" minGramSize="3" maxGramSize="20" />
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
  </analyzer>
</fieldType>
```

Index with edge n-grams; query without (prevents "campi" being tokenized further).

---

## Field Attributes

Critical attributes that control indexing and storage behavior.

### indexed

Whether field is indexed (searchable).

```xml
<field name="title" type="text_general" indexed="true" />
<field name="internal_notes" type="text_general" indexed="false" stored="true" />
```

- `indexed=true`: Field appears in inverted index; can be searched.
- `indexed=false`: Field is only stored, not searchable. Useful for metadata that doesn't need search.

### stored

Whether field value is stored verbatim (returned in search results).

```xml
<field name="title" type="text_general" stored="true" />
<field name="description" type="text_general" indexed="true" stored="false" />
```

- `stored=true`: Full field value returned in results; increases index size.
- `stored=false`: Not stored; you can return it from docValues, but original value is lost.

### docValues

Whether field supports fast column-oriented access (for sorting, faceting, grouping).

```xml
<field name="price" type="float" docValues="true" />
<field name="category" type="string" docValues="true" />
```

**docValues vs stored:**
- **docValues:** Optimized for aggregations (sorting, faceting, min/max). Memory-efficient. Replaces disk seeks with linear scan.
- **stored:** Returns original values in search results. Less efficient for aggregations.

**Best practice:** Use `docValues="true"` for fields you sort/facet/group. Use `stored="true"` for fields you want in results. Both are independent; you can have one, both, or neither.

### multiValued

Whether a field can have multiple values per document.

```xml
<field name="tags" type="string" multiValued="true" />
<field name="colors" type="string" multiValued="true" />
```

**Single-valued:**
```json
{ "id": "1", "tag": "outdoor" }
```

**Multi-valued:**
```json
{ "id": "1", "tags": ["outdoor", "camping", "gear"] }
```

For string fields, multiValued fields are usually faceted per value (each tag contributes one count).

### required

Whether field must be present in every document.

```xml
<field name="id" type="string" required="true" />
```

Solr validates at update time; missing required fields cause errors.

### termVectors & termPositions & termOffsets

Enable term vector storage for highlighting and more-like-this.

```xml
<field name="title" type="text_general" termVectors="true" termPositions="true" termOffsets="true" />
```

- `termVectors="true"`: Store which terms appear in each doc.
- `termPositions="true"`: Store token positions (needed for highlighting).
- `termOffsets="true"`: Store character offsets in original text (needed for accurate highlighting).

**Cost:** Increases index size ~10%. Rarely needed unless you use highlighting or MLT extensively.

### omitNorms

Exclude document length normalization from scoring.

```xml
<field name="status" type="string" omitNorms="true" />
<field name="category" type="string" omitNorms="true" />
```

**Effect:** Longer documents don't get boosted/penalized based on length. Useful for exact-match fields where length is irrelevant.

**Saves:** Memory (small impact).

### omitTermFreqAndPositions

Don't store term frequency or positions; treat field as a bag of words.

```xml
<field name="keywords" type="text_general" omitTermFreqAndPositions="true" />
```

**Effect:** Can search field, but scoring ignores frequency and proximity. Faster indexing, smaller index.

**Trade-off:** Loses phrase queries, proximity boosts for this field.

---

## SchemaAPI vs Static Schema

### Static Schema (schema.xml)

Traditional approach: schema is a file, edited offline, uploaded to ZooKeeper.

**Pros:**
- Explicit control; schema is versioned in git
- No runtime mutations; schema is stable
- Supports advanced features (custom field types with complex analyzer chains)

**Cons:**
- Requires restart or schema reload for changes
- Manual workflow: edit file → upload → reload
- Risky if multiple team members edit simultaneously

**Deployment:**
```bash
solr zk upconfig -z zk1:2181 -n my_config -d /path/to/config
POST /admin/collections?action=RELOAD&name=mycol
```

### Managed Schema (SchemaAPI)

Modern approach: schema is managed via REST API; Solr applies changes dynamically.

**Pros:**
- No restart needed; changes are live within seconds
- Easy for discovery workflows (auto-creating fields as they're encountered)
- Dynamic field expansion: POST unknown field, Solr creates it

**Cons:**
- Schema can diverge (hard to audit)
- Complex analyzer chains must still be manually created
- Risk of unintended field creation if not gated

**Enabling managed schema:**
```xml
<schemaFactory class="solr.ManagedIndexSchemaFactory">
  <bool name="mutable">true</bool>
  <str name="managedSchemaResourceName">managed-schema</str>
</schemaFactory>
```

**SchemaAPI endpoints:**

```bash
# Get current schema
curl http://localhost:8983/solr/mycol/schema

# Add a field
POST /solr/mycol/schema/fields
{ "name": "new_field", "type": "text_general", "indexed": true, "stored": true }

# Modify a field
PUT /solr/mycol/schema/fields/new_field
{ "type": "string" }

# Delete a field
DELETE /solr/mycol/schema/fields/new_field

# Add a field type (complex; requires JSON definition)
POST /solr/mycol/schema/fieldTypes
{ "name": "my_custom_type", "class": "solr.TextField", ... }
```

### Hybrid Approach

Manage core schema (`schema.xml`) statically; use SchemaAPI for field-level changes.

```xml
<schemaFactory class="solr.ManagedIndexSchemaFactory">
  <bool name="mutable">true</bool>
  <str name="managedSchemaResourceName">managed-schema</str>
</schemaFactory>
```

Then:
1. Define all field types in `schema.xml` (complex analyzer chains)
2. Use SchemaAPI to add/modify fields as needed
3. Version control the base schema.xml, generated managed-schema is ZK-only

---

## Dynamic Field Patterns

Dynamic fields use wildcard patterns to auto-assign types. Reduces schema bloat for large, flexible datasets.

### Common Patterns

#### *_s (string)
```xml
<dynamicField name="*_s" type="string" indexed="true" stored="true" />
```

Any field ending in `_s` is automatically a `string` type.

**Examples:** `color_s`, `brand_s`, `status_s`

#### *_t (text)
```xml
<dynamicField name="*_t" type="text_general" indexed="true" stored="true" />
```

Any field ending in `_t` is a full-text `text` field.

**Examples:** `title_t`, `description_t`, `content_t`

#### *_i (integer)
```xml
<dynamicField name="*_i" type="int" indexed="true" stored="true" />
```

**Examples:** `quantity_i`, `rating_i`, `year_i`

#### *_l (long)
```xml
<dynamicField name="*_l" type="long" indexed="true" stored="true" />
```

For large integers (milliseconds timestamps, IDs).

#### *_f (float)
```xml
<dynamicField name="*_f" type="float" indexed="true" stored="true" />
```

**Examples:** `price_f`, `rating_f`, `score_f`

#### *_d (double)
```xml
<dynamicField name="*_d" type="double" indexed="true" stored="true" />
```

Higher precision than float.

#### *_b (boolean)
```xml
<dynamicField name="*_b" type="boolean" indexed="true" stored="true" />
```

**Examples:** `in_stock_b`, `featured_b`

#### *_dt (date)
```xml
<dynamicField name="*_dt" type="date" indexed="true" stored="true" />
```

**Examples:** `publish_date_dt`, `created_dt`, `modified_dt`

#### *_ss (string, searchable, no analysis)
```xml
<dynamicField name="*_ss" type="string" indexed="true" stored="true" />
```

Distinguishes from `*_s` if you want different storage behavior.

#### *_is (integer, stored only)
```xml
<dynamicField name="*_is" type="int" indexed="false" stored="true" />
```

Useful for dimensions or metadata that don't need search.

### Pattern Ordering

Dynamic field matching is first-match-wins. Order patterns by specificity.

```xml
<!-- More specific patterns first -->
<dynamicField name="*_exact_s" type="string" indexed="true" stored="true" />

<!-- Generic patterns last -->
<dynamicField name="*_s" type="string" indexed="true" stored="true" />
<dynamicField name="*" type="text_general" indexed="true" stored="true" />
```

If an incoming field matches multiple patterns, the first match is used.

---

## CopyField Use Cases

copyField copies field values during indexing, enabling multiple index strategies for a single piece of content.

### Catch-All Field (_text_)

Combine multiple fields into a single searchable field.

```xml
<field name="_text_" type="text_general" indexed="true" stored="false" />
<copyField source="title" dest="_text_" />
<copyField source="description" dest="_text_" />
<copyField source="tags" dest="_text_" />
<copyField source="reviews" dest="_text_" />
```

Query `q=camping` searches all copied fields simultaneously. Useful for unified search where you don't care which field matches.

**Performance:** Single query on `_text_` is faster than multiple field searches with OR logic.

### Boosted Copies

Store the same content in two fields with different analyzers, creating a "boosted copy."

```xml
<field name="title" type="text_general" indexed="true" stored="true" />
<field name="title_exact" type="text_exact" indexed="true" stored="false" />
<copyField source="title" dest="title_exact" />
```

Then in query:
```
q=camping&qf=title^2 title_exact^4 description
```

Titles are searched twice: once with stemming (title), once without (title_exact). If the exact phrase matches, it gets boosted.

**Cost:** Index size increases for the copied field.

### Multi-Language Copies

Different analyzers for different languages.

```xml
<copyField source="content" dest="content_en" />
<copyField source="content" dest="content_fr" />
<copyField source="content" dest="content_es" />

<fieldType name="text_en" class="solr.TextField">
  <!-- English analyzer -->
</fieldType>
<fieldType name="text_fr" class="solr.TextField">
  <!-- French analyzer -->
</fieldType>
<!-- etc. -->
```

Index once; search language-specific copy for correct stemming/stopwords.

---

## Nested Documents

Nested documents allow hierarchical relationships in the index (e.g., products with reviews, posts with comments).

### Index-Time Structure

Documents with nested children are indexed as a single "block" or "family."

```json
POST /update
{
  "add": {
    "doc": {
      "id": "product-1",
      "type": "product",
      "title": "Tent",
      "price": 150,
      "_childDocuments_": [
        { "id": "review-1", "type": "review", "rating": 5, "text": "Great!" },
        { "id": "review-2", "type": "review", "rating": 4, "text": "Good" }
      ]
    }
  }
}
```

Or via XML:
```xml
<doc>
  <field name="id">product-1</field>
  <field name="type">product</field>
  <field name="title">Tent</field>
  <doc>
    <field name="id">review-1</field>
    <field name="type">review</field>
    <field name="rating">5</field>
  </doc>
  <doc>
    <field name="id">review-2</field>
    <field name="type">review</field>
    <field name="rating">4</field>
  </doc>
</doc>
```

### Schema Configuration

Declare the parent type:

```xml
<field name="type" type="string" indexed="true" stored="true" />
```

Children inherit all fields; no special schema declaration needed.

### Querying Nested Documents

#### toParent Query

Find parents where any child matches criteria.

```
q={!parent which="type:product"}rating:5
```

Returns product docs where at least one review has rating=5.

#### toChild Query

Find children where parent matches criteria.

```
q={!child parentFilter="price:[100 TO 300]"}rating:4
```

Returns review docs (children) whose parent product is priced 100-300 and review has rating >= 4.

### Cost & Tradeoff

**Pros:**
- Single index for related entities; no separate join
- Atomic updates (entire family updates or rolls back together)
- Explicit hierarchy in the index

**Cons:**
- Modifying one child requires re-indexing entire family
- Complex queries (toParent/toChild) have overhead
- Lucene Scorer complexity increases

---

## docValues vs Inverted Index

Two different indexing structures serve different query patterns. Understanding when to use each is critical for schema design.

### Inverted Index (Traditional Full-Text Index)

Maps terms to documents.

```
Term → [DocID1, DocID2, DocID3, ...]
```

**When to use:**
- Full-text search (find all docs containing a term)
- Boolean queries (AND, OR, NOT)
- Phrase queries ("camping gear")
- Filtering (exact-match filters)

**Example:** Index field "title" with StandardTokenizer, analyze it to find "camping" in all docs.

### DocValues (Column-Oriented Store)

Maps documents to field values.

```
DocID → FieldValue
```

**When to use:**
- Sorting (sort by price ascending)
- Faceting (group by category, count each)
- Grouping (group by brand)
- Min/max aggregations
- Scoring functions (boost by popularity)

**Example:** Field "price" with docValues=true allows sorting 1M docs by price without scanning inverted index.

### Performance Implications

#### Faceting without docValues

```xml
<field name="category" type="string" indexed="true" docValues="false" />
```

Solr must iterate inverted index (term → docs) to count documents per category. Slow for high-cardinality fields (many unique values).

#### Faceting with docValues

```xml
<field name="category" type="string" indexed="true" docValues="true" />
```

Solr iterates docValues (doc → value) and counts in memory. Much faster.

#### Sorting without docValues

Solr must fetch stored values for each matching document and sort in-memory. For 100K results, this requires 100K disk seeks.

#### Sorting with docValues

Values are already in memory (or cached); linear scan. 10-100x faster.

### Hybrid Approach

```xml
<field name="category" type="string" indexed="true" stored="false" docValues="true" />
```

- Use inverted index for filtering/searching
- Use docValues for faceting/sorting
- Don't store; saves space; values are retrieved from docValues when needed

**Best practice:** For any field you facet or sort, add `docValues="true"`.

---

## Common Schema Anti-Patterns & Fixes

### Anti-Pattern 1: Storing Raw Text with No Analysis

```xml
<field name="content" type="text_general" indexed="true" stored="true" />
```

**Problem:** Text is analyzed (lowercased, stemmed), so original case/form is lost. If you need exact reconstruction, the analyzer has destroyed information.

**Fix:**
```xml
<field name="content" type="text_general" indexed="true" stored="false" />
<field name="content_original" type="string" indexed="false" stored="true" />
<copyField source="content_original" dest="content" />
```

Or, for exact phrase search, add a copy with minimal analysis:
```xml
<field name="content_exact" type="text_exact" indexed="true" stored="false" />
<copyField source="content" dest="content_exact" />
```

### Anti-Pattern 2: Too Many Fields Stored

```xml
<field name="description" type="text_general" indexed="true" stored="true" />
<field name="reviews" type="text_general" indexed="true" stored="true" />
<field name="metadata" type="text_general" indexed="true" stored="true" />
```

**Problem:** Stored fields increase heap memory and response size. For 10M docs with 5 stored text fields, each 500 bytes, storage is 25GB.

**Fix:** Store only fields you actually return in results. Use `indexed=true, stored=false` for aggregation-only fields.

```xml
<field name="description" type="text_general" indexed="true" stored="true" />
<field name="reviews_text" type="text_general" indexed="true" stored="false" docValues="true" />
<!-- Don't store reviews; users don't request them -->
```

### Anti-Pattern 3: Missing docValues for Faceting

```xml
<field name="brand" type="string" indexed="true" />
<!-- facet.field=brand in query -->
```

**Problem:** Faceting is slow because Solr must iterate inverted index for every request.

**Fix:** Add `docValues="true"`.

```xml
<field name="brand" type="string" indexed="true" docValues="true" />
```

### Anti-Pattern 4: Incorrect Field Type for Numeric Data

```xml
<field name="price" type="text_general" indexed="true" stored="true" />
```

**Problem:** Price is analyzed as text; queries like `price:[10 TO 100]` don't work; sorting is lexicographic (9 > 100).

**Fix:** Use correct numeric type.

```xml
<field name="price" type="float" indexed="true" stored="true" docValues="true" />
```

### Anti-Pattern 5: Over-Aggressive Stemming

```xml
<fieldType name="text_general" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.PorterStemFilterFactory" />
  </analyzer>
</fieldType>
```

**Problem:** "Stemming" can be too aggressive. Example: "camping" → "camp"; "camper" → "camp". User searches "camping" and gets results about campers (unintended).

**Fix:** Use less aggressive stemmer (KStem, Snowball) or apply synonyms carefully.

```xml
<filter class="solr.KStemFilterFactory" />
```

Or skip stemming for brand/product names:
```xml
<field name="product_name" type="text_exact" indexed="true" stored="true" />
<fieldType name="text_exact" class="solr.TextField">
  <analyzer>
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.LowerCaseFilterFactory" />
    <!-- no stemming -->
  </analyzer>
</fieldType>
```

### Anti-Pattern 6: Using EdgeNGram for Every Field

```xml
<dynamicField name="*_t" type="text_with_edgengram" indexed="true" stored="true" />
<fieldType name="text_with_edgengram" class="solr.TextField">
  <analyzer>
    <filter class="solr.EdgeNGramFilterFactory" minGramSize="3" maxGramSize="20" />
  </analyzer>
</fieldType>
```

**Problem:** EdgeNGram inflates index size 3-5x. Only useful if you need prefix search; wasteful otherwise.

**Fix:** Use EdgeNGram only for autocomplete fields:

```xml
<field name="title" type="text_general" indexed="true" stored="true" />
<field name="title_autocomplete" type="text_autocomplete" indexed="true" stored="false" />
<copyField source="title" dest="title_autocomplete" />

<fieldType name="text_autocomplete" class="solr.TextField">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory" />
    <filter class="solr.EdgeNGramFilterFactory" minGramSize="3" maxGramSize="20" />
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory" />
  </analyzer>
</fieldType>
```

---

## Summary for Migration

**Schema design strengths:**
- Rich analyzer chains; fine-grained control over tokenization and filtering
- Dynamic fields reduce boilerplate for large, flexible schemas
- CopyField and nested documents support complex data structures elegantly
- docValues enable efficient aggregations without sacrificing search quality

**Key differences from OpenSearch:**
- Solr schema is more explicit; OpenSearch mapping is more implicit
- analyzers in Solr are declarative XML; in OpenSearch, they're JSON with slightly different syntax
- Nested documents work differently (Solr uses block join; OpenSearch uses nested type with different query syntax)
- Dynamic fields are Solr-specific; OpenSearch relies on dynamic mapping

For migration, prioritize:
1. Are your analyzer chains critical (custom stemming, synonym expansion)?
2. Do you rely on nested documents?
3. Which fields must support faceting/sorting (these need docValues analysis)?
