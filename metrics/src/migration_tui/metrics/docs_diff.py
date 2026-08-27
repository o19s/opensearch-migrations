"""Index-level document-count comparison, ported from get_query.sh's jq+python pipeline."""

from __future__ import annotations

from typing import Any

from migration_tui.config import AppConfig
from migration_tui.metrics.models import IndexCountRow, Status

CAT_INDICES_URI = "/_cat/indices?format=json"


def is_cat_indices_request(request_uri: str) -> bool:
    return request_uri == CAT_INDICES_URI


def _counts_by_index(body: list[dict]) -> dict[str, int]:
    return {row["index"]: int(row["docs.count"]) for row in body if "index" in row}


def _classify(delta: int, delta_percent: float, cfg: AppConfig) -> tuple[Status, str]:
    if delta == 0:
        return Status.IDENTICAL, "Match"

    if abs(delta) <= cfg.index_count_threshold_absolute and abs(
        delta_percent
    ) <= cfg.index_count_threshold_percent:
        return Status.ACCEPTABLE, "Minor lag (in-sync tolerance)"

    return Status.REGRESSION, f"Action required: review {abs(delta):,} records"


def build_index_count_rows(entry: dict[str, Any], cfg: AppConfig) -> list[IndexCountRow]:
    """Build one row per index found in a `/_cat/indices` tuple entry."""

    request_uri = entry.get("sourceRequest", {}).get("Request-URI", "")
    if not is_cat_indices_request(request_uri):
        return []

    target_responses = entry.get("targetResponses", [])
    if not target_responses:
        return []

    source_body = entry.get("sourceResponse", {}).get("payload", {}).get("inlinedJsonBody", [])
    target_body = target_responses[-1].get("payload", {}).get("inlinedJsonBody", [])

    source_counts = _counts_by_index(source_body)
    target_counts = _counts_by_index(target_body)

    rows: list[IndexCountRow] = []
    for index in sorted(set(source_counts) | set(target_counts)):
        source = source_counts.get(index, 0)
        target = target_counts.get(index, 0)
        delta = target - source

        if source == 0:
            delta_percent = 0.0 if target == 0 else 100.0
        else:
            delta_percent = (delta / source) * 100.0

        status, label = _classify(delta, delta_percent, cfg)

        rows.append(
            IndexCountRow(
                index=index,
                source_count=source,
                target_count=target,
                delta=delta,
                delta_percent=delta_percent,
                status=status,
                status_label=label,
            )
        )

    return rows


def totals_row(rows: list[IndexCountRow], cfg: AppConfig) -> IndexCountRow | None:
    """Aggregate row across all indices, mirroring get_query.sh's Total line."""

    if not rows:
        return None

    source_total = sum(r.source_count for r in rows)
    target_total = sum(r.target_count for r in rows)
    delta = target_total - source_total
    delta_percent = 0.0 if source_total == 0 else (delta / source_total) * 100.0

    status, label = _classify(delta, delta_percent, cfg)

    return IndexCountRow(
        index="TOTAL",
        source_count=source_total,
        target_count=target_total,
        delta=delta,
        delta_percent=delta_percent,
        status=status,
        status_label=label,
    )
