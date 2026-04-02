# Project Structure: `hello` Migration (Spring Boot / Kotlin)

[ASSUMED: Spring Boot 3.x + Kotlin + Gradle Kotlin DSL, following OSC standard platform stack]

## Project Layout

```
hello-search/
├── build.gradle.kts
├── src/
│   ├── main/
│   │   ├── kotlin/
│   │   │   └── com/example/hellosearch/
│   │   │       ├── HelloSearchApplication.kt
│   │   │       ├── config/
│   │   │       │   └── OpenSearchConfig.kt         # SigV4 client configuration
│   │   │       ├── domain/
│   │   │       │   └── HelloDocument.kt            # Kotlin data class (field definitions)
│   │   │       ├── index/
│   │   │       │   ├── HelloIndexService.kt        # Indexing: single + bulk
│   │   │       │   └── MigrationReindexService.kt  # Full reindex from Solr source
│   │   │       ├── search/
│   │   │       │   ├── HelloSearchService.kt       # Query building + execution
│   │   │       │   ├── HelloSearchRequest.kt       # Inbound query params DTO
│   │   │       │   └── HelloSearchResponse.kt      # Outbound search results DTO
│   │   │       ├── dualwrite/
│   │   │       │   └── DualWriteIndexService.kt    # Writes to both Solr + OpenSearch
│   │   │       └── api/
│   │   │           └── HelloSearchController.kt    # REST endpoint (replaces /solr/hello/select)
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── opensearch/
│   │       │   └── hello-mapping.json              # Index mapping (from design.md)
│   │       └── opensearch/
│   │           └── hello-settings.json             # Index settings (analyzers, replicas)
│   └── test/
│       ├── kotlin/
│       │   └── com/example/hellosearch/
│       │       ├── search/
│       │       │   └── HelloSearchServiceTest.kt   # Query translation unit tests
│       │       └── index/
│       │           └── HelloIndexServiceTest.kt    # Index + retrieve integration tests
│       └── resources/
│           └── testdata/
│               └── sample-docs.json                # 20 representative documents for tests
```

## Key Classes

### `OpenSearchConfig.kt`
Builds the `OpenSearchClient` with AWS SigV4 request signing.

```kotlin
@Configuration
class OpenSearchConfig(
    @Value("\${opensearch.endpoint}") private val endpoint: String,
    @Value("\${opensearch.region}") private val region: String
) {
    @Bean
    fun openSearchClient(): OpenSearchClient {
        val signer = AwsSdk2TransportOptions.builder()
            .setSigner(Aws4Signer.create())
            .build()
        val transport = RestClientTransport(
            RestClient.builder(HttpHost.create(endpoint)).build(),
            new JacksonJsonpMapper(),
            signer
        )
        return OpenSearchClient(transport)
    }
}
```

### `HelloDocument.kt`
Mirrors the OpenSearch index mapping. Field names must exactly match mapping properties.

```kotlin
data class HelloDocument(
    val id: String,
    val title: String,
    val body: String?,                          // [ASSUMED: primary text field]
    val category: String?,                      // [ASSUMED: facet field]
    val author: String?,                        // [ASSUMED: metadata field]
    val publishedDate: Instant?,                // [ASSUMED: date field for range filters]
    val tags: List<String> = emptyList(),       // [ASSUMED: multi-value keyword field]
    val score: Float? = null                    // [ASSUMED: numeric boost field]
)
```

### `HelloSearchService.kt`
Translates `HelloSearchRequest` into an OpenSearch `SearchRequest`. This is where the
eDisMax → `multi_match` translation lives.

