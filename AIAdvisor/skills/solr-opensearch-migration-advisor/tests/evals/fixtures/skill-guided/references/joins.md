# Join Query Migration Reference

Solr `{!join from=field_a to=field_b}` has no direct equivalent in OpenSearch.

| Approach | When to use |
|----------|-------------|
| `terms` lookup query | Small-to-medium join sets. Queries index B for values, filters index A. |
| Denormalize (flatten) | Best performance. Copy joined data into parent doc at index time. |
| `nested` type | Child data queried together with parent. |
| `join` field (parent-child) | Child docs update independently. Higher query cost. |

Key: Solr joins can be chained; OpenSearch `terms` lookup is single-hop only.
Multi-level joins require denormalization or application-side logic.
