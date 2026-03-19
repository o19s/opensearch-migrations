# Relevance Scoring: Solr vs OpenSearch - The #1 Migration Risk

## Executive Summary
Relevance scoring differences represent the single largest user-facing risk in Solr→OpenSearch migrations. This document provides deep technical analysis and practical testing strategies.

**Critical insight**: A perfect technical migration can still fail users if search quality regresses. Expect 3-8% relevance degradation without proper tuning; budget 40% of migration effort for relevance testing and recovery.

## Default Ranking Algorithms

### Solr: TF-IDF (Through 8.x) to BM25 (9.x+)

#### TF-IDF (Solr ≤8.x default)
**Term Frequency-Inverse Document Frequency**

```
Score = coord(q,d) × queryNorm(q) × Σ( tf(t in d) × idf(t)² × t.getBoost() × norm(t,d) )
```

**Components:**
- **tf(term)**: How many times term appears in document (linear growth)
- **idf(term)**: log₁₀(total_docs / docs_with_term + 1) — rarer terms boosted more
- **coord(q,d)**: Bonus for matching multiple query terms
- **norm(t,d)**: Field length normalization (penalizes long documents)
- **Boost**: Per-field or per-query boost multiplier

**Characteristics:**
- ✅ Simple to understand
- ✅ Predictable behavior for well-tuned queries
- ✅ Good for categorical/traditional search
- ❌ Tail probability issues at very high term frequencies
- ❌ Less sophisticated than probabilistic models

#### BM25 (Solr 9.x+, OpenSearch default)
**Okapi BM25 - Probabilistic Ranking Function**

```
Score = Σ( IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × |D| / avgdl)) )
```

**Parameters:**
- **k1** (default 1.2): Controls term frequency saturation (tuning parameter)
- **b** (default 0.75): Controls field length normalization (0.0 - 1.0)
- **IDF(q)**: log( (N - n(q) + 0.5) / (n(q) + 0.5) )

**Characteristics:**
- ✅ Probabilistic foundation (information retrieval research)
- ✅ Better handling of term frequency saturation
- ✅ Accounts for document length more elegantly
- ✅ Less susceptible to over-optimization tricks
- ✅ Industry standard (Google, Bing use variants)
- ❌ Less intuitive parameter tuning
- ❌ Different ranking outcomes than TF-IDF for same queries

### Key Algorithm Differences

| Aspect | TF-IDF | BM25 |
|--------|--------|------|
| **TF growth** | Linear: 1, 2, 3, 4... | Logarithmic with k1 (1.2): diminishing returns |
| **Document length** | Simple length normalization | Sophisticated length factorization (avgdl aware) |
| **Term saturation** | None: higher TF = higher score | Saturation point: tf ≥ k1×(avgdl+|D|)/avgdl |
| **Field boosting** | Via boost parameter | Via IDF + k1 interaction |
| **Coordination bonus** | Explicit coord factor | Implicit via IDF contribution |
| **Rare term emphasis** | Strong (log growth of idf) | Moderate (capped idf) |

## Impact on Migration: Real-World Examples

### Example 1: E-commerce Product Search

**Query**: `red running shoes`

**Solr TF-IDF results**:
1. "Red Running Shoes" (exact match) — Score: 45.2
2. "Men's Red Shoes for Running" — Score: 38.9
3. "RED RED RED Running Shoe" (keyword stuffing) — Score: 52.1 ⚠️

**OpenSearch BM25 results**:
1. "Red Running Shoes" (exact match) — Score: 18.7
2. "Men's Red Shoes for Running" — Score: 16.2
3. "RED RED RED Running Shoe" (keyword stuffing) — Score: 14.3 ✅

**Analysis**: BM25 naturally penalizes keyword stuffing due to term frequency saturation. However, absolute scores changed (45.2 → 18.7), and if you're relying on score thresholds for filtering, that breaks.

### Example 2: Technical Documentation Search

**Query**: `python concurrent execution threads`

**Solr TF-IDF ranking**:
1. "Concurrent Execution in Python" (short doc, all terms present)
2. "Advanced Python Programming Guide" (long doc, all terms present but diluted)

**OpenSearch BM25 ranking**:
1. "Advanced Python Programming Guide" (long doc, hits avgdl threshold)
2. "Concurrent Execution in Python" (short doc, penalized for brevity)

**Analysis**: BM25 prefers average-length documents; very short OR very long documents are penalized. Field length normalization parameter (b) is critical here.

### Example 3: Duplicate Detection

**Query**: `duplicate content issue`

**Solr TF-IDF**: Document with [duplicate, duplicate, duplicate, content, issue] scores higher (TF unbounded)

**OpenSearch BM25**: Document with [duplicate, content, issue] scores similarly (TF saturation kicks in)

**Analysis**: BM25 is more robust to term repetition; less prone to spam. But if your old queries relied on frequency-based boosting, scores shift.

## Migration Testing Strategy

