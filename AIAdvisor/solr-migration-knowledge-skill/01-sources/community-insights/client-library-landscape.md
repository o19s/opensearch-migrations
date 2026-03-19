# OpenSearch Client Library Landscape: Multi-Language & Framework Guide

## Overview
OpenSearch provides official client libraries for multiple programming languages. This guide covers architecture, capabilities, and migration paths from Solr clients across the polyglot ecosystem.

## Official OpenSearch Client Libraries

### 1. Java Client

#### opensearch-java (Modern, Recommended)
**Status**: Official, actively maintained
**Minimum Java**: Java 8+
**Latest**: 2.x+ (tracking OpenSearch 2.0+ API)

**Architecture:**
- API client: Type-safe DSL for queries, indices, cluster operations
- Transport layer: HTTP connections with connection pooling
- Built on: Java 11 internals, Netty for async I/O
- No Elasticsearch dependency (fully OpenSearch-native)

**Maven:**
```xml
<dependency>
    <groupId>org.opensearch.client</groupId>
    <artifactId>opensearch-java</artifactId>
    <version>2.18.0</version>
</dependency>
```

**Basic Usage:**
```java
// Connection
RestClientTransport transport = new RestClientTransport(
    RestClient.builder(
        new HttpHost("localhost", 9200)
    ).build(),
    new JacksonJsonpMapper()
);
OpenSearchClient client = new OpenSearchClient(transport);

// Search
SearchResponse<Object> response = client.search(s -> s
    .index("products")
    .query(q -> q
        .match(m -> m
            .field("title")
            .query(v -> v.stringValue("running shoes"))
        )
    ),
    Object.class
);
```

**Key Features:**
- ✅ Type-safe query builder (compile-time checking)
- ✅ Full OpenSearch API coverage (2.0+)
- ✅ Async/non-blocking support
- ✅ Custom serialization
- ✅ Convenient builders for complex queries
- ✅ Active development, regular updates

**From Solr Migration:**
- Solr: SolrJ uses query strings; OpenSearch Java uses DSL builders
- Learning curve: Moderate (new query syntax)
- Compatibility: Not backward-compatible (rewrite required)

#### Legacy RestHighLevelClient (Deprecated ⚠️)
**Status**: Deprecated as of Elasticsearch 7.15+
**Usage**: Migration away required

**Why deprecated:**
- Was tied to Elasticsearch versioning (confusion with ES 8.x)
- opensearch-java is cleaner abstraction
- Maintenance burden

**Migration path:**
- For existing code using RestHighLevelClient: Upgrade to opensearch-java
- For Solr migration: Use opensearch-java directly

### 2. Python Client

#### opensearch-py (Modern, Recommended)
**Status**: Official, actively maintained
**Python**: 3.6+
**Latest**: 2.x+ (tracking OpenSearch versions)

**Installation:**
```bash
pip install opensearch-py
```

**Basic Usage:**
```python
from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=['localhost:9200'],
    http_auth=('admin', 'admin'),
    use_ssl=True,
    verify_certs=False,
    ssl_show_warn=False
)

response = client.search(
    index='products',
    body={
        'query': {
            'multi_match': {
                'query': 'running shoes',
                'fields': ['title^2', 'description']
            }
        },
        'size': 10
    }
)
```

**Key Features:**
- ✅ Pure Python implementation
- ✅ Dict-based query construction (Pythonic)
- ✅ Connection pooling
- ✅ Async support (via aiohttp)
- ✅ Bulk operations
- ✅ Good community support

**From Solr Migration:**
- Solr: pysolr uses parameter dictionaries; OpenSearch uses nested dicts
- Learning curve: Low (similar to SolrCloud clients)
- Compatibility: Good for existing Python search code

#### Async (Asyncio) Support:
```python
from opensearchpy import AsyncOpenSearch

async def search_async():
    async with AsyncOpenSearch(hosts=['localhost:9200']) as client:
        response = await client.search(index='products', body=query)
        return response
```

### 3. Go Client

#### opensearch-go (Modern, Recommended)
**Status**: Official, actively maintained
**Go**: 1.11+
**Latest**: 2.x+

**Installation:**
```bash
go get github.com/opensearch-project/opensearch-go/v2
```

