# Platform Integration: Application-Layer Migration

**Scope:** Migrating the application code that talks to Solr — client libraries, query construction, response parsing, connection management — to OpenSearch equivalents.
**Audience:** Software engineers, architects, and consultants working on the "last mile" of a migration.
**Last reviewed:** 2026-03-19 | **Reviewer:** AI draft — needs expert review

---

## What This Reference Covers (and Doesn't)

A Solr-to-OpenSearch migration has two distinct workstreams:

1. **Engine-side:** Schema translation, query mapping, index settings, cluster configuration — covered by the other reference chunks in this skill.
2. **Application-side:** Changing the code that *talks to* the search engine — client libraries, query construction, response parsing, auth, connection pooling. **This is what this reference covers.**

The application layer is where the migration becomes visible to developers. Even if the engine-side mapping is perfect, the migration isn't done until application code can construct queries, parse responses, and handle errors against OpenSearch instead of Solr.

### What the application layer is NOT

The application layer is **not a search UI.** In the demos in this repository (e.g., `03-specs/techproducts-demo/`), we include a minimal Spring Boot app as a "Hello Search" verification tool — similar in spirit to the Velocity ResponseWriter that Solr used to ship for quick result inspection. Its purpose is to prove that queries run, results come back, and the integration works. It is not a product UI, and it is not the point of the migration.

The real application-layer migration work is in the **service code** that sits between your product and the search engine: the query builders, the indexing pipelines, the response mappers, and the error handling.

---

## Key Judgements

1. **The application layer is where migrations stall.** Engine-side work (schema, mappings, settings) is tractable because it's configuration. Application-side work touches production code, requires developer time, and competes with feature work. Budget for it explicitly.

2. **Don't leak engine details into business logic.** Your application should ask for "search results," not "Elasticsearch Boolean Queries." If your service layer imports `org.opensearch.client.*` in 30 files, you have a migration problem *and* a maintenance problem.

3. **The client library swap is mechanical; the query construction rewrite is not.** Changing `SolrClient` to `OpenSearchClient` is find-and-replace. Rewriting query construction from Solr's query-string syntax to OpenSearch's Query DSL JSON is a design task that requires understanding what each query *means*, not just what it *says*.

4. **Dual-write lives in the application layer.** The engine doesn't know about dual-write — your application code decides where to send writes. This means the application team owns the most critical phase of the migration (dual-write + gradual cutover), not the search team.

5. **Auth changes are the sleeper issue.** Solr typically uses simple HTTP or ZooKeeper-based auth. AWS OpenSearch uses SigV4 request signing. This touches every HTTP call and often requires new dependencies, IAM roles, and credential management. Don't discover this in week 6.

---

## Platform-Specific Migration Guides

### JVM (Java / Kotlin) — SolrJ → opensearch-java

**Client library swap:**

| Solr | OpenSearch | Notes |
|------|-----------|-------|
| `SolrJ` (CloudSolrClient) | `opensearch-java` (OpenSearchClient) | Different API style: SolrJ is method-chaining, opensearch-java is builder-pattern |
| `SolrQuery` object | `SearchRequest` + Query DSL builders | No query-string shorthand — must use builder API or raw JSON |
| `SolrInputDocument` | `IndexRequest` with Map or POJO | Similar concept, different serialization |
| `QueryResponse` → `SolrDocumentList` | `SearchResponse` → `Hit<T>` | Response structure differs significantly |
| ZooKeeper-based discovery | Direct endpoint or service discovery | No ZK equivalent — use DNS, load balancer, or AWS endpoint |

**SigV4 authentication (AWS OpenSearch Service):**

```java
// Java — using AWS SDK v2 request interceptor
OpenSearchClient client = new OpenSearchClient(
    new AwsSdk2TransportBuilder()
        .region(Region.US_EAST_1)
        .service("es")
        .build()
);
```

```kotlin
// Kotlin — same pattern, Kotlin syntax
val transport = AwsSdk2TransportBuilder()
    .region(Region.US_EAST_1)
    .service("es")
    .build()
val client = OpenSearchClient(transport)
```

**Query construction — before and after:**