### Phase 1: Baseline Measurement (Weeks 1-2)

#### Build Relevance Test Set
1. **Select 100-500 representative queries**: Top 80%, mid-frequency 15%, long-tail 5%
2. **Create judgment data**: For each query, rate top 10 results (1-4 scale):
   - 4 = Excellent match
   - 3 = Good match
   - 2 = Acceptable
   - 1 = Poor/irrelevant
3. **Document current Solr behavior**: Record rank positions, scores, explanation

#### Capture Solr Baseline
```bash
# For each query in test set:
curl "http://solr:8983/solr/products/select" \
  -d 'q=red+running+shoes&fl=id,score,_explain_&rows=10' \
  -o solr_baseline_query_1.json
```

**Baseline metrics:**
- nDCG@10 (Normalized Discounted Cumulative Gain)
- Mean Reciprocal Rank (MRR)
- Precision@3, @5, @10
- User satisfaction scores (if available)

### Phase 2: OpenSearch Baseline (Week 2)

#### Initial Migration (No Tuning)
```bash
# Exact same queries, OpenSearch native DSL
curl -X POST "localhost:9200/products/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "multi_match": {
        "query": "red running shoes",
        "fields": ["title^2", "description"]
      }
    },
    "size": 10,
    "explain": true
  }'
```

**Expected outcome**: 5-15% nDCG regression (normal with BM25 shift)

#### Record Metrics
- nDCG@10, MRR, Precision metrics
- Note which queries degrade most
- Categorize: title-heavy vs. description-heavy, short vs. long queries, etc.

### Phase 3: Identify Problem Areas (Week 3)

#### Query Analysis
```
High-regression queries:
- "brand name" exact matches (TF-IDF favored)
- Long queries with many terms (BM25 handles differently)
- Niche domains with sparse vocabulary
- Queries with stopwords (TF-IDF vs BM25 IDF differences)

Low-regression queries:
- Simple 1-2 term searches
- Well-balanced result sets
- Queries with moderate term frequency
```

#### Root Cause Analysis
1. **k1 sensitivity**: Does lowering k1 (0.5-1.0) improve scores?
   - Low k1: More TF-IDF like (less saturation)
   - High k1 (1.2+): More aggressive saturation

2. **Field length bias**: Is 'b' parameter hurting certain field types?
   - b=0: No length normalization (like TF-IDF)
   - b=1: Full length normalization
   - b=0.5: Moderate normalization (good baseline)

3. **IDF differences**: Rare terms scored lower?
   - Check term distribution in corpus
   - Consider custom IDF with term boost

### Phase 4: Tuning & Recovery (Weeks 4-6)

#### Approach 1: BM25 Parameter Tuning

**Conservative tuning** (minimize k1, reduce b):
```json
{
  "settings": {
    "index": {
      "analysis": {
        "analyzer": {
          "default": {
            "type": "standard",
            "stopwords": "_english_"
          }
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "similarity": "bm25_tuned"
      },
      "description": {
        "type": "text",
        "similarity": "bm25_default"
      }
    }
  }
}
```

**With custom similarity:**
```json
{
  "settings": {
    "index": {
      "similarity": {
        "bm25_tuned": {
          "type": "BM25",
          "k1": 0.9,
          "b": 0.5
        },
        "bm25_aggressive": {
          "type": "BM25",
          "k1": 1.5,
          "b": 0.75
        }
      }
    }
  }
}
```

**Tuning ranges to test:**
- k1: 0.5, 0.9, 1.2 (default), 1.5, 2.0
- b: 0.0, 0.5, 0.75 (default), 1.0

#### Approach 2: Query-Level Boosting

**Compensate with field weights:**
```json
{
  "query": {
    "multi_match": {
      "query": "red running shoes",
      "fields": [
        "title^3.0",     // Increase from 2.0
        "brand^2.5",     // Add explicit brand boost
        "description^1.2"
      ],
      "type": "best_fields"
    }
  }
}
```

**Or use script_score for precise control:**
```json
{
  "query": {
    "script_score": {
      "query": {
        "multi_match": {
          "query": "red running shoes",
          "fields": ["title", "description"]
        }
      },
      "script": {
        "source": "_score * doc['popularity'].value",
        "lang": "painless"
      }
    }
  }
}
```

#### Approach 3: A/B Testing Framework

**Setup parallel ranking:**
1. **Algorithm A**: Current best Solr queries (baseline)
2. **Algorithm B**: BM25 tuned parameters (candidate)
3. **Traffic split**: 50/50 random users
4. **Metrics tracked**:
   - Click-through rate (CTR)
   - Query reformulation rate (lower is better)
   - Dwell time (how long user stays on clicked result)
   - Explicit feedback (ratings, thumbs up/down)

**Duration**: Minimum 2 weeks per variant (account for day-of-week variation)

**Decision criteria**:
- Algorithm B must not regress any metric by >2%
- Must improve at least one metric by >1%
- Statistical significance: p < 0.05

