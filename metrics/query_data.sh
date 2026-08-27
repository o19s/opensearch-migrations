#!/usr/bin/env bash

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

PROXY_URL="${PROXY_URL:-http://localhost:9200}"
INDEX="${INDEX:-products}"

# Ignore TLS certificate validation for self-signed certificates.
CURL_OPTS=(-k -sS)

# ============================================================================
# Helper
# ============================================================================

request() {
    local method="$1"
    local path="$2"
    local body="${3:-}"

    echo
    echo "================================================================"
    echo "REQUEST: $method $path"
    echo "================================================================"

    if [[ -n "$body" ]]; then
        echo "$body" | jq .
        echo
    fi

    if [[ "$method" == "GET" ]]; then
        curl "${CURL_OPTS[@]}" \
            -X GET \
            "${PROXY_URL}${path}"
    else
        curl "${CURL_OPTS[@]}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            "${PROXY_URL}${path}" \
            -d "$body"
    fi

    echo
}


# ============================================================================
# 1. INDEX OVERVIEW
#
# This is the important request for the document-count comparison.
#
# The proxy sends this request to Elasticsearch and replays it against
# OpenSearch, giving the capture/replay logs both source and target results.
# ============================================================================

request \
    "GET" \
    "/_cat/indices?format=json"


# ============================================================================
# 2. BASELINE SEARCH
#
# Return the first 10 documents.
#
# Useful for:
#   - Jaccard
#   - RBO
#   - rank comparison
#   - source/target hit count
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "match_all": {}
        }
    }'


# ============================================================================
# 3. CATEGORY SEARCH - ACCESSORIES
#
# Tests a filtered result set.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "term": {
                "category": "Accessories"
            }
        }
    }'


# ============================================================================
# 4. CATEGORY SEARCH - ELECTRONICS
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "term": {
                "category": "Electronics"
            }
        }
    }'


# ============================================================================
# 5. PRICE RANGE
#
# Tests numeric range filtering.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "range": {
                "price": {
                    "gte": 20,
                    "lte": 100
                }
            }
        }
    }'


# ============================================================================
# 6. PRICE SORT
#
# This is particularly useful for RBO/ranking comparison because we explicitly
# define the ordering rather than relying on _score.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "price": {
                    "order": "asc"
                }
            },
            {
                "_id": {
                    "order": "asc"
                }
            }
        ]
    }'


# ============================================================================
# 7. REVERSE PRICE SORT
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "price": {
                    "order": "desc"
                }
            },
            {
                "_id": {
                    "order": "asc"
                }
            }
        ]
    }'


# ============================================================================
# 8. ID-ORDERED SEARCH
#
# Because your IDs are explicit:
#
#   { "index": { "_id": "98" } }
#
# this gives us a very deterministic result set.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 10,
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "_id": {
                    "order": "asc"
                }
            }
        ]
    }'


# ============================================================================
# 9. CATEGORY AGGREGATION
#
# Tests terms/bucket aggregation.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 0,
        "aggs": {
            "by_category": {
                "terms": {
                    "field": "category",
                    "size": 20
                }
            }
        }
    }'


# ============================================================================
# 10. PRICE STATISTICS
#
# Tests:
#   count
#   min
#   max
#   avg
#   sum
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 0,
        "aggs": {
            "price_stats": {
                "stats": {
                    "field": "price"
                }
            }
        }
    }'


# ============================================================================
# 11. AVERAGE PRICE BY CATEGORY
#
# Tests nested bucket + metric aggregation.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 0,
        "aggs": {
            "by_category": {
                "terms": {
                    "field": "category",
                    "size": 20
                },
                "aggs": {
                    "average_price": {
                        "avg": {
                            "field": "price"
                        }
                    }
                }
            }
        }
    }'


# ============================================================================
# 12. PRICE HISTOGRAM
#
# Tests distribution of the numeric field.
# ============================================================================

request \
    "POST" \
    "/${INDEX}/_search" \
    '{
        "size": 0,
        "aggs": {
            "price_distribution": {
                "histogram": {
                    "field": "price",
                    "interval": 25,
                    "min_doc_count": 0
                }
            }
        }
    }'


echo
echo "================================================================"
echo "Validation workload completed"
echo "================================================================"
