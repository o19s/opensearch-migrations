# Search Relevance and Query Tuning for OpenSearch

**Source:** https://docs.opensearch.org/latest/search-plugins/

## Overview

Search relevance is determined by query strategy, scoring model calibration, and analytical infrastructure. Tuning involves understanding Lucene scoring, leveraging business logic through function_score, and systematic testing via the Explain and Profile APIs.

## BM25 Scoring: Core Algorithm

### Algorithm Basics

BM25 (Best Matching) is the default relevance algorithm in OpenSearch. Score factors:

```
score = IDF(term) × (k1 + 1) × term_freq / (term_freq + k1 × (1 - b + b × doc_length / avg_doc_length))
```

**Components**:
- **IDF (Inverse Document Frequency)**: How rare is this term? (log(total_docs / docs_with_term))
  - Rare terms are more valuable (higher weight)
  - Common terms (the, a, is) have low IDF
- **Term Frequency**: How many times does term appear in document?
  - More appearances = higher score
  - Diminishing returns (k1 parameter controls curve)
- **Document Length Normalization**: Longer documents naturally have more term hits
  - b parameter controls how much to penalize long documents
  - Default b=0.75 (moderate normalization)

### BM25 Parameters

**k1 (term frequency saturation)**:

```json
PUT my-index/_settings
{
  "index.similarity.bm25.k1": 1.2  // default
}
```

- Controls how much additional term matches improve score
- **k1 = 0**: Only IDF matters (position 1 vs position 2 = same score)
- **k1 = 1.2** (default): Reasonable saturation (10th match worth ~10% more than 9th)
- **k1 = 2.0**: High saturation (term frequency matters more)
- **Use case**: Increase k1 for keyword-heavy fields (tags, categories); decrease for text (title, body)

**b (document length normalization)**:

```json
{
  "index.similarity.bm25.b": 0.75  // default
}
```

- **b = 0**: No normalization (long docs always score higher)
- **b = 0.75** (default): Moderate normalization (typical text)
- **b = 1.0**: Full normalization (pure proportional; 2x length = expected 2x term hits)
- **Use case**: Lower b (0.5) for title field (short, normalized); higher b (0.9) for body (varies wildly)

### Per-Field Tuning

Different field types need different BM25 settings:

```json
PUT product-index/_settings
{
  "index.similarity.title_bm25": {
    "type": "BM25",
    "k1": 0.8,
    "b": 0.5
  },
  "index.similarity.body_bm25": {
    "type": "BM25",
    "k1": 1.2,
    "b": 0.75
  }
}

PUT product-index/_mappings
{
  "properties": {
    "title": {
      "type": "text",
      "similarity": "title_bm25"
    },
    "body": {
      "type": "text",
      "similarity": "body_bm25"
    }
  }
}
```

## function_score for Business Logic

### When to Use function_score

BM25 is IR-optimized but doesn't understand business metrics. Use function_score to boost based on:
- Popularity (sales, views, ratings)
- Freshness (newer articles rank higher)
- Authority (page rank, inbound links)
- Inventory (in-stock products rank higher)
- Personalization (user history, preferences)

### Basic Structure

```json
GET products/_search
{
  "query": {
    "function_score": {
      "query": {
        "multi_match": {
          "query": "laptop",
          "fields": ["title^2", "description"]
        }
      },
      "functions": [
        {
          "filter": {"term": {"in_stock": true}},
          "weight": 2.0
        },
        {
          "field_value_factor": {
            "field": "popularity_score",
            "factor": 1.2,
            "modifier": "log1p"
          }
        },
        {
          "gauss": {
            "release_date": {
              "origin": "now",
              "scale": "30d",
              "decay": 0.5
            }
          }
        }
      ],
      "boost_mode": "multiply",
      "score_mode": "sum"
    }
  }
}
```

**Functions**:
- **filter + weight**: Conditional boost (if in_stock, multiply by 2.0)
- **field_value_factor**: Boost based on numeric field value
- **gauss/linear/exponential**: Decay boost based on distance from origin

