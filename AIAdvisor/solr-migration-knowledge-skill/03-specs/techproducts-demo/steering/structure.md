# Project Structure: Spring Boot / Kotlin

This is the recommended minimal project structure for the techproducts migration. It demonstrates patterns that scale to real migrations.

## Directory Layout

```
techproducts-migration/
├── build.gradle.kts              # Gradle config (OpenSearch client, Spring Boot)
├── src/main/kotlin/
│   └── com/example/techproducts/
│       ├── TechproductsApp.kt      # Spring Boot entry point
│       ├── config/
│       │   ├── OpenSearchConfig.kt  # Bean: OpenSearchClient (SigV4 for AWS)
│       │   └── AppConfig.kt         # Other Spring beans
│       ├── domain/
│       │   ├── ProductDocument.kt   # @Document class (mapping metadata)
│       │   └── SearchQuery.kt       # Query request/response DTOs
│       ├── repository/
│       │   └── ProductRepository.kt # Spring Data OpenSearch repo
│       ├── service/
│       │   ├── ProductSearchService.kt     # Query logic layer
│       │   └── MigrationService.kt         # Reindex / bulk load
│       ├── controller/
│       │   └── SearchController.kt  # REST API (optional; CLI demo is fine)
│       └── util/
│           └── SolrExporter.kt      # Export from Solr; transform; load
├── src/main/resources/
│   ├── application.yml              # Spring Boot config (OpenSearch endpoint)
│   ├── synonyms.txt                 # Synonym graph (mirrors Solr)
│   └── logback-spring.xml           # Logging
├── src/test/kotlin/
│   └── com/example/techproducts/
│       ├── ProductSearchServiceTest.kt      # Unit tests (mocks)
│       ├── ProductRepositoryIntegrationTest.kt  # Integration (TestContainers)
│       └── MigrationIntegrationTest.kt      # Full flow
└── README.md                        # How to run
```

## Key Classes

### `ProductDocument.kt`
```kotlin
@Document(indexName = "techproducts")
data class ProductDocument(
    @Id val id: String,
    @Field(type = FieldType.Text, analyzer = "text_general") val name: String,
    @Field(type = FieldType.Keyword) val manu: String,
    @Field(type = FieldType.Keyword) val manu_exact: String,  // from copyField
    @MultiField(
        mainField = Field(type = FieldType.Text, analyzer = "text_general"),
        otherFields = [InnerField(suffix = "keyword", type = FieldType.Keyword)]
    ) val cat: List<String>,
    @Field(type = FieldType.Text, analyzer = "text_general") val features: List<String>,
    @Field(type = FieldType.Float) val weight: Float?,
    @Field(type = FieldType.Float) val price: Float,
    @Field(type = FieldType.Integer) val popularity: Int,
    @Field(type = FieldType.Boolean) val inStock: Boolean,
    @Field(type = FieldType.GeoPoint) val store: String?,  // "lat,lon"
    @Field(type = FieldType.Date) val manufacturedate_dt: LocalDateTime?,
    @Field(type = FieldType.Text) val _text_: String  // catchall (copy_to)
)
```

### `ProductSearchService.kt`
```kotlin
@Service
class ProductSearchService(private val repository: ProductRepository) {
    // Keyword search (eDisMax equivalent)
    fun searchKeyword(query: String, limit: Int = 10): SearchResults { }

    // Filtered search
    fun searchWithFilters(
        query: String,
        inStock: Boolean? = null,
        priceMin: Float? = null,
        priceMax: Float? = null,
        categories: List<String>? = null
    ): SearchResults { }

    // Faceted search
    fun searchWithFacets(query: String): SearchWithFacets { }

    // Geo search
    fun searchNearby(lat: Double, lon: Double, distanceKm: Double): List<ProductDocument> { }
}
```

