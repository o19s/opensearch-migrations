# Data Transformation Rules: Solr to OpenSearch

**Trigger:** When transforming documents for indexing into OpenSearch — applied per document, per field. Validate every transformation explicitly; do not skip a rule because a field looks correct.

## Rules

- **Timestamps:** convert ISO-8601 strings to `epoch_millis` (long); map field as `"date"` with `"format": "epoch_millis"`.
- **Trie / numeric fields:** cast to native JSON numbers; map to `integer`, `long`, `float`, or `double`.
- **String-encoded numbers:** coerce to declared numeric type before indexing; reject documents that fail coercion (do not index null).
- **Multi-value fields:** preserve array structure; never flatten to a single value.
- **Booleans:** normalize to JSON `true`/`false`; reject string variants (`"yes"`, `"1"`, `"TRUE"`).
- **Geo fields:** convert `"lat,lon"` strings to `{"lat": <float>, "lon": <float>}`; map as `"geo_point"`.
- **Field names with dots:** replace dots with underscores (`product.id` → `product_id`); update mapping accordingly.
- **Solr internal fields:** strip `_version_`, `_root_`, `_nest_path_` from every document before indexing.
- **Document identity:** use Solr `uniqueKey` value as OpenSearch `_id`; set explicitly on every index request.
- **Text cleanup:** strip residual HTML/XML markup unless intentionally stored; collapse whitespace.

## What counts as a transformation error

- Date field indexed as a string in a `date`-typed mapping.
- Numeric field indexed as a string in a numeric-typed mapping.
- Multi-value field silently truncated to one value.
- Document indexed with a Solr internal field present.
- Geo field stored as `"lat,lon"` string in a `geo_point` mapping.

Flag any of the above as **Breaking** and surface it before proceeding.

**Reference:** `references/01-schema-migration.md` — type-by-type field mappings, dynamic fields, copy fields, similarity configuration with worked examples.