### Boost Modes

**multiply** (default):
```
final_score = base_score × function_score
```
- Multiplicative effect (functions amplify or dampen)
- Relevance order preserved (relevant docs stay relevant)

**sum**:
```
final_score = base_score + function_score
```
- Additive (useful for combining independent signals)
- Can elevate low-relevance docs if function score is high

**replace**:
```
final_score = function_score
```
- Ignore query relevance entirely (use only business metrics)
- Rarely recommended (loses relevance signal)

## Multi-Field Search Strategies

### best_fields (Default for most queries)

```json
{
  "multi_match": {
    "query": "quick brown fox",
    "fields": ["title^2", "body"],
    "type": "best_fields",
    "operator": "OR"
  }
}
```

**Behavior**:
- Document must match one field
- Uses highest-scoring field for final score
- Matches against each field independently
- Example: "quick" in title (high score) vs. "brown fox" in body (lower score) = document scores on title match

**Best for**: Multi-field search where one field has higher quality (e.g., title > body)

**Scoring**: 
```
score = max(title_score, body_score)
```

### cross_fields (Distribute terms across fields)

```json
{
  "multi_match": {
    "query": "john smith",
    "fields": ["first_name", "last_name"],
    "type": "cross_fields",
    "operator": "AND"
  }
}
```

**Behavior**:
- Terms can be spread across fields
- All terms must match (AND logic)
- IDF computed across all fields (avoids field-specific term weighting)

**Example**:
- "john smith" matches: first_name=john AND last_name=smith (high score)
- Also matches: first_name="john smith" (not matched; phrase requires adjacency)

**Best for**: Structured data where terms naturally distribute (name, address, location)

### most_fields (Maximize term coverage)

```json
{
  "multi_match": {
    "query": "quick brown fox",
    "fields": ["title", "title.english", "title.synonym"],
    "type": "most_fields"
  }
}
```

**Behavior**:
- Matches query against each field, scores all matches
- Document score = sum of all matching field scores
- Assumes multiple fields represent same data (with different analyzers)

**Best for**: Query-time synonym expansion or language-specific analyzers

**Example**:
- title="quick brown fox" (matched, high score)
- title.english="quick brown fox" (matched via stemmed analyzer)
- title.synonym="swift brown fox" (matched via synonym)
- Final score = sum (document gets credit for multiple matches)

## Analyzers for Relevance

### Analyzer Selection Impact

Analyzers tokenize documents and queries, affecting what matches:

```json
PUT books/_mappings
{
  "properties": {
    "title": {
      "type": "text",
      "analyzer": "english"  // stemming, stopword removal
    },
    "title_exact": {
      "type": "keyword"  // no analysis
    }
  }
}
```

**Example**: Query "running books"
- With `english` analyzer: matches "run", "runs", "runner" (stemming enabled)
- With default analyzer: matches only exact "running" (stemming disabled)

### Stopword Removal

```json
PUT books/_settings
{
  "analysis": {
    "analyzer": {
      "my_analyzer": {
        "type": "custom",
        "tokenizer": "standard",
        "filter": ["lowercase", "stop"]
      }
    }
  }
}
```

- **Standard stopwords** (the, a, is, of): Usually removed (high noise, low value)
- **Risk**: Phrase queries "to be or not to be" lose meaning
- **Alternative**: Keep stopwords but downweight them

### Stemming and Lemmatization

```json
{
  "analysis": {
    "analyzer": {
      "english": {
        "type": "custom",
        "tokenizer": "standard",
        "filter": ["lowercase", "english_stemmer"]
      }
    },
    "filter": {
      "english_stemmer": {
        "type": "stemmer",
        "language": "light_english"
      }
    }
  }
}
```

**Stemming**:
- running → run, jumped → jump (aggressive, can over-match)
- Example: "running" matches "run" (might be false positive in some contexts)

**Lemmatization**:
- running → run, better → good (semantic understanding)
- More accurate, higher CPU cost

**Choice**: Stemming for recall (find all variations); lemmatization for precision (avoid false matches)