**Basic Usage:**
```go
client, _ := opensearchapi.NewDefaultClient()

req := opensearchapi.SearchRequest{
    Index: []string{"products"},
    Body: strings.NewReader(`{
        "query": {
            "multi_match": {
                "query": "running shoes",
                "fields": ["title^2", "description"]
            }
        }
    }`),
}

res, _ := req.Do(context.Background(), client)
```

**Key Features:**
- ✅ Idiomatic Go (interfaces, goroutines)
- ✅ Built-in connection pool
- ✅ Bulk API support
- ✅ Streaming responses
- ✅ Plugin support via SDK
- ✅ Excellent documentation

**From Solr Migration:**
- Solr: Limited Go ecosystem; most use HTTP directly
- Learning curve: Moderate (new client paradigm)
- Compatibility: Good for new services

### 4. JavaScript/Node.js Client

#### @opensearch-project/opensearch (Modern, Recommended)
**Status**: Official, actively maintained
**Node**: 14+
**Latest**: 2.x+

**Installation:**
```bash
npm install @opensearch-project/opensearch
```

**Basic Usage:**
```javascript
const { Client } = require('@opensearch-project/opensearch');

const client = new Client({
    nodes: ['http://localhost:9200'],
    auth: {
        username: 'admin',
        password: 'admin'
    }
});

const response = await client.search({
    index: 'products',
    body: {
        query: {
            multi_match: {
                query: 'running shoes',
                fields: ['title^2', 'description']
            }
        }
    }
});
```

**Key Features:**
- ✅ Promise-based (native async/await)
- ✅ TypeScript support
- ✅ Bulk indexing
- ✅ Full OpenSearch API
- ✅ Browser-compatible (limited, CORS restrictions)
- ✅ Active development

**From Solr Migration:**
- Solr: solr-client npm or direct HTTP
- Learning curve: Low (familiar REST patterns)
- Compatibility: Good for existing JavaScript code

### 5. .NET Client

#### opensearch-net (Modern, Recommended)
**Status**: Official (NEST port)
**Framework**: .NET 4.6+, .NET Core 2.1+, .NET 5/6/7/8
**Latest**: 1.x+

**NuGet:**
```bash
dotnet add package OpenSearch.Net
```

**Basic Usage:**
```csharp
var client = new OpenSearchClient(
    new Uri("http://localhost:9200")
);

var response = await client.SearchAsync<Product>(s => s
    .Index("products")
    .Query(q => q
        .MultiMatch(m => m
            .Query("running shoes")
            .Fields("title^2", "description")
        )
    )
);
```

**Key Features:**
- ✅ LINQ support (IQueryable)
- ✅ Type-safe query builders
- ✅ Async/await first-class
- ✅ Strongly-typed documents
- ✅ Connection pooling
- ✅ POCO mapping

**From Solr Migration:**
- Solr: SolrNet (community) or direct HTTP
- Learning curve: Low (familiar .NET patterns)
- Compatibility: Excellent for .NET shops

## Framework-Specific Integrations

### Spring Data OpenSearch (Java Spring Boot)

**Dependency:**
```xml
<dependency>
    <groupId>org.opensearch.spring.data</groupId>
    <artifactId>spring-data-opensearch</artifactId>
    <version>1.0.x</version>
</dependency>
```

**Usage:**
```java
@Document(indexName = "products")
public class Product {
    @Id
    private String id;

    @Field(type = FieldType.Text)
    private String title;

    @Field(type = FieldType.Text, analyzer = "standard")
    private String description;
}

public interface ProductRepository extends
    OpenSearchRepository<Product, String> {
    List<Product> findByTitle(String title);
    List<Product> findByTitleAndDescription(String title, String description);
}
```

**Features:**
- ✅ Repository pattern (Spring Data abstraction)
- ✅ Query method generation
- ✅ Transaction management
- ✅ Integration with Spring boot auto-config
- ✅ Familiar Spring ecosystem

**From Solr Migration:**
- Solr: Spring Data Solr (similar but Solr-specific)
- Migration path: Direct swap if using Spring Data
- Effort: Low to medium (method naming conventions differ)

### FastAPI / Python Async

**Integration:**
```python
from fastapi import FastAPI
from opensearchpy import AsyncOpenSearch

app = FastAPI()
client = AsyncOpenSearch(hosts=['localhost:9200'])

@app.get("/search")
async def search(q: str):
    results = await client.search(
        index='products',
        body={'query': {'match': {'title': q}}}
    )
    return results['hits']['hits']
```