```java
// SolrJ: query-string style
SolrQuery query = new SolrQuery("search terms");
query.set("defType", "edismax");
query.set("qf", "title^3 body^1");
query.addFilterQuery("status:active");
query.setFacet(true);
query.addFacetField("category");

// opensearch-java: builder style
SearchRequest request = SearchRequest.of(s -> s
    .index("products")
    .query(q -> q.bool(b -> b
        .must(m -> m.multiMatch(mm -> mm
            .query("search terms")
            .fields("title^3", "body^1")))
        .filter(f -> f.term(t -> t
            .field("status").value("active")))))
    .aggregations("by_category", a -> a
        .terms(t -> t.field("category").size(20)))
);
```

**Common mistakes (JVM):**
- Using `RestHighLevelClient` (Elasticsearch legacy) instead of `OpenSearchClient` — it works initially but breaks on version-specific features and sends wrong compatibility headers.
- Forgetting to close the client / connection pool — SolrJ is forgiving about this, opensearch-java is not.
- Assuming `SolrJ`'s automatic retry/failover behavior carries over — it doesn't. OpenSearch client retry is configured differently.

---

### Python — pysolr / solrpy → opensearch-py

**Client library swap:**

| Solr | OpenSearch | Notes |
|------|-----------|-------|
| `pysolr.Solr` | `opensearchpy.OpenSearch` | Similar connection model |
| `solr.search(q='...')` | `client.search(index='...', body={...})` | Query-string → JSON body |
| `solr.add([docs])` | `helpers.bulk(client, actions)` | Bulk helper for indexing |
| Dict response | Dict response | Similar structure, different keys |

**Query construction — before and after:**

```python
# pysolr
results = solr.search(
    'search terms',
    **{
        'defType': 'edismax',
        'qf': 'title^3 body^1',
        'fq': 'status:active',
        'facet': 'true',
        'facet.field': 'category',
    }
)
for doc in results.docs:
    print(doc['title'])

# opensearch-py
results = client.search(
    index='products',
    body={
        'query': {
            'bool': {
                'must': [{'multi_match': {
                    'query': 'search terms',
                    'fields': ['title^3', 'body^1']
                }}],
                'filter': [{'term': {'status': 'active'}}]
            }
        },
        'aggs': {
            'by_category': {'terms': {'field': 'category', 'size': 20}}
        }
    }
)
for hit in results['hits']['hits']:
    print(hit['_source']['title'])
```

**SigV4 authentication (AWS):**

```python
from opensearchpy import OpenSearch, RequestsAWSV4SignerAuth
import boto3

credentials = boto3.Session().get_credentials()
auth = RequestsAWSV4SignerAuth(credentials, 'us-east-1', 'es')
client = OpenSearch(
    hosts=[{'host': 'search-xxx.us-east-1.es.amazonaws.com', 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    connection_class=RequestsHttpConnection,
)
```

**Common mistakes (Python):**
- Using `elasticsearch-py` instead of `opensearch-py` — they forked and are diverging. Use the right client for the right engine.
- Not using `helpers.bulk()` for indexing — single-document indexing is 10-50x slower.
- Passing Solr query syntax strings in the `q` parameter — OpenSearch expects Query DSL JSON, not Lucene query strings (unless you explicitly use `query_string` query type, which has different parsing rules).

---

### Other Platforms

**PHP (Solarium → opensearch-php):**
- Solarium's fluent query builder has no OpenSearch equivalent — queries must be constructed as associative arrays matching Query DSL.
- Laravel Scout has an OpenSearch driver, but it's limited. For complex queries, use the client directly.

**Ruby (rsolr → opensearch-ruby):**
- Similar pattern to Python: hash-based query construction replaces query-string parameters.
- The `searchkick` gem supports OpenSearch and provides a higher-level abstraction.

**Node.js (@opensearch-project/opensearch-js):**
- JavaScript object literals map naturally to Query DSL JSON — often the easiest migration.
- Use the official `@opensearch-project/opensearch-js` client, not the Elasticsearch client.

**.NET (SolrNet → OpenSearch.Client):**
- OpenSearch.Client (NEST fork) provides a strongly-typed query DSL that maps well to the JSON API.
- Connection management and authentication differ significantly from SolrNet.

For all platforms: the query translation patterns are the same regardless of language. The skill's query syntax mapping reference (`query-syntax-mapping.md` in `01-sources/`) covers every Solr query pattern and its OpenSearch equivalent. The client library is just the delivery mechanism.