### Synonym Filters

```json
{
  "analysis": {
    "filter": {
      "synonym_filter": {
        "type": "synonym",
        "synonyms": [
          "quick,fast,rapid",
          "smart,intelligent,clever",
          "laptop,notebook"
        ]
      }
    }
  }
}
```

**Two approaches**:

1. **Index-time synonyms** (at index creation):
   - Expand "quick" → "quick fast rapid" (larger index)
   - Best for common synonyms (maximize recall)
   - Query: "quick" matches docs with "fast" or "rapid"

2. **Query-time synonyms** (at search):
   - Expand query "quick" → "quick fast rapid"
   - Smaller index, slower queries
   - Best for rare synonyms (avoid index bloat)

## Percolate Queries for Alerting

### Use Case: Reverse Search

Instead of "find documents matching query", use "which saved queries match this new document?"

```json
PUT alerts/_doc/alert-1
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "error"}},
        {"match": {"message": "database connection failed"}}
      ]
    }
  }
}

PUT alerts/_doc/alert-2
{
  "query": {
    "range": {"response_time_ms": {"gte": 5000}}
  }
}
```

**Percolate new log entry**:

```json
GET alerts/_search
{
  "query": {
    "percolate": {
      "field": "query",
      "document": {
        "level": "error",
        "message": "database connection failed to production db",
        "response_time_ms": 1200
      }
    }
  }
}
```

**Result**: Returns alert-1 (matches error + database connection)

**Use cases**:
- Real-time alerting (new logs trigger matching alerts)
- Content distribution (new articles trigger subscriptions)
- Fraud detection (new transactions match suspicious patterns)

## Search Templates for Consistency

### Parameterized Queries

```json
PUT _search/template/product-search
{
  "script": {
    "source": """
    {
      "query": {
        "multi_match": {
          "query": "{{query}}",
          "fields": ["title^2", "description"],
          "operator": "{{operator|default 'OR'}}"
        }
      },
      "from": {{from|default 0}},
      "size": {{size|default 10}}
    }
    """,
    "lang": "mustache"
  }
}

GET products/_search/template
{
  "id": "product-search",
  "params": {
    "query": "laptop",
    "operator": "AND",
    "size": 20
  }
}
```

**Benefits**:
- Consistency (all clients use same query logic)
- Performance (templated queries are cached)
- Governance (QA approves all search patterns)

## Explain API for Debugging Relevance

### Understand Why Documents Score

```json
GET products/_explain/123?pretty
{
  "query": {
    "multi_match": {
      "query": "laptop",
      "fields": ["title^2", "body"]
    }
  }
}
```

**Output**:
```
"explanation" : {
  "value" : 5.12,
  "description" : "sum of:",
  "details" : [
    {
      "value" : 3.2,
      "description" : "weight(title:laptop in 123) = 3.2",
      "details" : [
        {
          "value" : 2.0,
          "description" : "boost"
        },
        {
          "value" : 1.6,
          "description" : "idf, log(1 + (10000 - 123 + 0.5) / (123 + 0.5))"
        }
      ]
    }
  ]
}
```

**Reading**:
- Total score: 5.12
- Breakdown: title field (3.2) + body field (1.92)
- boost^2 from "title^2" field weighting
- IDF calculated from corpus stats

**Debugging**:
- "Why didn't document X rank higher?" → Explain shows scoring breakdown
- Identify missing field matches or low IDF terms

## Profile API for Query Performance

### Identify Slow Queries

```json
GET products/_search
{
  "profile": true,
  "query": {
    "bool": {
      "must": [
        {"match": {"title": "laptop"}},
        {"range": {"price": {"lte": 1000}}}
      ]
    }
  }
}
```

**Output** (abbreviated):
```
"profile" : {
  "shards" : [
    {
      "searches" : [
        {
          "query" : [
            {
              "type" : "BooleanQuery",
              "description" : "title:laptop price:[* TO 1000]",
              "time_in_nanos" : 5234000,
              "breakdown" : {
                "create_weight" : 1023000,
                "build_scorer" : 2111000,
                "score" : 2100000
              }
            }
          ]
        }
      ]
    }
  ]
}
```

