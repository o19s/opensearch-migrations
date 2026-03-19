# Solr to OpenSearch Migration Skill

An **OpenSearch Agent Skill** that helps migrate from [Apache Solr](https://solr.apache.org/) to [OpenSearch](https://opensearch.org/).

## Good example prompts

* "Help me migrate from Solr to OpenSearch."
* "Convert this Solr schema to OpenSearch mapping: <schema>...</schema>"
* "Translate this Solr query to OpenSearch: title:opensearch AND price:[10 TO 100]"
* "Create a migration report for my Solr setup."

## Features

| Capability | Method | Description |
|---|---|---|
| Schema conversion (XML) | `convert_schema_xml()` | Converts a Solr `schema.xml` file to an OpenSearch index mapping |
| Schema conversion (JSON) | `convert_schema_json()` | Converts a Solr Schema API JSON response to an OpenSearch index mapping |
| Query conversion | `convert_query()` | Translates a Solr query string to an OpenSearch Query DSL JSON object |
| Migration checklist | `get_migration_checklist()` | Returns a human-readable migration checklist |
| Field type reference | `get_field_type_mapping_reference()` | Returns a Markdown table of Solr → OpenSearch type mappings |

## Supported Solr → OpenSearch Field Type Mappings

| Solr Field Type | OpenSearch Type |
|---|---|
| `StrField` | `keyword` |
| `TextField` | `text` |
| `IntPointField` / `TrieIntField` | `integer` |
| `LongPointField` / `TrieLongField` | `long` |
| `FloatPointField` / `TrieFloatField` | `float` |
| `DoublePointField` / `TrieDoubleField` | `double` |
| `DatePointField` / `TrieDateField` | `date` |
| `BoolField` | `boolean` |
| `BinaryField` | `binary` |
| `LatLonPointSpatialField` | `geo_point` |
| `SpatialRecursivePrefixTreeFieldType` | `geo_shape` |

## Supported Solr Query Conversions

| Solr Query Pattern | OpenSearch Query DSL |
|---|---|
| `*:*` | `match_all` |
| `field:value` | `match` |
| `field:"phrase value"` | `match_phrase` |
| `field:val*` / `field:*val` | `wildcard` |
| `field:[low TO high]` | `range` (inclusive) |
| `field:{low TO high}` | `range` (exclusive) |
| `field:[* TO high]` / `field:[low TO *]` | open-ended `range` |
| `term1 AND term2` | `bool` / `must` |
| `term1 OR term2` | `bool` / `should` |
| `NOT term` | `bool` / `must_not` |
| `+term1 -term2` | `bool` / `must` + `must_not` |
| bare term | `query_string` (fallback) |

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```python
import sys
import os
# Add scripts directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "scripts"))

from skill import SolrToOpenSearchMigrationSkill

skill = SolrToOpenSearchMigrationSkill()

# --- Schema conversion ---

# From schema.xml
with open("schema.xml") as f:
    mapping_json = skill.convert_schema_xml(f.read())
print(mapping_json)

# From Solr Schema API JSON (GET /solr/<collection>/schema)
import urllib.request
with urllib.request.urlopen("http://localhost:8983/solr/mycore/schema") as resp:
    schema_api_json = resp.read().decode()
mapping_json = skill.convert_schema_json(schema_api_json)
print(mapping_json)

# --- Query conversion ---
dsl = skill.convert_query("title:opensearch AND category:docs")
print(dsl)

# Range query
dsl = skill.convert_query("price:[10 TO 100]")
print(dsl)

# --- Migration guidance ---
print(skill.get_migration_checklist())
print(skill.get_field_type_mapping_reference())
```

### Example: Convert a schema.xml

Given a Solr `schema.xml`:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<schema name="products" version="1.6">
  <fieldType name="string" class="solr.StrField" />
  <fieldType name="text_general" class="solr.TextField" />
  <fieldType name="pint" class="solr.IntPointField" />
  <fieldType name="pfloat" class="solr.FloatPointField" />
  <fieldType name="pdate" class="solr.DatePointField" />

  <field name="id"          type="string"       indexed="true"  stored="true" required="true" />
  <field name="name"        type="text_general" indexed="true"  stored="true" />
  <field name="price"       type="pfloat"       indexed="true"  stored="true" />
  <field name="quantity"    type="pint"         indexed="true"  stored="true" />
  <field name="created_at"  type="pdate"        indexed="true"  stored="true" />

  <dynamicField name="*_s" type="string" indexed="true" stored="true" />
</schema>
```

The skill produces:

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": { "type": "text" },
      "price": { "type": "float" },
      "quantity": { "type": "integer" },
      "created_at": { "type": "date" }
    },
    "dynamic_templates": [
      {
        "dynamic_s": {
          "match": "*_s",
          "match_pattern": "wildcard",
          "mapping": { "type": "keyword" }
        }
      }
    ]
  }
}
```

### Example: Convert a Solr query

```python
skill.convert_query("title:opensearch AND price:[10 TO 100]")
```

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "opensearch" } },
        { "range": { "price": { "gte": 10, "lte": 100 } } }
      ]
    }
  }
}
```

## Running the Tests

```bash
cd solr-to-opensearch
pip install -e ".[dev]"
pytest
```

## Project Structure

```
solr-to-opensearch/
├── pyproject.toml
├── requirements-dev.txt
├── README.md
├── SKILL.md
└── scripts/
    ├── __init__.py
    ├── skill.py             # High-level SolrToOpenSearchMigrationSkill class
    ├── schema_converter.py  # Solr schema → OpenSearch mapping converter
    └── query_converter.py   # Solr query syntax → OpenSearch Query DSL converter