**Benefits:**
- ✅ Native async throughout stack
- ✅ Efficient resource usage
- ✅ High concurrency
- ✅ No thread pool overhead

### Express.js / Node.js

**Integration:**
```javascript
const express = require('express');
const { Client } = require('@opensearch-project/opensearch');

const app = express();
const client = new Client({ nodes: ['http://localhost:9200'] });

app.get('/search', async (req, res) => {
    try {
        const result = await client.search({
            index: 'products',
            body: { query: { match: { title: req.query.q } } }
        });
        res.json(result.body.hits.hits);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});
```

## Connection Management Patterns

### Pattern 1: Connection Pooling (Recommended)

**Java Example:**
```java
// Create once, reuse across application
RestClientTransport transport = new RestClientTransport(
    RestClient.builder(
        new HttpHost("localhost", 9200),
        new HttpHost("localhost", 9201),
        new HttpHost("localhost", 9202)
    )
    .setRequestConfigCallback(
        config -> config.setConnectTimeout(5000)
            .setSocketTimeout(60000)
    )
    .build(),
    new JacksonJsonpMapper()
);

OpenSearchClient client = new OpenSearchClient(transport);

// Use throughout application lifecycle
// Close when done
transport.close();
```

**Python Example:**
```python
client = OpenSearch(
    hosts=['localhost:9200', 'localhost:9201', 'localhost:9202'],
    max_retries=3,
    retry_on_timeout=True,
    http_auth=('admin', 'admin'),
    use_ssl=True
)

# Auto connection pooling by library
# Single client instance for entire app
```

### Pattern 2: Retry and Circuit Breaker

**Java with Failover:**
```java
RestClient restClient = RestClient.builder(
    new HttpHost("primary.opensearch.local", 9200),
    new HttpHost("secondary.opensearch.local", 9200)
)
.setFailureListener(new RestClient.FailureListener() {
    @Override
    public void onFailure(Node node) {
        log.warn("Node failed: {}", node.getHost());
    }
})
.build();
```

**Python with Retries:**
```python
client = OpenSearch(
    hosts=[
        {'host': 'opensearch1.local', 'port': 9200},
        {'host': 'opensearch2.local', 'port': 9200}
    ],
    max_retries=3,
    retry_on_timeout=True,
    timeout=30
)
```

**Go with Circuit Breaker Pattern:**
```go
cfg := opensearchconfig.Config{
    Addresses: []string{"http://opensearch1.local:9200", "http://opensearch2.local:9200"},
    DiscoverNodesOnStart: false,
    MaxRetries: 3,
}

client, _ := opensearchapi.NewClient(cfg)

// Add custom retry logic if needed
```

### Pattern 3: Bulk Operations

**Java:**
```java
BulkRequest.Builder br = new BulkRequest.Builder();

for (Product p : products) {
    br.operations(op -> op
        .index(idx -> idx
            .index("products")
            .id(p.getId())
            .document(p)
        )
    );
}

BulkResponse result = client.bulk(br.build());

if (result.errors()) {
    log.error("Bulk had errors");
    result.items().forEach(item -> {
        if (item.error() != null) {
            log.error("Error: {}", item.error().reason());
        }
    });
}
```

**Python:**
```python
from opensearchpy import helpers

actions = [
    {
        "_index": "products",
        "_id": p['id'],
        "_source": p
    }
    for p in products
]

success_count, errors = helpers.bulk(client, actions)
print(f"Indexed {success_count}, errors: {errors}")
```

## Migration from Solr Clients

### Solr → OpenSearch Mapping

| Solr (Java) | OpenSearch (Java) |
|-------------|------------------|
| SolrClient | OpenSearchClient |
| QueryResponse | SearchResponse |
| SolrInputDocument | Map<String, Object> |
| SolrQuery | SearchRequest (builder) |
| CloudSolrClient | OpenSearchClient (same) |

### Query Syntax Translation

**Solr QueryParser:**
```
title:"red shoes" AND category:footwear
```

**OpenSearch Query DSL:**
```json
{
  "bool": {
    "must": [
      { "match_phrase": { "title": "red shoes" } },
      { "term": { "category": "footwear" } }
    ]
  }
}
```