**Interpretation**:
- Total query time: 5.2 milliseconds
- create_weight: Building term/phrase structures (1ms)
- build_scorer: Creating scoring algorithm (2.1ms)
- score: Actual score calculation (2.1ms)

**Optimizations**:
- If score dominates: Reduce scope (add filters, reduce documents scored)
- If create_weight dominates: Simplify query logic
- If build_scorer dominates: Add indices or filters to reduce shard scope

## Caching Strategies

### Request Cache (Full Query Results)

```json
GET products/_search?request_cache=true
{
  "query": {"match": {"title": "laptop"}}
}
```

- Caches full response (query + results)
- Hits when exact same query + parameters requested again
- Invalidated when index is refreshed or updated
- Size limit: `indices.queries.cache.size` (default 10% of heap)

**When to use**:
- Repeated identical queries (dashboards, reports)
- Low cardinality (few unique queries)

**Overhead**:
- Cache invalidation on refresh (frequent refreshes = no benefit)
- Memory cost (results cached in JVM)

### Query Cache (Filter Caching)

```json
PUT products/_settings
{
  "index.queries.cache.enabled": true
}
```

- Caches filter query results only (not full query)
- Shared across queries (filters "status:active" cached, reused)
- Segment-level caching (invalidated when segment merges)

**Difference from request cache**:
- Request cache: Full responses (query + sorting + highlighting)
- Query cache: Filter results only (cheaper, more reusable)

### Field Data Cache

```json
GET _stats/fielddata?human
```

- Caches document-level field values (for aggregations, sorting)
- Expensive to build (reads entire index into memory)
- Use `doc_values: true` instead (pre-built at index time, disk-backed)

**Recommendation**: Always use doc_values for aggregation fields

## Search Pagination: scroll vs search_after

### search_after (Recommended)

```json
GET products/_search
{
  "size": 10,
  "sort": ["_id"],
  "query": {"match_all": {}}
}

// Next page: use last document's sort values
GET products/_search
{
  "size": 10,
  "sort": ["_id"],
  "search_after": ["product-123"],
  "query": {"match_all": {}}
}
```

**Advantages**:
- Stateless (server doesn't track position)
- Efficient (no deep paging overhead)
- Scales to millions of documents

**How it works**:
- sort by _id (or custom field)
- search_after retrieves docs after specified sort value
- O(1) memory per request (not O(from+size))

**Use case**: Deep pagination (page 1000+), millions of results

### scroll (Legacy, use only if needed)

```json
GET products/_search?scroll=1m
{
  "size": 1000,
  "query": {"match_all": {}}
}

GET _search/scroll
{
  "scroll": "1m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAA..."
}
```

**How it works**:
- Server maintains point-in-time snapshot
- Returns scroll ID for next batch
- Must request again within scroll window (1m)

**Drawbacks**:
- Stateful (server maintains position)
- Memory overhead (snapshot held for duration)
- Expensive at scale

**Use case**: Export all documents (if search_after unavailable in legacy system)

## Systematic Relevance Testing

### A/B Testing Queries

Compare two query strategies:

```json
// Control: BM25 default
GET products/_search
{
  "query": {"match": {"title": "laptop"}}
}

// Variant: BM25 with business boost
GET products/_search
{
  "query": {
    "function_score": {
      "query": {"match": {"title": "laptop"}},
      "functions": [
        {
          "field_value_factor": {
            "field": "sales_volume",
            "modifier": "log1p"
          }
        }
      ]
    }
  }
}
```

**Metrics**:
- Click-through rate (CTR): % of results clicked
- Mean reciprocal rank (MRR): How high is relevant result (10% worse, 10% better)
- Discounted cumulative gain (DCG): Relevance weighted by position
- Normalized DCG (NDCG): NDCG vs. ideal ranking

**Recommendation**: Run for 1-2 weeks, ensure statistical significance (p<0.05)
