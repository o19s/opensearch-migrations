# Create Index API

**Source URL:** https://docs.opensearch.org/latest/api-reference/index-apis/create-index/

**Note:** This file was created with known OpenSearch fundamentals due to network access restrictions. Please verify current documentation for latest updates.

## Summary

The Create Index API enables programmatic creation of OpenSearch indexes with custom configurations. This API allows specification of index settings, mappings, and aliases in a single request, forming the foundation for data storage and retrieval operations.

## Basic Create Index Request

```
PUT /my-index-name
```

Creates index with default settings.

```
PUT /my-index-name
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "field_name": {
        "type": "text"
      }
    }
  }
}
```

Creates index with custom settings and mappings.

## Request Parameters

### Index Settings

- **number_of_shards**: How many shards to distribute the index across (default: 1)
- **number_of_replicas**: Number of replica copies of each shard (default: 1)
- **refresh_interval**: How often to make data searchable (default: 1s)
- **codec**: Compression codec (default: LZ4)
- **analysis**: Custom analyzer, tokenizer, and filter definitions
- **index.max_result_window**: Maximum query result size (default: 10000)

### Mapping Definition

- **properties**: Field definitions for the index
- **dynamic**: Control automatic field mapping (true, false, strict)

### Index Aliases

```json
{
  "aliases": {
    "my-alias": {
      "filter": {
        "term": { "status": "active" }
      }
    }
  }
}
```

## Complete Example

```json
PUT /my-application-index
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "refresh_interval": "30s",
    "analysis": {
      "analyzer": {
        "custom_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "custom_analyzer"
      },
      "category": {
        "type": "keyword"
      },
      "timestamp": {
        "type": "date",
        "format": "epoch_millis"
      },
      "price": {
        "type": "float"
      }
    }
  },
  "aliases": {
    "current-index": {}
  }
}
```

## Response

Successful creation returns:
```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "index": "my-index-name"
}
```

## Important Configuration Details

### Shard Strategy

- **Single shard**: Good for small indexes (< 50GB), simplifies management
- **Multiple shards**: Distribute large indexes for parallel querying and higher throughput
- **Shard count**: Typically 1 shard per 30-50GB expected data size
- **Immutable after creation**: Cannot change shard count without reindexing

### Replica Configuration

- **Zero replicas**: Single points of failure; useful for non-critical data
- **One replica**: Standard for production; enables failover and read scaling
- **Multiple replicas**: High availability but increased storage overhead
- **Dynamic adjustment**: Can change replica count on live indexes

### Refresh Interval

- **1s (default)**: Data visible ~1 second after indexing
- **Longer intervals**: Reduce I/O during bulk loading (use 30s-60s)
- **Production tuning**: Balance between search freshness and indexing performance

## Query Parameter Options

- **wait_for_active_shards**: Wait for specified shards to be ready (default: 1)
- **timeout**: Request timeout duration (default: 30s)
- **master_timeout**: Timeout for master node operations

## Error Responses

- **400 Bad Request**: Invalid settings, malformed JSON, invalid field types
- **400 resource_already_exists_exception**: Index already exists
- **504 Gateway Timeout**: Cluster too busy or unresponsive

## Practical Guidance

### Pre-Production Checklist

1. **Define mappings explicitly**: Avoid dynamic mapping in production
2. **Plan shard count**: Based on expected data volume and query patterns
3. **Set replica count**: Minimum 1 for HA in production
4. **Configure refresh interval**: Balance between visibility and performance
5. **Define custom analyzers if needed**: For specialized text processing
6. **Test mapping with sample data**: Ensure correct field indexing behavior
7. **Plan index lifecycle**: Define retention policies and rotation strategy

### Development vs. Production

**Development:**
- 1 shard, 0 replicas: Minimal resource usage
- 1s refresh interval: Fast search visibility
- Dynamic mapping: Flexible field discovery

**Production:**
- Multiple shards: Based on expected data size
- At least 1 replica: Ensure failover capability
- Longer refresh interval: Optimize write throughput
- Explicit mappings: Control field indexing behavior
- Properly sized cluster: Adequate resources for load

### Index Naming Conventions

- Use descriptive names: `logs-application-2026.03`
- Include dates for time-series: Enables easy rotation
- Avoid reserved characters: Use hyphens, not dots in some contexts
- Lowercase names: OpenSearch normalizes to lowercase anyway
- Consider alias strategy: Separate index naming from application access

## Advanced Features

### Lifecycle Management

- Define index templates for automatic settings inheritance
- Use index state management (ISM) for automatic rollover and deletion
- Implement warm/cold data tiering

### Performance Optimization

- Use doc_values for aggregations on keyword fields
- Enable compression for large text fields
- Configure thread pool sizes for write-heavy workloads
- Monitor indexing performance metrics

## Related Operations

- **Index Exists**: Check if index exists before operations
- **Get Index**: Retrieve current index settings and mappings
- **Delete Index**: Remove index and all data
- **Update Settings**: Modify settings on existing indexes
- **Reindex**: Copy data between indexes with mapping changes

## Best Practices

1. Create index with explicit, production-ready configuration
2. Define all mappings upfront; avoid dynamic mapping in production
3. Plan shard and replica strategy before creation
4. Use consistent naming convention for indexes
5. Create index templates for repeated patterns
6. Test mapping behavior with sample data
7. Document index purpose and retention policy
8. Use aliases for version management
9. Monitor index health metrics regularly
10. Prepare migration strategy before adding replicas or resharding
