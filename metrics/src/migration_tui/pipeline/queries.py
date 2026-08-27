"""The validation query workload, ported 1:1 from query_data.sh.

Kept as data (not shell) so it's trivial to add/remove cases without
touching the runner, and so a future TUI screen could let you toggle
individual queries on/off.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Query:
    name: str
    method: str
    path: str
    body: dict[str, Any] | None = None


def build_catalog(index: str) -> list[Query]:
    return [
        Query("Index overview", "GET", "/_cat/indices?format=json"),
        Query(
            "Baseline search (first 10 docs)",
            "POST",
            f"/{index}/_search",
            {"size": 10, "query": {"match_all": {}}},
        ),
        Query(
            "Category search: Accessories",
            "POST",
            f"/{index}/_search",
            {"size": 10, "query": {"term": {"category": "Accessories"}}},
        ),
        Query(
            "Category search: Electronics",
            "POST",
            f"/{index}/_search",
            {"size": 10, "query": {"term": {"category": "Electronics"}}},
        ),
        Query(
            "Price range 20-100",
            "POST",
            f"/{index}/_search",
            {"size": 10, "query": {"range": {"price": {"gte": 20, "lte": 100}}}},
        ),
        Query(
            "Price sort ascending",
            "POST",
            f"/{index}/_search",
            {
                "size": 10,
                "query": {"match_all": {}},
                "sort": [{"price": {"order": "asc"}}, {"_id": {"order": "asc"}}],
            },
        ),
        Query(
            "Price sort descending",
            "POST",
            f"/{index}/_search",
            {
                "size": 10,
                "query": {"match_all": {}},
                "sort": [{"price": {"order": "desc"}}, {"_id": {"order": "asc"}}],
            },
        ),
        Query(
            "ID-ordered search",
            "POST",
            f"/{index}/_search",
            {"size": 10, "query": {"match_all": {}}, "sort": [{"_id": {"order": "asc"}}]},
        ),
        Query(
            "Category aggregation",
            "POST",
            f"/{index}/_search",
            {"size": 0, "aggs": {"by_category": {"terms": {"field": "category", "size": 20}}}},
        ),
        Query(
            "Price statistics",
            "POST",
            f"/{index}/_search",
            {"size": 0, "aggs": {"price_stats": {"stats": {"field": "price"}}}},
        ),
        Query(
            "Average price by category",
            "POST",
            f"/{index}/_search",
            {
                "size": 0,
                "aggs": {
                    "by_category": {
                        "terms": {"field": "category", "size": 20},
                        "aggs": {"average_price": {"avg": {"field": "price"}}},
                    }
                },
            },
        ),
        Query(
            "Price histogram",
            "POST",
            f"/{index}/_search",
            {
                "size": 0,
                "aggs": {
                    "price_distribution": {
                        "histogram": {"field": "price", "interval": 25, "min_doc_count": 0}
                    }
                },
            },
        ),
    ]
