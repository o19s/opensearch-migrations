# OpenSearch Mappings

**Source URL:** https://docs.opensearch.org/latest/mappings/

**Note:** This file was created with known OpenSearch fundamentals due to network access restrictions. Please verify current documentation for latest updates.

## Summary

Mappings define how documents and their fields are stored and indexed in OpenSearch. They specify field types, analyzers, and indexing behavior, enabling proper searching, filtering, and aggregation. Explicit mappings are essential for production systems to ensure correct data handling.

## Core Mapping Concepts

- **Field Type**: Defines how a field is indexed and analyzed (text, keyword, number, date, etc.)
- **Analyzer**: Breaks text into tokens for full-text search
- **Tokenizer**: Splits text into individual tokens
- **Token Filters**: Modify tokens (lowercasing, stemming, synonyms)
- **Mapping Definition**: JSON structure specifying field configurations

## Common Field Types

- **text**: Analyzed full-text search (default for string fields)
- **keyword**: Exact match, not analyzed; used for filtering, sorting, aggregations
- **integer, long, short, byte**: Integer number types
- **float, double, half_float**: Floating-point number types
- **boolean**: True/false values
- **date**: Date values with configurable formats
- **object**: Nested JSON objects
- **nested**: Array of objects with preserved relationships
- **geo_point**: Geographic location (latitude, longitude)
- **ip**: IP address fields
- **wildcard**: Efficient prefix and wildcard queries

## Mapping Definition Structure

```json
{
  "mappings": {
    "properties": {
      "field_name": {
        "type": "text",
        "analyzer": "standard"
      }
    }
  }
}
```

## Important Configuration Options

- **index**: Boolean flag controlling whether field is indexed (default: true)
- **store**: Store original field value separate from indexed data (rarely needed)
- **analyzer**: Specify which analyzer to use for text fields
- **fields**: Define multiple ways to analyze the same field (e.g., text + keyword)
- **copy_to**: Copy field values to another field for combined searching
- **enabled**: For object types, whether to index nested fields

## Dynamic Mapping

- **Dynamic: true** (default): Automatically creates mappings for new fields
- **Dynamic: false**: Ignores new fields but allows indexing
- **Dynamic: strict**: Rejects documents with unmapped fields

## Practical Guidance

- **Always define explicit mappings for production** to prevent unexpected field type conversions
- **Use keyword type for fields requiring exact matches**, filtering, or aggregations (product IDs, tags, categories)
- **Use text type for full-text searchable content** (descriptions, comments, articles)
- **Define multi-fields for flexible analysis**: Use `"fields": {"raw": {"type": "keyword"}}` to enable both full-text and exact match searching
- **Plan field structure before indexing** large datasets to avoid expensive remapping
- **Consider search performance**: Appropriate field types reduce query latency

## Analyzers and Tokenization

- **Standard Analyzer**: Default; splits on whitespace and punctuation, lowercases
- **Simple Analyzer**: Splits on non-letters, lowercases
- **Language Analyzers**: Language-specific stemming and stopwords (english, french, etc.)
- **Custom Analyzers**: Combine tokenizers and filters for specific requirements

## Nested vs. Object

- **object**: Flattens nested structure; good for independent fields
- **nested**: Preserves relationships in arrays of objects; required for complex queries on related fields

## Index Mapping Limits

- **256 fields limit** by default (configurable)
- **Limit nested depth** to avoid performance issues
- **Consider field count** in mapping strategy

## Mapping Updates

- **New fields can be added** to existing mappings without reindexing
- **Existing field types cannot be changed** without reindexing the index
- **Use aliases or rolling indices** for zero-downtime type changes

## Best Practices

1. Define mappings explicitly before production indexing
2. Use appropriate field types to optimize search and storage
3. Plan for future fields and queryable variations
4. Use multi-fields for dual analysis (text + keyword)
5. Document mapping intent and field purposes
6. Test mapping with realistic data before deployment
7. Monitor mapping evolution as schema changes occur