### `MigrationService.kt`
```kotlin
@Service
class MigrationService(
    private val client: OpenSearchClient,
    private val repository: ProductRepository
) {
    // Full reindex from Solr export
    suspend fun reindexFromSolr(solrExportUrl: String) { }

    // Bulk index with refresh control
    suspend fun bulkIndex(documents: List<ProductDocument>) { }

    // Validate migration: count + spot-check queries
    suspend fun validateMigration() { }
}
```

### `OpenSearchConfig.kt`
```kotlin
@Configuration
class OpenSearchConfig {
    // Local development: HTTP without auth
    @Bean
    @Profile("dev")
    fun openSearchClient(): OpenSearchClient { }

    // AWS managed: SigV4 signing required
    @Bean
    @Profile("aws")
    fun openSearchClientAws(
        @Value("\${aws.opensearch.endpoint}") endpoint: String,
        @Value("\${aws.region}") region: String
    ): OpenSearchClient { }
}
```

## Testing Strategy

### Unit Tests (no infrastructure)
- `ProductSearchServiceTest` — mock repository, test query logic
- `SolrExporter` parsing — mock Solr response, test transform

### Integration Tests (with TestContainers)
- `ProductRepositoryIntegrationTest` — real OpenSearch container, CRUD ops
- `MigrationIntegrationTest` — full flow: create index, bulk load, query, verify

### Example using TestContainers:
```kotlin
@SpringBootTest
@Container
class ProductSearchServiceIntegrationTest {
    companion object {
        @Container
        private val openSearchContainer = OpenSearchContainer()
    }

    @Test
    fun searchByCategory() {
        // Load test data
        repository.saveAll(testProducts)
        // Execute query
        val results = service.searchKeyword("hard drive")
        // Assert
        assertThat(results.hits).hasSize(2)
    }
}
```

## Package Conventions

| Package | Responsibility | Who Owns |
|---------|-----------------|----------|
| `config` | Spring beans, AWS credentials, index settings | Infrastructure/DevOps |
| `domain` | Kotlin data classes, `@Document` annotations | Domain modeler |
| `repository` | Spring Data OpenSearch repository interface | Data layer engineer |
| `service` | Query logic, business rules, transformation | Search engineer |
| `controller` | REST endpoints (if building web UI) | API engineer |
| `util` | Solr export/transform, utilities | Migration engineer |

## Build Configuration (build.gradle.kts)

```kotlin
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web:3.5.0")
    implementation("org.opensearch.client:opensearch-java:2.10.0")
    implementation("org.springframework.data:spring-data-opensearch:1.3.0")

    // AWS SigV4 signing for managed service
    implementation("software.amazon.awssdk:opensearch:2.21.0")
    implementation("software.amazon.awssdk:auth:2.21.0")

    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test:3.5.0")
    testImplementation("org.testcontainers:testcontainers:1.19.0")
    testImplementation("org.testcontainers:junit-jupiter:1.19.0")
}

tasks.test {
    useJUnitPlatform()
}
```

## Running Locally

### 1. Start OpenSearch (Docker)
```bash
docker run -d \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  opensearchproject/opensearch:2.10.0
```

### 2. Create Index and Load Data
```bash
./gradlew run --args="--migrate-from-solr=http://localhost:8983/solr/techproducts"
```

### 3. Run Tests
```bash
./gradlew test
```

### 4. Query via CLI (example)
```bash
./gradlew run --args="--query='hard drive' --facet=cat"
```

## Deployment Target

**Development:** Local Docker + IDE

**CI/CD:** GitHub Actions or GitLab CI
- Build JAR
- Run integration tests (TestContainers)
- Deploy to target (ECS, Kubernetes, or EC2)

**AWS:** Spring Boot app on ECS/Fargate
- Pulls OpenSearch endpoint from CloudFormation stack
- SigV4 credentials from IAM task role

---

**Architect:** Platform Team
**Framework:** Spring Boot 3.5 + Kotlin 1.9
**Java:** OpenJDK 21+
