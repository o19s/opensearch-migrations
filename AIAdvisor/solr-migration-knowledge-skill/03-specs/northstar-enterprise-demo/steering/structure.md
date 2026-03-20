# Project Structure: Northstar Enterprise Demo

## Recommended Demo Layout

```text
northstar-enterprise-app/
├── build.gradle.kts
├── settings.gradle.kts
├── src/main/kotlin/com/northstar/search/
│   ├── config/
│   │   ├── OpenSearchConfig.kt
│   │   └── SecurityConfig.kt
│   ├── domain/
│   │   ├── AtlasDocument.kt
│   │   ├── SearchRequest.kt
│   │   └── SearchResponse.kt
│   ├── indexing/
│   │   ├── SolrExportClient.kt
│   │   ├── DocumentTransformer.kt
│   │   └── ReindexService.kt
│   ├── search/
│   │   ├── QueryBuilderService.kt
│   │   ├── AtlasSearchService.kt
│   │   └── AggregationMapper.kt
│   ├── web/
│   │   ├── SearchController.kt
│   │   └── AdminController.kt
│   └── Application.kt
├── src/main/resources/
│   ├── application.yml
│   ├── opensearch/
│   │   └── atlas-index.json
│   └── samples/
│       └── northstar-sample-docs.json
└── src/test/
```

## Module Intent

- `config/`: client, auth, and environment configuration
- `domain/`: document model and API contracts
- `indexing/`: Solr extraction, transformation, and bulk loading
- `search/`: query translation and response shaping
- `web/`: demo endpoints for search and admin operations

## Design Rules

1. Keep Solr-specific logic isolated in the indexing layer.
2. Keep OpenSearch query-building isolated from web controllers.
3. Use aliases in all runtime search code.
4. Keep entitlement filters explicit and testable.
5. Make sample-doc loading deterministic for repeatable demo runs.