```

## Example Solr IMDB queries

* q=primaryTitle:Inception
* q=primaryTitle:Batman AND genres:Action
* q=titleType:tvSeries
* q=*:*&fq=startYear:[2010 TO 2020]
* q=genres:Sci-Fi&sort=startYear desc

```
defType=edismax
&q=Christopher Nolan Sci-Fi
&qf=primaryTitle^10 originalTitle^5 directors^2 genres^1
&pf=primaryTitle^20
&tie=0.1
&bq=averageRating:[8 TO 10]^5
```

## Example Solr Cluster Config

1. SolrCloud with 3 nodes, 2 shards, 2 replicas per shard
2. 40 million documents
3. 50 QPS
4. Indexing rate is 5,000 to 10,000 docs/second
5. Running on AWS m6.ilarge EC2 instances
6. Heap is 8 GB

## Example Solr Schema

```
<schema name="imdb-movies" version="1.6">
  <!-- Unique Identifier -->
  <field name="id" type="string" indexed="true" stored="true" required="true" />

  <!-- Movie Metadata -->
  <field name="title" type="text_general" indexed="true" stored="true" />
  <field name="original_title" type="text_general" indexed="true" stored="true" />
  <field name="year" type="pint" indexed="true" stored="true" />
  <field name="runtime_minutes" type="pint" indexed="true" stored="true" />
  <field name="is_adult" type="boolean" indexed="true" stored="true" />

  <!-- Content and People (Multi-valued) -->
  <field name="genres" type="string" indexed="true" stored="true" multiValued="true" />
  <field name="directors" type="string" indexed="true" stored="true" multiValued="true" />
  <field name="cast" type="string" indexed="true" stored="true" multiValued="true" />

  <!-- Ratings and Metrics -->
  <field name="average_rating" type="pfloat" indexed="true" stored="true" />
  <field name="num_votes" type="plong" indexed="true" stored="true" />

  <!-- Catch-all field for searching -->
  <field name="text" type="text_general" indexed="true" stored="false" multiValued="true" />

  <!-- Copy Fields for search optimization -->
  <copyField source="title" dest="text"/>
  <copyField source="directors" dest="text"/>
  <copyField source="cast" dest="text"/>
  <copyField source="genres" dest="text"/>

  <!-- Field Type Definitions -->
  <fieldType name="string" class="solr.StrField" sortMissingLast="true" />
  <fieldType name="text_general" class="solr.TextField" positionIncrementGap="100">
    <analyzer>
      <tokenizer class="solr.StandardTokenizerFactory"/>
      <filter class="solr.LowerCaseFilterFactory"/>
    </analyzer>
  </fieldType>
  <fieldType name="pint" class="solr.IntPointField" />
  <fieldType name="pfloat" class="solr.FloatPointField" />
  <fieldType name="plong" class="solr.LongPointField" />
  <fieldType name="boolean" class="solr.BoolField" />
</schema>
```

## License

Apache-2.0