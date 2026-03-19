# Index Management in OpenSearch Dashboards

**Source URL:** https://docs.opensearch.org/latest/dashboards/im-dashboards/index/

**Note:** This file was created with known OpenSearch fundamentals due to network access restrictions. Please verify current documentation for latest updates.

## Summary

OpenSearch Dashboards provides a comprehensive UI for managing indexes, including creation, configuration, monitoring, and lifecycle management. The Index Management feature integrates with Index State Management (ISM) policies for automated index operations across their lifecycle.

## Index Management Dashboard Features

### Index Overview

- **List view**: Display all indexes with key metrics
- **Health status**: Visual indicators (green, yellow, red) for cluster health
- **Shard distribution**: View shard allocation across nodes
- **Document count**: Number of documents in each index
- **Index size**: Total storage consumption
- **Refresh rate**: Current refresh interval configuration

### Index Details

Access detailed information for each index:
- **Settings**: Shard count, replica count, refresh interval
- **Mappings**: Field definitions and types
- **Aliases**: Associated aliases and their configurations
- **Statistics**: Document count, storage size, indexing rate
- **State**: Current index state (open, close, etc.)

## Creating Indexes via Dashboards

- **UI form creation**: Interactive form for settings, mappings, aliases
- **JSON editor**: Direct JSON definition for advanced configuration
- **Template application**: Apply index templates for consistent settings
- **Field type selection**: Visual field type picker for mapping definition
- **Validation**: Real-time validation of settings and mappings

## Index State Management (ISM)

ISM enables automated policies for index lifecycle operations.

### Common ISM Operations

- **Rollover**: Create new index when current reaches size/age threshold
- **Delete**: Remove indexes matching retention policy criteria
- **Shrink**: Reduce shard count for old, read-only indexes
- **Force merge**: Optimize segments for better performance
- **Close**: Make index unavailable but retain data
- **Snapshot**: Backup indexes automatically

### ISM Policy Structure

```json
{
  "policy": {
    "description": "Index lifecycle policy",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          {
            "rollover": {
              "min_size": "50gb",
              "min_index_age": "1d"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": {
              "min_index_age": "7d"
            }
          }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "set_replica_count": {
              "number_of_replicas": 1
            }
          }
        ],
        "transitions": [
          {
            "state_name": "cold",
            "conditions": {
              "min_index_age": "30d"
            }
          }
        ]
      },
      {
        "name": "cold",
        "actions": [
          {
            "set_replica_count": {
              "number_of_replicas": 0
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "90d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    ]
  }
}
```

## Monitoring Index Health

### Health Indicators

- **Green**: All primary and replica shards allocated
- **Yellow**: Primary shards allocated, some replicas unallocated
- **Red**: Some primary shards unallocated; data loss risk

### Key Metrics to Monitor

- **Unassigned shards**: Indicates cluster issues
- **Indexing rate**: Documents per second being indexed
- **Query rate**: Number of searches per second
- **Search latency**: Time to complete searches
- **Index size growth**: Monitor for space planning
- **Segment count**: Monitor force merge effectiveness

## Managing Aliases

### Alias Operations

- **Create alias**: Group multiple indexes under single name
- **Filter alias**: Restrict documents visible through alias
- **Write alias**: Set preferred index for write operations
- **Routing alias**: Route queries to specific shards
- **Remove alias**: Disassociate from index

### Zero-Downtime Version Updates

```
1. Create new index with updated mapping
2. Create read alias pointing to old index
3. Reindex data to new index
4. Update write alias to new index
5. Switch read alias to new index
6. Remove old index when safe
```

## Index Settings Management

### Modifiable Settings (Dynamic)

- **number_of_replicas**: Adjust replica count
- **refresh_interval**: Change how frequently data becomes searchable
- **index.max_result_window**: Modify maximum query result size
- **analysis**: Update analyzers and filters
- **codec**: Change compression codec

### Immutable Settings

- **number_of_shards**: Requires reindexing to change
- **index.version**: Created value cannot change

## Advanced Management Operations

### Closing Indexes

- Saves memory and cluster resources
- Data remains intact but not searchable
- Use for archival or temporary deactivation

### Opening Indexes

- Reactivate closed indexes
- Indexes become searchable again
- Cluster reallocation occurs

### Shrinking Indexes

- Reduce primary shard count
- Useful for read-only historical indexes
- Lowers cluster overhead

### Force Merge

- Reduce segment count (improves search performance)
- Use before closing old indexes
- Improves disk space efficiency

## Template Management

### Index Templates

- Define default settings and mappings
- Auto-apply to new indexes matching pattern
- Ensure consistency across similar indexes
- Example: `logs-*` pattern applies template to all matching new indexes

### Composable Templates

- Component templates: Reusable settings/mapping blocks
- Template composition: Combine components into final template
- Index patterns: Control which indexes match template

## Backup & Snapshots

### Snapshot Management in Dashboards

- Create on-demand snapshots
- Schedule automated backups
- Monitor backup progress
- Restore from snapshots
- Manage retention policies

## Practical Guidance

### Daily Operations

1. **Check cluster health**: Monitor shard allocation
2. **Review index sizes**: Ensure adequate storage
3. **Monitor query performance**: Check latency trends
4. **Verify ISM policy execution**: Ensure automated operations run
5. **Check for unassigned shards**: Investigate and resolve issues

### Production Setup

1. **Implement ISM policies**: Automate lifecycle management
2. **Use aliases**: Decouple application from index names
3. **Monitor actively**: Set up alerts for health issues
4. **Plan capacity**: Track growth and plan expansion
5. **Regular backups**: Schedule automated snapshots
6. **Document policies**: Record index lifecycle strategy

### Troubleshooting Common Issues

- **Yellow health**: Add replicas or restore missing shards
- **Red health**: Investigate node failures or disk space
- **High memory usage**: Reduce shard count or optimize queries
- **Slow indexing**: Check refresh interval, network, node resources
- **Query latency**: Investigate mapping, shard distribution, cache

### Best Practices

1. Use ISM policies for automated lifecycle management
2. Monitor indexes regularly through Dashboards
3. Implement rollover for time-series data
4. Use aliases for production indexes
5. Archive and delete old data per retention policy
6. Test recovery procedures regularly
7. Document index purposes and SLAs
8. Set up alerts for health anomalies
9. Plan capacity based on growth trends
10. Maintain snapshot/backup schedule

## Integration Points

- **Index State Management API**: Programmatic policy management
- **Cluster Settings**: Cluster-wide configuration affecting all indexes
- **Notification Plugins**: Alert on index state changes
- **Security**: Control who can manage specific indexes
