# Client Library Migration: Solr to OpenSearch

## Client Library Mapping

| Language | Solr Client | OpenSearch Client | Package |
|----------|------------|-------------------|---------|
| Java | SolrJ | opensearch-java | `org.opensearch.client:opensearch-java:2.18.0` |
| Python | pysolr | opensearch-py | `pip install opensearch-py` |
| Go | Direct HTTP / go-solr | opensearch-go | `go get github.com/opensearch-project/opensearch-go/v2` |
| Node.js | solr-client / HTTP | @opensearch-project/opensearch | `npm install @opensearch-project/opensearch` |
| .NET | SolrNet | opensearch-net | `dotnet add package OpenSearch.Net` |
| Spring | Spring Data Solr | Spring Data OpenSearch | `org.opensearch.spring.data:spring-data-opensearch` |

## Java: SolrJ to opensearch-java

**Dependency change:** Replace `org.apache.solr:solr-solrj` with `org.opensearch.client:opensearch-java:2.18.0`.

**Client init -- before (Solr):**
```java
SolrClient solrClient = new HttpSolrClient.Builder("http://localhost:8983/solr/products").build();
```

**Client init -- after (OpenSearch):**
```java
RestClientTransport transport = new RestClientTransport(
    RestClient.builder(new HttpHost("localhost", 9200)).build(),
    new JacksonJsonpMapper()
);
OpenSearchClient client = new OpenSearchClient(transport);
```

**Query -- before (Solr):**
```java
SolrQuery query = new SolrQuery("title:\"red shoes\"");
query.addFilterQuery("category:footwear");
QueryResponse response = solrClient.query(query);
```

**Query -- after (OpenSearch):**
```java
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q.bool(b -> b
        .must(m -> m.matchPhrase(mp -> mp.field("title").query("red shoes")))
        .filter(f -> f.term(t -> t.field("category").value("footwear")))
    )),
    Product.class
);
```

**Key difference:** SolrJ uses query strings; opensearch-java uses type-safe DSL builders. Full rewrite required -- no backward compatibility.

## Python: pysolr to opensearch-py

**Dependency change:** Replace `pysolr` with `opensearch-py`.

**Client init -- before (Solr):**
```python
import pysolr
solr = pysolr.Solr('http://localhost:8983/solr/products', timeout=10)
```

**Client init -- after (OpenSearch):**
```python
from opensearchpy import OpenSearch
client = OpenSearch(
    hosts=['localhost:9200'],
    http_auth=('admin', 'admin'),
    use_ssl=True,
    verify_certs=False
)
```

**Query -- before (Solr):**
```python
results = solr.search('title:"red shoes"', fq='category:footwear')
```

**Query -- after (OpenSearch):**
```python
response = client.search(index='products', body={
    'query': {'bool': {
        'must': [{'match_phrase': {'title': 'red shoes'}}],
        'filter': [{'term': {'category': 'footwear'}}]
    }}
})
```

**Key difference:** Both use dict/parameter patterns. Migration is lower friction than Java. Async support via `AsyncOpenSearch` and aiohttp.

## Go: HTTP to opensearch-go

**Dependency change:** `go get github.com/opensearch-project/opensearch-go/v2`

**Client init -- after (OpenSearch):**
```go
client, _ := opensearchapi.NewDefaultClient()
```

**Query -- after (OpenSearch):**
```go
req := opensearchapi.SearchRequest{
    Index: []string{"products"},
    Body: strings.NewReader(`{
        "query": {"match": {"title": "running shoes"}}
    }`),
}
res, _ := req.Do(context.Background(), client)
```

**Key difference:** Solr has limited Go ecosystem (most apps use direct HTTP). opensearch-go provides idiomatic Go with built-in connection pooling and goroutine safety.

## Node.js: solr-client to @opensearch-project/opensearch

**Dependency change:** Replace `solr-client` with `@opensearch-project/opensearch`.

**Client init -- after (OpenSearch):**
```javascript
const { Client } = require('@opensearch-project/opensearch');
const client = new Client({
    nodes: ['http://localhost:9200'],
    auth: { username: 'admin', password: 'admin' }
});
```

**Query -- after (OpenSearch):**
```javascript
const response = await client.search({
    index: 'products',
    body: {
        query: { multi_match: { query: 'running shoes', fields: ['title^2', 'description'] } }
    }
});
```

**Key difference:** Promise-based with native async/await. TypeScript types included. Low migration friction from solr-client or direct HTTP.

## Auth Migration

**Solr Basic Auth** typically uses `security.json` in ZooKeeper with username/password.

**OpenSearch Security Plugin** supports multiple auth backends:
- Basic auth (username/password) -- closest to Solr
- TLS client certificates
- SAML / OpenID Connect
- LDAP / Active Directory

**Client-side auth change:**
- All OpenSearch clients accept `http_auth` / `auth` parameters for basic auth
- TLS: configure `use_ssl=True`, `verify_certs=True`, and CA cert path
- For AWS OpenSearch Service: use `AWSV4SignerAuth` (opensearch-py) or `AwsSdk2Transport` (opensearch-java)

**Action item:** Map each Solr user/role to an OpenSearch security role. OpenSearch uses fine-grained access control (index-level, field-level, document-level) which is more granular than Solr's plugin.

## Connection Pooling Differences

| Aspect | Solr (SolrJ) | OpenSearch |
|--------|-------------|------------|
| Protocol | HTTP to Solr nodes or ZooKeeper-managed | HTTP/HTTPS direct to nodes |
| Discovery | ZooKeeper (SolrCloud) | Static host list or sniffing |
| Pooling | Apache HttpClient pool | Built-in per client library |
| Failover | ZooKeeper-based leader election | Round-robin with retry |

**Best practices for OpenSearch clients:**
- Create one client instance per service, reuse across requests. Never create per-request.
- Configure multiple hosts for failover: all clients support host lists.
- Set explicit timeouts: connect (5s), socket (60s).
- Use `max_retries=3` and `retry_on_timeout=True` for transient failures.
- For bulk indexing: use the bulk API with 1000-5000 docs per batch, not single-doc loops.