### Phase 5: Production Validation (Week 6+)

#### Canary Deployment
1. Route 5% of traffic to OpenSearch cluster
2. Compare click metrics, latency, error rates
3. Expand: 5% → 25% → 50% → 100%

#### Monitoring During Rollout
```
Key metrics:
- Query latency (p50, p95, p99)
- Error rate (timeout, 5xx, connection errors)
- Index refresh lag
- Memory/CPU utilization
- User-facing: CTR, query reformulation, ratings
```

#### Rollback Triggers
- CTR drops >3%
- Query reformulation increases >5%
- Error rate >1%
- Latency p99 >500ms

## Advanced Tuning Techniques

### Technique 1: Custom Scoring Function

**Example: Freshness + Relevance**
```json
{
  "query": {
    "script_score": {
      "query": {
        "bool": {
          "must": [
            {
              "multi_match": {
                "query": "python threading",
                "fields": ["title^2", "content"]
              }
            }
          ]
        }
      },
      "script": {
        "source": """
          Math.log(2 + doc['popularity'].value) +
          doc['recency'].value * 0.1
        """
      },
      "min_score": 5
    }
  }
}
```

### Technique 2: Per-Field BM25 Customization

**Different parameters for different fields:**
```json
{
  "settings": {
    "index": {
      "similarity": {
        "bm25_title": {
          "type": "BM25",
          "k1": 0.8,
          "b": 0.5
        },
        "bm25_tags": {
          "type": "BM25",
          "k1": 1.5,
          "b": 0.0
        },
        "bm25_content": {
          "type": "BM25",
          "k1": 1.2,
          "b": 0.75
        }
      }
    }
  }
}
```

### Technique 3: Learning-to-Rank (LTR)

**For complex ranking logic:**
```json
{
  "query": {
    "ltr_query": {
      "model": "my_model",
      "features": [
        "tf_title",
        "idf_content",
        "popularity_score",
        "freshness_signal"
      ]
    }
  }
}
```

Requires: Training data, feature extraction, model building (ML pipeline)

## Testing Tools & Frameworks

### Tool: Elasticsearch/OpenSearch LTR Plugin
- Define ranking features
- Train models on judgment data
- Validates against test set
- Measurable nDCG improvement

### Tool: Ranklib (Learning-to-Rank Library)
- Open-source ranking algorithm library
- Supports multiple algorithms (MART, LambdaMART, etc.)
- Compatible with search engines

### Tool: Searchmetrics
- Proprietary but powerful A/B testing
- Real user metrics tracking
- Statistical significance testing

### DIY Approach (Minimal Tools)
```python
# Simple nDCG calculator
def ndcg(predicted_ranking, judgment_scores, k=10):
    dcg = sum(judgment_scores[i] / math.log2(i + 2) for i in range(min(k, len(predicted_ranking))))
    ideal_dcg = sum(sorted(judgment_scores, reverse=True)[i] / math.log2(i + 2) for i in range(min(k, len(judgment_scores))))
    return dcg / ideal_dcg if ideal_dcg > 0 else 0

# For each query variant
solr_ndcg = ndcg(solr_results, judgments)
opensearch_ndcg = ndcg(opensearch_results, judgments)
improvement = (opensearch_ndcg - solr_ndcg) / solr_ndcg * 100
```

## Relevance Regression: Risk Mitigation

### Preparation
- ✅ Build judgment dataset BEFORE migration begins
- ✅ Measure Solr baseline comprehensively
- ✅ Document which queries are business-critical
- ✅ Identify queries sensitive to algorithm changes

### During Migration
- ✅ Test on full production index (sample testing insufficient)
- ✅ Run A/B tests minimum 2 weeks
- ✅ Track all relevance metrics weekly
- ✅ Have rollback plan ready

### Post-Cutover
- ✅ Monitor relevance metrics daily for 4 weeks
- ✅ Iterate on tuning based on real user behavior
- ✅ Document final parameters for future reference
- ✅ Plan quarterly relevance audits

## Summary: Migration Impact by Search Type

| Search Type | Impact | Primary Risk | Mitigation |
|------------|--------|-------------|-----------|
| **Branded/exact match** | 3-5% | Title matches may shift | Field boost tuning |
| **Long queries (3+ terms)** | 8-12% | Term frequency interaction | Query rewriting |
| **Numerical/exact filtering** | <1% | No algorithm sensitivity | Direct mapping |
| **Full-text/content search** | 2-4% | Moderate, tunable | BM25 parameters |
| **Faceted search** | <1% | No algorithm impact | Migration straightforward |
| **Semantic/AI-powered** | N/A | Not applicable to TF-IDF/BM25 | New capability in OpenSearch |

## Key Takeaway
**Relevance scoring is non-negotiable migration work.** Budget 25-40% of migration effort here, invest in proper testing, and plan for 2-4 week optimization cycle. User experience depends on it.