```kotlin
@Service
class HelloSearchService(private val client: OpenSearchClient) {

    fun search(req: HelloSearchRequest): HelloSearchResponse {
        val query = buildQuery(req)
        val aggs = buildAggregations(req)

        val response = client.search({ s ->
            s.index("hello")
             .query(query)
             .aggregations(aggs)
             .from(req.from)
             .size(req.size)
        }, HelloDocument::class.java)

        return HelloSearchResponse.from(response)
    }

    private fun buildQuery(req: HelloSearchRequest): Query {
        // eDisMax translation:
        // Solr: q=<text>&qf=title^3 body^1&pf=title^5&mm=75%
        // OpenSearch: bool.should[ multi_match(best_fields), match_phrase(title, boost=5) ]
        val shouldClauses = mutableListOf<Query>()

        if (req.q.isNotBlank()) {
            shouldClauses += Query.of { q ->
                q.multiMatch { mm ->
                    mm.query(req.q)
                      .fields("title^3", "body^1")    // [ASSUMED: qf field weights]
                      .type(TextQueryType.BestFields)
                      .minimumShouldMatch("75%")       // [ASSUMED: mm=75%]
                }
            }
            shouldClauses += Query.of { q ->
                q.matchPhrase { mp ->
                    mp.field("title")
                      .query(req.q)
                      .boost(5.0f)                     // [ASSUMED: pf boost]
                      .slop(2)
                }
            }
        }

        val filterClauses = mutableListOf<Query>()
        req.category?.let { cat ->
            filterClauses += Query.of { q -> q.term { t -> t.field("category").value(cat) } }
        }

        return Query.of { q ->
            q.bool { b ->
                b.should(shouldClauses)
                 .filter(filterClauses)
                 .minimumShouldMatch(if (req.q.isNotBlank()) "1" else "0")
            }
        }
    }

    private fun buildAggregations(req: HelloSearchRequest): Map<String, Aggregation> =
        mapOf(
            "by_category" to Aggregation.of { a ->
                a.terms { t -> t.field("category").size(20) }  // [ASSUMED: facet.field=category]
            }
        )
}
```

### `DualWriteIndexService.kt`
During Phase 3 (dual-write), all index operations go to both Solr and OpenSearch.

```kotlin
@Service
@ConditionalOnProperty("migration.dual-write.enabled", havingValue = "true")
class DualWriteIndexService(
    private val solrClient: SolrClient,       // existing client
    private val helloIndexService: HelloIndexService
) {
    private val log = LoggerFactory.getLogger(javaClass)

    fun index(doc: HelloDocument) {
        // Write to OpenSearch first (fail-fast on new system)
        helloIndexService.index(doc)

        // Write to Solr (existing path — must not regress)
        try {
            solrClient.addBean("hello", toSolrInputDocument(doc))
        } catch (e: Exception) {
            // DUCT TAPE: Log and continue — Solr is the retiring system
            // Proper fix: implement retry queue if Solr consistency matters
            log.warn("Solr dual-write failed for doc ${doc.id}: ${e.message}")
        }
    }
}
```

## application.yml

```yaml
spring:
  application:
    name: hello-search

opensearch:
  endpoint: https://your-domain.us-east-1.es.amazonaws.com   # [ASSUMED: endpoint format]
  region: us-east-1    # [ASSUMED]
  index: hello

migration:
  dual-write:
    enabled: false     # flip to true during Phase 3

solr:
  base-url: http://solr:8983/solr    # [ASSUMED: SolrCloud ZK or direct URL]
  collection: hello
```

## build.gradle.kts (key dependencies)

```kotlin
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.opensearch.client:opensearch-java:2.10.0")
    implementation("software.amazon.awssdk:opensearch:2.25.0")
    implementation("software.amazon.awssdk:auth:2.25.0")
    implementation("org.apache.solr:solr-solrj:8.11.2")     // for dual-write + reindex source
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.opensearch:opensearch-testcontainers:2.0.0")
}
```

## Testing Strategy

| Layer | Approach | Tools |
|-------|----------|-------|
| Query building | Unit tests, assert Query DSL JSON | JUnit 5, `ObjectMapper` |
| Index + retrieve | Integration test against real container | TestContainers + OpenSearch image |
| Schema fidelity | Mapping verification test | Assert `_mapping` API matches `hello-mapping.json` |
| Query parity | Side-by-side comparison script | Python script hitting both Solr + OpenSearch |
| Load test | Replay production query log | Gatling or k6 with captured traffic |

## Local Development

```bash
# Start OpenSearch locally
docker run -d -p 9200:9200 -e discovery.type=single-node \
  opensearchproject/opensearch:2.17.0

# Disable SSL for local (dev only — never production)
export OPENSEARCH_SECURITY_DISABLED=true

# Start app
./gradlew bootRun --args='--spring.profiles.active=local'

# Create index + load test data
./gradlew test --tests "*HelloIndexServiceTest.loadSampleDocs"
```
