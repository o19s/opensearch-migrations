# Getting Started with OpenSearch

**Source URL:** https://docs.opensearch.org/latest/getting-started/

**Note:** This file was created with known OpenSearch fundamentals due to network access restrictions. Please verify current documentation for latest updates.

## Summary

Getting started with OpenSearch involves setting up a cluster, understanding core concepts, and performing basic operations. This guide covers installation, configuration, cluster health checks, and fundamental operations needed to begin working with OpenSearch.

## Key Concepts

- **Cluster**: A collection of nodes working together to store and search data
- **Node**: A single instance of OpenSearch running on a server
- **Index**: Similar to a database table; stores documents with a specific mapping
- **Document**: A JSON object representing a single data record
- **Shard**: A subset of an index distributed across nodes for scalability
- **Replica**: A copy of a shard for redundancy and availability

## Installation & Setup

- OpenSearch can be deployed via Docker, Kubernetes, or traditional installation
- Requires Java 11 or higher for the core engine
- OpenSearch Dashboards provides web UI for cluster management and querying
- Security plugins available for authentication and encryption (optional in dev, required in production)

## Cluster Health & Status

- Use `GET _cluster/health` to check cluster status
- Health states: green (all shards allocated), yellow (replicas unallocated), red (primary shards missing)
- Monitor node connectivity and shard allocation status
- Check JVM memory usage and thread pools

## Initial Operations

- Create indexes with or without explicit mappings
- Ingest documents via bulk API or direct indexing
- Query data using Query DSL
- Configure index settings (number of shards, replicas, refresh intervals)
- Use index aliases for version management and zero-downtime deployments

## Practical Guidance

- Start with single-node clusters for development/testing
- Define mappings explicitly for production to ensure correct field types
- Use bulk operations for efficient data ingestion
- Monitor cluster health regularly
- Plan shard and replica strategy based on data size and availability requirements

## Next Steps

- Review mappings documentation for field type configuration
- Explore data ingestion methods (bulk API, Logstash integration)
- Learn Query DSL for effective searching
- Configure security and access control
- Set up monitoring and alerting