---

## Abstraction Patterns

These patterns apply regardless of language or framework. They make the initial migration easier *and* protect against future engine changes.

### Interface Segregation

Define a search service interface. The implementation (Solr or OpenSearch) is injected via DI.

```
// Pseudo-code — adapt to your language
interface SearchService {
    search(query: String, filters: Map, facets: List) -> SearchResults
    index(documents: List<Document>) -> IndexResult
    delete(ids: List<String>) -> DeleteResult
}

class OpenSearchSearchService implements SearchService { ... }
class SolrSearchService implements SearchService { ... }  // keep during dual-write
```

During dual-write, both implementations exist. After cutover, the Solr implementation is deleted.

### Query Factory

Build a factory that takes domain-specific input and returns engine-specific queries. This isolates the Query DSL from business logic.

```
// Domain layer asks for what it wants
val results = queryFactory.productSearch(
    terms = "industrial pump",
    category = "hydraulics",
    minPrice = 100.0
)

// Query factory translates to engine-specific DSL
// This is the ONLY place that knows about OpenSearch Query DSL
```

### Domain DTOs

Never pass raw search engine responses to your UI or API layer. Map to engine-agnostic domain objects.

```
// Bad: leaking engine internals
return response.getHits().getHits()  // OpenSearch-specific

// Good: mapping to domain
return response.getHits().getHits().map { hit ->
    ProductResult(
        id = hit.id,
        title = hit.source["title"],
        score = hit.score
    )
}
```

---

## Decision Heuristics

- **If your app imports the search client in more than 3 files → refactor before migrating.** Wrap the client behind an interface first, then swap the implementation. Migrating scattered client calls is error-prone and untestable.
- **If you're building a "Hello Search" demo app → keep it minimal.** Its job is to prove the integration works, not to be a product. A single endpoint that runs 5 representative queries and shows results is enough. Think Solr's old Velocity template, not a production UI.
- **If the application team has no OpenSearch experience → pair them with the search team for query construction.** The client library swap is mechanical, but writing correct Query DSL requires understanding search semantics, not just API syntax.
- **If auth is changing (e.g., ZK → SigV4) → prototype the auth integration first, before any query work.** Auth failures are binary (everything breaks) and easy to test. Get this working in week 1.
- **If you have more than one application consuming Solr → inventory all consumers before changing any of them.** Hidden consumers are the #1 source of post-cutover incidents. See `consulting-methodology.md` → Common Issues.

---

## Common Pitfalls

1. **The "Hardcoded JSON" Disaster:** A team had 50+ lines of raw Elasticsearch JSON DSL hardcoded in their service layer. When they moved from OpenSearch 1.x to 2.x, 20% of their queries broke due to deprecated field types. They spent 2 weeks doing find-and-replace instead of updating a central query factory. **Lesson:** Centralize query construction.

2. **The "Global Exception" Trap:** An app caught *every* exception from the search client and returned a generic "Search Unavailable" error. When OpenSearch returned a 400 (bad query syntax), the team assumed the *cluster* was down and restarted infrastructure, causing a 30-minute outage. **Lesson:** Distinguish client errors (4xx) from server errors (5xx). Handle them differently.

3. **The "Wrong Client" Drift:** A team used the Elasticsearch client library to talk to OpenSearch because "it mostly works." It did — until they needed a feature that diverged between the forks. By then, they had 40 files importing `elasticsearch-java` and a painful swap ahead. **Lesson:** Use the correct client library from day one.

4. **The "Forgotten Consumer":** A migration team updated the main web application but forgot that a nightly reporting job also queried Solr directly via HTTP. After Solr was decommissioned, the reporting job silently failed for two weeks before anyone noticed. **Lesson:** Inventory all consumers, not just the primary application.

---

## Open Questions / Evolving Guidance

- Should the skill include framework-specific guidance (e.g., Spring Data OpenSearch, Django Haystack) or stay at the client-library level? Framework abstractions add convenience but hide engine-specific behavior that matters during migration.
- How do we handle the growing number of OpenSearch client forks and compatibility layers? The ecosystem is fragmenting.
- Should we provide a reference "Hello Search" app template in multiple languages, or is one worked example (techproducts-demo in Spring Boot/Kotlin) sufficient?
