# Introduction to OpenSearch

**Source URL:** https://docs.opensearch.org/latest/getting-started/intro/

**Note:** This file was created with known OpenSearch fundamentals due to network access restrictions. Please verify current documentation for latest updates.

## Summary

OpenSearch is a distributed, open-source search and analytics engine forked from Elasticsearch. It provides scalable full-text search, analytics, and observability capabilities with a focus on community-driven development and transparency.

## What is OpenSearch?

OpenSearch is built on the Lucene search library and provides:
- Full-text search across large datasets
- Real-time analytics and aggregations
- RESTful API for all operations
- Horizontal scalability through distributed architecture
- Community-driven security and feature development

## Core Architecture

- **Distributed**: Data and processing distributed across multiple nodes
- **Scalable**: Add nodes to increase capacity and performance
- **Resilient**: Built-in replication and failover capabilities
- **Open**: Community-driven with transparent development process
- **Compatible**: API compatibility with Elasticsearch for migration ease

## Key Features

- **Search**: Fast, relevant full-text and phrase searching
- **Analytics**: Aggregations for data analysis and reporting
- **Dashboards**: OpenSearch Dashboards for visualization and exploration
- **Security**: Authentication, authorization, encryption (optional)
- **Plugins**: Extensible via plugins for custom functionality
- **Observability**: Tools for monitoring logs, metrics, and traces

## Common Use Cases

- **Log and Event Data**: Centralized logging and event analysis
- **Metrics and Time-Series**: Store and analyze operational metrics
- **Application Search**: Full-text search for e-commerce, content platforms
- **Security Analytics**: Threat detection and security monitoring
- **Business Analytics**: Data aggregation and business intelligence

## OpenSearch vs. Elasticsearch

- Community-driven development vs. proprietary Elasticsearch
- Open-source license (SSPL/Commons Clause) vs. proprietary licenses
- AWS-backed infrastructure and support
- Regular release cycle with community input
- Maintains API compatibility for ease of migration

## Getting Started Paths

1. **Single-Node Setup**: Ideal for development and learning
2. **Multi-Node Cluster**: For production deployments with high availability
3. **OpenSearch Service (AWS)**: Managed service option
4. **Docker/Containers**: Quick setup for testing and CI/CD

## Practical Considerations

- Define data strategy before indexing (mapping planning)
- Plan capacity based on data volume and query patterns
- Implement security policies for production environments
- Monitor cluster health and resource utilization
- Use appropriate refresh intervals for indexing performance

## Related Topics

- Mappings: Configure how fields are indexed and stored
- Data Ingestion: Methods for getting data into OpenSearch
- Query DSL: Language for searching and filtering data
- Dashboards: Visualization and monitoring tools
