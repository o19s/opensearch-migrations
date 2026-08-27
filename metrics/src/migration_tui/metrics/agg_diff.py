"""Aggregation (bucket + metric) comparison, ported from query_diff_visualization.py."""

from __future__ import annotations

from typing import Any

from migration_tui.config import AppConfig
from migration_tui.metrics.models import AggDiffRow, Status
from migration_tui.metrics.search_diff import describe_query, shorten

_SKIP_BUCKET_KEYS = {"key", "key_as_string", "doc_count", "from", "to", "from_as_string", "to_as_string"}
_SKIP_WALK_KEYS = {"buckets", "value", "doc_count", "key", "key_as_string"}


def is_agg_request(request_uri: str, request_body: dict) -> bool:
    if not request_uri.endswith("/_search"):
        return False
    return bool(request_body.get("aggs") or request_body.get("aggregations"))


def _extract_values(aggregations: dict) -> dict[str, float | int]:
    """Flatten nested ES/OS aggregations into {path: numeric_value}."""

    result: dict[str, float | int] = {}
    if not aggregations:
        return result

    def walk(node: Any, path: str = "") -> None:
        if not isinstance(node, dict):
            return

        if isinstance(node.get("value"), (int, float)):
            result[path] = node["value"]

        buckets = node.get("buckets")
        if isinstance(buckets, list):
            for bucket in buckets:
                if not isinstance(bucket, dict):
                    continue

                bucket_key = bucket.get("key_as_string", bucket.get("key", "?"))
                bucket_path = f"{path}[{bucket_key}]" if path else str(bucket_key)

                if "doc_count" in bucket:
                    result[bucket_path] = bucket["doc_count"]

                for key, value in bucket.items():
                    if key in _SKIP_BUCKET_KEYS or not isinstance(value, dict):
                        continue
                    walk(value, f"{bucket_path}.{key}")

        for key, value in node.items():
            if key in _SKIP_WALK_KEYS or not isinstance(value, dict):
                continue
            walk(value, f"{path}.{key}" if path else key)

    for name, aggregation in aggregations.items():
        walk(aggregation, name)

    return result


def _variance(source: float, target: float) -> float | None:
    if source == 0:
        return 0.0 if target == 0 else None
    return ((target - source) / source) * 100.0


def _classify(source: float, target: float, variance: float | None, cfg: AppConfig) -> tuple[Status, str]:
    difference = abs(target - source)
    if difference == 0:
        return Status.IDENTICAL, "Identical"

    if variance is None:
        if difference <= cfg.agg_threshold_absolute:
            return Status.ACCEPTABLE, "Within tolerance"
        return Status.REGRESSION, "Discrepancy found"

    if difference <= cfg.agg_threshold_absolute or abs(variance) <= cfg.agg_threshold_percent:
        return Status.ACCEPTABLE, "Within tolerance"

    return Status.REGRESSION, "Discrepancy found"


def build_agg_diff_rows(entry: dict[str, Any], cfg: AppConfig) -> list[AggDiffRow]:
    """Build one row per flattened metric/bucket for an aggregation query entry."""

    request = entry.get("sourceRequest", {})
    request_uri = request.get("Request-URI", "")
    request_body = request.get("payload", {}).get("inlinedJsonBody", {})

    if not is_agg_request(request_uri, request_body):
        return []

    target_responses = entry.get("targetResponses", [])
    if not target_responses:
        return []

    source_aggs = entry.get("sourceResponse", {}).get("payload", {}).get("inlinedJsonBody", {}).get(
        "aggregations", {}
    )
    target_aggs = target_responses[-1].get("payload", {}).get("inlinedJsonBody", {}).get(
        "aggregations", {}
    )

    source_values = _extract_values(source_aggs)
    target_values = _extract_values(target_aggs)

    description = shorten(describe_query(request_body, request_uri))

    rows: list[AggDiffRow] = []
    for key in sorted(set(source_values) | set(target_values)):
        source_value = source_values.get(key, 0)
        target_value = target_values.get(key, 0)
        variance = _variance(source_value, target_value)
        status, label = _classify(source_value, target_value, variance, cfg)

        if "[" in key:
            name, bucket = key.split("[", 1)
            metric = f"{name}({bucket.rstrip(']')})"
        else:
            metric = key

        rows.append(
            AggDiffRow(
                query_description=description,
                metric=metric,
                source_value=source_value,
                target_value=target_value,
                variance_percent=variance,
                status=status,
                status_label=label,
            )
        )

    return rows
