# Spring Boot 3.5+ / Kotlin: OpenSearch Client Integration Guide

## Table of Contents
1. [Client Options Overview](#client-options-overview)
2. [Recommended Setup](#recommended-setup)
3. [Dependencies & Configuration](#dependencies--configuration)
4. [SigV4 Authentication for AWS](#sigv4-authentication-for-aws)
5. [OpenSearchClient Bean](#opensearchclient-bean)
6. [Spring Data OpenSearch Repository Pattern](#spring-data-opensearch-repository-pattern)
7. [Direct Client Queries](#direct-client-queries)
8. [Index Management](#index-management)
9. [Bulk Indexing](#bulk-indexing)
10. [Testing with TestContainers](#testing-with-testcontainers)
11. [Connection & Performance Tuning](#connection--performance-tuning)
12. [Common Gotchas](#common-gotchas)

---

## Client Options Overview

### opensearch-java (Official Java Client)

The official Java client from OpenSearch Project. Provides low-level and builder API.

**Pros:**
- Official; first-class support
- Modern async support (CompletableFuture, reactive)
- Type-safe query builder
- Latest features

**Cons:**
- Minimal Spring integration (requires manual bean setup)
- Lower-level; more boilerplate for simple queries

### opensearch-spring-data (Community Project)

Spring Data abstraction over opensearch-java. Provides repository pattern, annotations.

**Pros:**
- Familiar Spring Data conventions (if you've used JPA, MongoDB)
- Declarative repository queries
- Annotation-based mapping (@Document, @Field)
- Automatic CRUD operations

**Cons:**
- Community-maintained; not official
- Sometimes lags behind latest OpenSearch features
- Can hide performance details

### High-Level REST Client (Deprecated Path from ES)

Older Elasticsearch High-Level REST Client (similar to opensearch-high-level-rest-client).

**Status:** Deprecated in favor of opensearch-java.

**Avoid for new projects.** Maintained for legacy code only.

### OpenSearch REST Client (Low-Level)

Direct HTTP client; no query builder, raw JSON.

**Use case:** If you have raw JSON queries you want to pass through without parsing.

---

## Recommended Setup

For Spring Boot 3.5+ with Kotlin, use this stack:

1. **Client:** opensearch-java (official, modern)
2. **Spring Integration:** opensearch-spring-data (repository pattern)
3. **Authentication:** AWS SDK v2 for SigV4 signing (if AWS-managed OpenSearch)
4. **Serialization:** Jackson (default; configured automatically)

### Architecture Overview

```
Spring Boot App (Kotlin)
    ↓
Spring Data OpenSearch Repositories
    ↓
opensearch-java Client
    ↓
RestClient (HTTP transport)
    ↓
OpenSearch Cluster
```

Repositories handle simple CRUD and queries; for complex queries, use OpenSearchClient directly.

---

## Dependencies & Configuration

### Gradle Build File

```gradle
dependencies {
    // OpenSearch client
    implementation 'org.opensearch.client:opensearch-java:2.5.0'

    // Spring Data OpenSearch
    implementation 'org.opensearch.client:spring-data-opensearch:2.5.0'

    // AWS SigV4 signing (for AWS managed OpenSearch)
    implementation 'software.amazon.awssdk:sdk-for-java:2.20.0'
    implementation 'software.amazon.awssdk:auth-crt:2.20.0'

    // Jackson for JSON serialization
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'

    // Spring Boot
    implementation 'org.springframework.boot:spring-boot-starter-web:3.5.0'
    implementation 'org.springframework.data:spring-data-commons:3.5.0'

    // Test
    testImplementation 'org.springframework.boot:spring-boot-starter-test:3.5.0'
    testImplementation 'org.testcontainers:testcontainers:1.19.0'
    testImplementation 'org.testcontainers:opensearch:1.19.0'
}
```

### application.yml Configuration

```yaml
spring:
  application:
    name: opensearch-app

opensearch:
  host: localhost
  port: 9200
  protocol: http
  username: admin
  password: admin123

  # AWS-managed OpenSearch Service
  aws:
    enabled: false
    region: us-west-2
    # Service endpoint will be auto-discovered from IAM role
```

### Configuration Class

```kotlin
package com.example.config

import org.opensearch.client.opensearch.OpenSearchClient
import org.opensearch.client.transport.OpenSearchTransport
import org.opensearch.client.transport.rest_client.RestClientTransport
import org.apache.http.HttpHost
import org.apache.http.auth.AuthScope
import org.apache.http.auth.UsernamePasswordCredentials
import org.apache.http.impl.client.BasicCredentialsProvider
import org.elasticsearch.client.RestClient
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import com.fasterxml.jackson.databind.ObjectMapper

@Configuration
class OpenSearchConfig(
    @Value("\${opensearch.host}") val host: String,
    @Value("\${opensearch.port}") val port: Int,
    @Value("\${opensearch.protocol}") val protocol: String,
    @Value("\${opensearch.username:admin}") val username: String,
    @Value("\${opensearch.password:admin123}") val password: String,
    @Value("\${opensearch.aws.enabled:false}") val awsEnabled: Boolean,
    @Value("\${opensearch.aws.region:us-west-2}") val awsRegion: String
) {

    @Bean
    fun objectMapper(): ObjectMapper = ObjectMapper()

    @Bean
    fun restClient(): RestClient {
        val credentialsProvider = BasicCredentialsProvider().apply {
            setCredentials(
                AuthScope.ANY,
                UsernamePasswordCredentials(username, password)
            )
        }

        return RestClient.builder(HttpHost(host, port, protocol))
            .setHttpClientConfigCallback { httpClientBuilder ->
                httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider)
            }
            .build()
    }

    @Bean
    fun transport(restClient: RestClient, objectMapper: ObjectMapper): OpenSearchTransport {
        return RestClientTransport(restClient, objectMapper)
    }

    @Bean
    fun openSearchClient(transport: OpenSearchTransport): OpenSearchClient {
        return OpenSearchClient(transport)
    }
}
```

---

## SigV4 Authentication for AWS

For AWS-managed OpenSearch Service (not self-hosted), use SigV4 signing to authenticate without username/password.

### AWS Configuration Class

```kotlin
package com.example.config

import org.opensearch.client.opensearch.OpenSearchClient
import org.opensearch.client.transport.OpenSearchTransport
import org.opensearch.client.transport.rest_client.RestClientTransport
import org.apache.http.HttpHost
import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import com.amazonaws.auth.DefaultAWSCredentialsProviderChain
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider
import software.amazon.awssdk.auth.signer.Aws4Signer
import software.amazon.awssdk.awscore.AwsRequestSigningConfig
import software.amazon.awssdk.http.apache.ApacheHttpClient
import software.amazon.awssdk.http.auth.aws.internal.AwsChunkedEncodingConfig
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.sts.StsClient
import software.amazon.awssdk.services.sts.model.GetCallerIdentityRequest
import com.fasterxml.jackson.databind.ObjectMapper
import org.elasticsearch.client.RestClient

@Configuration
@ConditionalOnProperty(name = "opensearch.aws.enabled", havingValue = "true")
class OpenSearchAwsConfig(
    @Value("\${opensearch.host}") val host: String,
    @Value("\${opensearch.port}") val port: Int,
    @Value("\${opensearch.aws.region}") val awsRegion: String
) {

    @Bean
    fun objectMapper(): ObjectMapper = ObjectMapper()

    @Bean
    fun restClient(): RestClient {
        val credentialsProvider = DefaultCredentialsProvider.create()
        val httpClient = ApacheHttpClient.builder()
            .credentialsProvider(credentialsProvider)
            .build()

        val signerConfig = Aws4SignerConfigProvider(
            service = "es",
            region = Region.of(awsRegion),
            credentials = credentialsProvider
        )

        return RestClient.builder(HttpHost(host, port, "https"))
            .setHttpClientConfigCallback { httpClientBuilder ->
                // Apply AWS SigV4 signing via interceptor
                httpClientBuilder.addInterceptorLast { httpRequest, httpContext ->
                    val signer = Aws4Signer.create()
                    signer.sign(httpRequest, signerConfig)
                }
            }
            .build()
    }

    @Bean
    fun transport(restClient: RestClient, objectMapper: ObjectMapper): OpenSearchTransport {
        return RestClientTransport(restClient, objectMapper)
    }

    @Bean
    fun openSearchClient(transport: OpenSearchTransport): OpenSearchClient {
        return OpenSearchClient(transport)
    }
}

class Aws4SignerConfigProvider(
    val service: String,
    val region: Region,
    val credentials: software.amazon.awssdk.auth.credentials.CredentialsProvider
) : AwsRequestSigningConfig {
    override fun getSigningName(): String = service
    override fun getSigningRegion(): Region = region
    override fun getCredentialsProvider(): software.amazon.awssdk.auth.credentials.CredentialsProvider = credentials
}
```

**For AWS OpenSearch Service, use HTTPS (port 443 or custom port), not HTTP.**

---

## OpenSearchClient Bean

The `OpenSearchClient` is the entry point for all operations.

### Basic Usage

```kotlin
package com.example.service

import org.opensearch.client.opensearch.OpenSearchClient
import org.opensearch.client.opensearch.core.SearchRequest
import org.opensearch.client.opensearch.core.SearchResponse
import org.opensearch.client.opensearch.core.search.Hit
import org.springframework.stereotype.Service
import org.slf4j.LoggerFactory

@Service
class ProductSearchService(
    private val openSearchClient: OpenSearchClient
) {
    private val logger = LoggerFactory.getLogger(javaClass)

    fun searchProducts(query: String): List<ProductDocument> {
        val searchRequest = SearchRequest.Builder()
            .index("products")
            .query { q ->
                q.match { m ->
                    m.field("title").query(query)
                }
            }
            .size(20)
            .build()

        val response: SearchResponse<ProductDocument> = openSearchClient.search(
            searchRequest,
            ProductDocument::class.java
        )

        return response.hits().hits()
            .mapNotNull { hit: Hit<ProductDocument> -> hit.source() }
    }
}
```

### Document Model (Kotlin Data Class)

```kotlin
package com.example.domain

import com.fasterxml.jackson.annotation.JsonProperty
import org.springframework.data.annotation.Id
import org.springframework.data.opensearch.annotations.Document
import org.springframework.data.opensearch.annotations.Field
import org.springframework.data.opensearch.annotations.FieldType

@Document(indexName = "products")
data class ProductDocument(
    @Id
    val id: String,

    @Field(type = FieldType.Text)
    val title: String,

    @Field(type = FieldType.Text)
    val description: String? = null,

    @Field(type = FieldType.Float)
    val price: Double,

    @Field(type = FieldType.Keyword)
    val category: String,

    @Field(type = FieldType.Keyword)
    @JsonProperty("brand")
    val brand: String,

    @Field(type = FieldType.Boolean)
    @JsonProperty("in_stock")
    val inStock: Boolean = true,

    @Field(type = FieldType.Keyword, name = "tags")
    val tags: List<String> = emptyList(),

    @Field(type = FieldType.Date)
    @JsonProperty("created_at")
    val createdAt: Long? = null
)
```

---

## Spring Data OpenSearch Repository Pattern

For simple CRUD and derived query methods, use Spring Data repository pattern.

### Repository Interface

```kotlin
package com.example.repository

import com.example.domain.ProductDocument
import org.springframework.data.opensearch.repository.OpenSearchRepository
import org.springframework.stereotype.Repository

@Repository
interface ProductRepository : OpenSearchRepository<ProductDocument, String> {

    // Derived query methods
    fun findByCategory(category: String): List<ProductDocument>

    fun findByBrand(brand: String): List<ProductDocument>

    fun findByCategoryAndBrand(category: String, brand: String): List<ProductDocument>

    fun findByInStockTrue(): List<ProductDocument>

    fun findByPriceBetween(minPrice: Double, maxPrice: Double): List<ProductDocument>

    fun findByTitleContainingIgnoreCase(title: String): List<ProductDocument>

    // Custom query with @Query annotation
    @Query("""{"match":{"title":{"query":"?0"}}}""")
    fun findByTitleCustom(title: String): List<ProductDocument>
}
```

### Using Repository

```kotlin
@Service
class ProductService(
    private val productRepository: ProductRepository
) {

    fun getProductsByCategory(category: String): List<ProductDocument> {
        return productRepository.findByCategory(category)
    }

    fun getPriceRange(min: Double, max: Double): List<ProductDocument> {
        return productRepository.findByPriceBetween(min, max)
    }

    fun saveProduct(product: ProductDocument): ProductDocument {
        return productRepository.save(product)
    }

    fun findById(id: String): ProductDocument? {
        return productRepository.findById(id).orElse(null)
    }

    fun deleteById(id: String) {
        productRepository.deleteById(id)
    }
}
```

**Note:** Derived queries work for simple conditions. For complex queries (bool, must_not, etc.), use @Query with JSON or switch to OpenSearchClient directly.

---

## Direct Client Queries

For complex queries, use `OpenSearchClient` directly.

### Match Query

```kotlin
fun searchByTitle(query: String): List<ProductDocument> {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q -> q.match { m -> m.field("title").query(query) } }
                .size(20)
        },
        ProductDocument::class.java
    )
    return response.hits().hits().mapNotNull { it.source() }
}
```

### Bool Query (Must, Should, Filter, MustNot)

```kotlin
fun advancedSearch(
    title: String?,
    minPrice: Double?,
    maxPrice: Double?,
    category: String?,
    mustBeInStock: Boolean = true
): List<ProductDocument> {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q ->
                    q.bool { b ->
                        if (title != null) {
                            b.must { m -> m.match { mq -> mq.field("title").query(title) } }
                        }
                        if (minPrice != null || maxPrice != null) {
                            b.filter { f ->
                                f.range { r ->
                                    r.field("price")
                                    if (minPrice != null) r.gte(minPrice)
                                    if (maxPrice != null) r.lte(maxPrice)
                                }
                            }
                        }
                        if (category != null) {
                            b.filter { f ->
                                f.term { t -> t.field("category").value(category) }
                            }
                        }
                        if (mustBeInStock) {
                            b.filter { f ->
                                f.term { t -> t.field("in_stock").value(true) }
                            }
                        }
                    }
                }
                .size(50)
        },
        ProductDocument::class.java
    )
    return response.hits().hits().mapNotNull { it.source() }
}
```

### Aggregations (Faceting)

```kotlin
fun getCategoryFacets(): Map<String, Long> {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q -> q.matchAll { } }
                .size(0) // Don't return docs, only aggs
                .aggregations("categories", { agg ->
                    agg.terms { t -> t.field("category").size(100) }
                })
        },
        Void::class.java
    )

    val categories = response.aggregations()["categories"]
    // Parse termsAggregate and extract buckets
    // Each bucket has key (category name) and docCount
    return emptyMap() // Implement bucket parsing
}
```

### Search with Sorting

```kotlin
fun searchSortedByPrice(query: String, ascending: Boolean = true): List<ProductDocument> {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q -> q.match { m -> m.field("title").query(query) } }
                .sort { s ->
                    s.field { f ->
                        f.field("price")
                        f.order(if (ascending) SortOrder.Asc else SortOrder.Desc)
                    }
                }
                .size(20)
        },
        ProductDocument::class.java
    )
    return response.hits().hits().mapNotNull { it.source() }
}
```

### Highlighting

```kotlin
fun searchWithHighlight(query: String): List<Pair<ProductDocument, Map<String, String>>> {
    val response = openSearchClient.search(
        { req ->
            req.index("products")
                .query { q -> q.match { m -> m.field("title").query(query) } }
                .highlight { h ->
                    h.fields("title", { f -> f.fragmentSize(150) })
                    h.fields("description", { f -> f.fragmentSize(150) })
                }
                .size(20)
        },
        ProductDocument::class.java
    )

    return response.hits().hits().map { hit ->
        val doc = hit.source()!!
        val highlights = hit.highlight()?.entries?.associate { (k, v) -> k to v.joinToString("...") } ?: emptyMap()
        doc to highlights
    }
}
```

---

## Index Management

### Create Index with Mapping

```kotlin
@Service
class IndexManagementService(
    private val openSearchClient: OpenSearchClient
) {

    fun createProductIndex() {
        val indexExists = openSearchClient.indices().exists { req ->
            req.index("products")
        }.value()

        if (!indexExists) {
            openSearchClient.indices().create { req ->
                req.index("products")
                    .mappings { m ->
                        m.properties("id", { p -> p.keyword { } })
                        m.properties("title", { p -> p.text { } })
                        m.properties("description", { p -> p.text { } })
                        m.properties("price", { p -> p.float_ { } })
                        m.properties("category", { p -> p.keyword { } })
                        m.properties("brand", { p -> p.keyword { } })
                        m.properties("in_stock", { p -> p.boolean_ { } })
                        m.properties("tags", { p -> p.keyword { } })
                        m.properties("created_at", { p -> p.date { } })
                    }
                    .settings { s ->
                        s.numberOfShards("1")
                        s.numberOfReplicas("0")
                    }
            }
        }
    }

    fun updateMapping(indexName: String) {
        openSearchClient.indices().putMapping { req ->
            req.index(indexName)
                .properties("new_field", { p -> p.text { } })
        }
    }

    fun deleteIndex(indexName: String) {
        openSearchClient.indices().delete { req ->
            req.index(indexName)
        }
    }
}
```

---

## Bulk Indexing

For high-throughput indexing, use bulk API.

### BulkIngester Pattern

```kotlin
@Service
class BulkIndexingService(
    private val openSearchClient: OpenSearchClient
) {

    fun bulkIndexProducts(products: List<ProductDocument>) {
        val bulkRequest = BulkRequest.Builder()

        products.forEach { product ->
            bulkRequest.operations { op ->
                op.index { idx ->
                    idx.index("products")
                        .id(product.id)
                        .document(product)
                }
            }
        }

        val response = openSearchClient.bulk(bulkRequest.build())

        if (response.errors()) {
            response.items().forEach { item ->
                if (item.operationName() != null) {
                    logger.error("Bulk operation error: ${item}")
                }
            }
        }
    }

    fun bulkUpsertWithRetry(products: List<ProductDocument>, maxRetries: Int = 3) {
        var attempt = 0
        var failedProducts = products

        while (failedProducts.isNotEmpty() && attempt < maxRetries) {
            attempt++
            val bulkRequest = BulkRequest.Builder()

            failedProducts.forEach { product ->
                bulkRequest.operations { op ->
                    op.index { idx ->
                        idx.index("products")
                            .id(product.id)
                            .document(product)
                    }
                }
            }

            val response = openSearchClient.bulk(bulkRequest.build())

            failedProducts = response.items()
                .filter { it.operationName() != null && it.result() == "error" }
                .mapNotNull { /* extract original doc if possible */ }

            if (failedProducts.isNotEmpty()) {
                logger.warn("Bulk attempt $attempt failed for ${failedProducts.size} docs, retrying...")
                Thread.sleep((100 * (2 to the power of attempt)).toLong()) // exponential backoff
            }
        }
    }
}
```

### StreamingBulk (For Large Datasets)

```kotlin
fun streamIndexLargeDataset(
    productStream: Sequence<ProductDocument>,
    batchSize: Int = 1000
) {
    productStream.chunked(batchSize).forEach { batch ->
        bulkIndexProducts(batch)
    }
}
```

---

## Testing with TestContainers

```kotlin
package com.example.integration

import org.junit.jupiter.api.BeforeAll
import org.junit.jupiter.api.Test
import org.springframework.boot.test.autoconfigure.data.redis.DataRedisTest
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource
import org.testcontainers.containers.GenericContainer
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers

@Testcontainers
@SpringBootTest
class ProductSearchIntegrationTest {

    companion object {
        @Container
        @JvmStatic
        val openSearchContainer = GenericContainer("opensearchproject/opensearch:2.5.0")
            .withExposedPorts(9200)
            .withEnv("discovery.type", "single-node")
            .withEnv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "TestPassword123!")

        @JvmStatic
        @DynamicPropertySource
        fun registerDynamicProperties(registry: DynamicPropertyRegistry) {
            val host = openSearchContainer.host
            val port = openSearchContainer.getMappedPort(9200)
            registry.add("opensearch.host") { host }
            registry.add("opensearch.port") { port }
        }
    }

    @Test
    fun testSearchProducts() {
        val product = ProductDocument(
            id = "1",
            title = "Camping Tent",
            description = "4-season tent",
            price = 150.0,
            category = "Shelter",
            brand = "Coleman",
            inStock = true,
            tags = listOf("tent", "camping")
        )

        val savedProduct = productRepository.save(product)
        assert(savedProduct.id == "1")

        // Refresh index for search
        openSearchClient.indices().refresh { req -> req.index("products") }

        val results = productRepository.findByTitle("Camping")
        assert(results.isNotEmpty())
    }
}
```

---

## Connection & Performance Tuning

### Connection Pooling

The RestClient handles pooling internally. Configure pool size:

```kotlin
@Bean
fun restClient(): RestClient {
    return RestClient.builder(HttpHost(host, port, protocol))
        .setHttpClientConfigCallback { httpClientBuilder ->
            httpClientBuilder
                .setMaxConnTotal(100)  // Max connections overall
                .setMaxConnPerRoute(50) // Max per host
        }
        .setRequestConfigCallback { requestConfig ->
            requestConfig
                .setConnectTimeout(5000)  // 5 seconds
                .setSocketTimeout(60000)  // 60 seconds
        }
        .build()
}
```

### Query Timeout

Prevent long-running queries from hanging:

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .query { q -> q.match { m -> m.field("title").query("expensive query") } }
            .timeout("5s") // timeout=5s
    },
    ProductDocument::class.java
)
```

### Batch Size Tuning

For bulk indexing:

```kotlin
// Too small (100 docs): High overhead, frequent network round-trips
// Too large (10000 docs): High memory usage, slow per-request
// Optimal: 500-2000 docs per batch
bulkIndexProducts(products.chunked(1000).flatten())
```

### Search Caching

OpenSearch caches query results by default. For high-cardinality aggregations:

```kotlin
val response = openSearchClient.search(
    { req ->
        req.index("products")
            .requestCache(true) // Explicitly enable (usually default)
            .query { q -> /* ... */ }
    },
    ProductDocument::class.java
)
```

Avoid caching for:
- User-specific queries (auth, permissions)
- Time-sensitive data (live feeds)
- Rarely-repeated queries (low hit rate wastes memory)

---

## Common Gotchas

### Gotcha 1: Jackson vs Jsonb Serialization

OpenSearch client uses Jackson by default. If you have a custom ObjectMapper:

```kotlin
@Bean
fun objectMapper(): ObjectMapper {
    return ObjectMapper()
        .registerModule(KotlinModule.Builder().build())
        .setSerializationInclusion(JsonInclude.Include.NON_NULL)
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
}
```

Ensure annotations match (use `@JsonProperty`, not `@XmlElement`).

### Gotcha 2: SSL for Localhost

For development, if OpenSearch uses self-signed certs:

```kotlin
val sslContext = SSLContext.getInstance("TLSv1.2").apply {
    val trustManager = object : X509TrustManager {
        override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) {}
        override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {}
        override fun getAcceptedIssuers(): Array<X509Certificate>? = null
    }
    init(null, arrayOf(trustManager), java.security.SecureRandom())
}

val restClient = RestClient.builder(HttpHost(host, port, "https"))
    .setHttpClientConfigCallback { httpClientBuilder ->
        httpClientBuilder.setSSLContext(sslContext)
    }
    .build()
```

**Not for production!** Use proper certificates in production.

### Gotcha 3: Connection Timeouts in Bulk Ops

Bulk requests may take longer than default socket timeout. Increase for bulk operations:

```kotlin
fun bulkIndexWithLongerTimeout(products: List<ProductDocument>) {
    val bulkRequest = BulkRequest.Builder()

    products.forEach { product ->
        bulkRequest.operations { op ->
            op.index { idx ->
                idx.index("products")
                    .id(product.id)
                    .document(product)
            }
        }
    }

    openSearchClient.bulk(
        bulkRequest.build(),
        null // requestOptions with timeout=120s if needed
    )
}
```

### Gotcha 4: Missing Index Refresh After Write

Documents are not immediately searchable after indexing; there's a refresh interval (default 1s).

```kotlin
// Write a document
productRepository.save(product)

// Search immediately - may not find it!
val results = productRepository.findByTitle(product.title)

// Force refresh
openSearchClient.indices().refresh { req -> req.index("products") }

// Now it's findable
val results2 = productRepository.findByTitle(product.title)
```

For tests, always refresh after writes:

```kotlin
@BeforeEach
fun setup() {
    openSearchClient.indices().delete { req -> req.index("products") }
    openSearchClient.indices().create { req -> req.index("products") /* mappings */ }
}

@AfterEach
fun teardown() {
    openSearchClient.indices().refresh { req -> req.index("products") }
}
```

### Gotcha 5: Kotlin Data Class Serialization

If your data class has default values, Jackson may not deserialize correctly:

```kotlin
@Document(indexName = "products")
data class ProductDocument(
    @Id
    val id: String,

    val title: String,

    // Default values in constructor can cause deserialization issues
    val tags: List<String> = emptyList(),

    val inStock: Boolean = true
)

// Fix: Use @JsonProperty with default values, or adjust Jackson config
@Bean
fun objectMapper(): ObjectMapper {
    val mapper = ObjectMapper()
    mapper.registerModule(KotlinModule.Builder()
        .nullToEmptyCollection(true)
        .build()
    )
    return mapper
}
```

### Gotcha 6: Query DSL Builder Null Safety

OpenSearch-java builder is not always null-safe. Avoid:

```kotlin
// This may throw NPE if field is null
req.query { q -> q.match { m -> m.field(nullableField).query(query) } }

// Better: guard nulls
req.query { q ->
    if (nullableField != null) {
        q.match { m -> m.field(nullableField).query(query) }
    } else {
        q.matchAll { }
    }
}
```

---

## Summary for Migration

**Spring Boot/Kotlin + OpenSearch strengths:**
- opensearch-java is official and actively maintained
- Repository pattern reduces boilerplate for CRUD
- Kotlin data classes map naturally to documents
- AWS SigV4 integration is straightforward for managed services

**Differences from Elasticsearch:**
- Client library renamed/rebranded (opensearch-java vs elasticsearch-java)
- Some API slight differences (QueryBuilders → builder DSL)
- Cluster licenses are more permissive (OpenSearch doesn't enforce licensing)

**Key decisions:**
1. Use opensearch-spring-data for simple CRUD, OpenSearchClient for complex queries
2. Tune bulk batch size for your throughput and memory constraints
3. Always refresh after writes in tests
4. Handle SSL certificates properly for production AWS deployments
5. Monitor connection pool and timeout configurations for stability