**Client API Translation:**

Solr SolrJ:
```java
SolrQuery query = new SolrQuery("title:\"red shoes\"");
query.addFilterQuery("category:footwear");
QueryResponse response = solrClient.query(query);
```

OpenSearch Java:
```java
SearchRequest request = new SearchRequest.Builder()
    .query(q -> q
        .bool(b -> b
            .must(m -> m
                .matchPhrase(mp -> mp
                    .field("title")
                    .query("red shoes")
                )
            )
            .filter(f -> f
                .term(t -> t
                    .field("category")
                    .value("footwear")
                )
            )
        )
    )
    .build();
```

## Multi-Stack Considerations

### Polyglot Environment (Java + Python + Node)

**Shared Index Configuration:**
- Version OpenSearch cluster centrally
- Sync index mappings via git-controlled templates
- Use integration tests across languages

**Example Multi-Language Setup:**
```
/opensearch-config
  /mappings
    products.json
    logs.json
  /policies
    index-lifecycle.json

/java-service
  src/main/java/Product.java (matches products.json)

/python-service
  models/product.py (matches products.json)

/node-service
  types/product.ts (matches products.json)
```

**Consistency Testing:**
```bash
# Test that all language clients can:
# 1. Index documents
# 2. Query successfully
# 3. Parse results consistently

docker-compose up opensearch
./test-all-clients.sh  # Runs test suite for Java, Python, Node
```

### Coordination Across Services

**Service Discovery:**
```yaml
# All services resolve OpenSearch via DNS
opensearch-cluster.internal:9200

# Or via environment config
OPENSEARCH_HOSTS=opensearch-0.service.consul:9200,opensearch-1.service.consul:9200
```

**Shared Monitoring:**
```
Metrics:
- Query latency across all client libraries
- Index rate (docs/sec)
- Error rate by client type
- Connection pool utilization

Tool: Prometheus + Grafana
Exporter: OpenSearch Prometheus Exporter
```

## Performance Best Practices

### 1. Connection Pooling
- ✅ Single client per service
- ✅ Reuse connections
- ❌ Do NOT create new client per request

### 2. Batch Operations
- ✅ Use bulk API for indexing (1000-5000 docs per batch)
- ✅ Group queries when possible
- ❌ Single-document indexing in loops

### 3. Caching
- ✅ Cache filter queries (constant score queries)
- ✅ Cache aggregation results
- ❌ Cache full-text search results (query-dependent)

### 4. Query Optimization
- ✅ Use term queries (not match) for exact keyword matching
- ✅ Add explicit filter clauses (faster than must)
- ✅ Limit aggregation depth
- ❌ Unbounded faceting

## Testing & Development

### Unit Testing with Mock/Testcontainers

**Java with Testcontainers:**
```java
@Testcontainers
class ProductSearchTest {
    @Container
    static final GenericContainer<?> opensearch =
        new GenericContainer<>("opensearchproject/opensearch:2.11.1")
            .withEnv("DISABLE_SECURITY_PLUGIN", "true")
            .withExposedPorts(9200);

    @Test
    void testSearch() {
        // opensearch.getHost(), opensearch.getFirstMappedPort()
    }
}
```

**Python with Docker:**
```python
import pytest
from testcontainers.opensearch import OpenSearchContainer

@pytest.fixture(scope="session")
def opensearch():
    with OpenSearchContainer() as container:
        yield container

def test_search(opensearch):
    client = OpenSearch(hosts=[opensearch.get_url()])
    # test operations
```

## Summary Table: Official Clients

| Language | Library | Status | Version | Async | Spring |
|----------|---------|--------|---------|-------|--------|
| Java | opensearch-java | ✅ Current | 2.x | ✅ | ✅ |
| Python | opensearch-py | ✅ Current | 2.x | ✅ | ❌ |
| Go | opensearch-go | ✅ Current | 2.x | Native | ❌ |
| JavaScript | @opensearch-project/opensearch | ✅ Current | 2.x | ✅ | ❌ |
| .NET | opensearch-net | ✅ Current | 1.x | ✅ | ❌ |

## Conclusion
OpenSearch provides mature, well-maintained clients for all major languages. Migration from Solr clients is straightforward—main work is translating query syntax and adapting to DSL-based query construction. For polyglot environments, coordinate version control and index mapping consistency across services.
