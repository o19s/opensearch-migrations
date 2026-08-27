"""Search-hit comparison: ID overlap, content overlap, ordering (RBO), rank drift.

This is the merged/best-of version of the original comparison_matrix.py and
comparison_matrix_alt.py: it compares both `_id` sets (does the source and
target agree on *which* documents came back) and content fingerprints (does
the target agree on *document content*, even if IDs differ after reindex),
which the original comparison_matrix.py could not distinguish.
"""

from __future__ import annotations

from typing import Any

from migration_tui.config import AppConfig
from migration_tui.metrics.models import SearchDiffRow, Status
from migration_tui.metrics.similarity import (
    document_fingerprint,
    jaccard_similarity,
    rank_shift,
    rbo_score,
)

MAX_QUERY_LENGTH = 60


def is_search_request(request_uri: str, request_body: dict) -> bool:
    return request_uri.endswith("/_search") and "query" in request_body


def shorten(value: str, max_length: int = MAX_QUERY_LENGTH) -> str:
    return value if len(value) <= max_length else value[: max_length - 3] + "..."


def short_connection_id(value: str | None, length: int = 12) -> str:
    return str(value)[:length] if value else "-"


def describe_query(request_body: dict, request_uri: str) -> str:
    """Render a query body into a short human-readable description."""

    query = request_body.get("query", {})
    if not query:
        return request_uri

    for clause_key in ("term", "match"):
        clause = query.get(clause_key)
        if isinstance(clause, dict):
            return " AND ".join(f"{field}={value}" for field, value in clause.items())

    if "bool" in query:
        return "bool query"
    if "range" in query:
        return f"range({', '.join(query['range'].keys())})"

    import json

    return json.dumps(query, separators=(",", ":"))


def _classify(
    *,
    source_ids: list[str],
    target_ids: list[str],
    id_jaccard: float,
    content_jaccard: float,
    rbo: float,
    source_total: int,
    target_total: int,
    cfg: AppConfig,
) -> tuple[Status, str]:
    if source_ids == target_ids:
        return Status.IDENTICAL, "Identical ranking"

    if content_jaccard == 1.0 and id_jaccard < 1.0:
        if rbo >= 0.999:
            return Status.WARNING, "ID difference only (reindexed IDs, same content)"
        return Status.WARNING, "ID difference + ranking shift"

    if content_jaccard == 1.0 and rbo < 0.999:
        return Status.ACCEPTABLE, "Ranking shift, same content"

    if content_jaccard >= cfg.jaccard_acceptable and rbo >= cfg.rbo_acceptable:
        return Status.ACCEPTABLE, "Minor content difference"

    if source_total != target_total:
        return Status.REGRESSION, "Hit-count discrepancy"

    return Status.REGRESSION, "Content discrepancy"


def build_search_diff_row(entry: dict[str, Any], cfg: AppConfig) -> SearchDiffRow | None:
    """Build one comparison row from a tuple entry, or None if not applicable."""

    request = entry.get("sourceRequest", {})
    request_uri = request.get("Request-URI", "")
    request_body = request.get("payload", {}).get("inlinedJsonBody", {})

    if not is_search_request(request_uri, request_body):
        return None

    target_responses = entry.get("targetResponses", [])
    if not target_responses:
        return None

    source_hits_container = (
        entry.get("sourceResponse", {}).get("payload", {}).get("inlinedJsonBody", {}).get("hits", {})
    )
    target_hits_container = (
        target_responses[-1].get("payload", {}).get("inlinedJsonBody", {}).get("hits", {})
    )

    source_hits = source_hits_container.get("hits", [])
    target_hits = target_hits_container.get("hits", [])

    source_total = source_hits_container.get("total", {}).get("value", len(source_hits))
    target_total = target_hits_container.get("total", {}).get("value", len(target_hits))

    source_ids = [hit["_id"] for hit in source_hits if "_id" in hit]
    target_ids = [hit["_id"] for hit in target_hits if "_id" in hit]

    source_fingerprints = [document_fingerprint(hit.get("_source", {})) for hit in source_hits]
    target_fingerprints = [document_fingerprint(hit.get("_source", {})) for hit in target_hits]

    id_jaccard = jaccard_similarity(source_ids, target_ids)
    content_jaccard = jaccard_similarity(source_fingerprints, target_fingerprints)
    rbo = rbo_score(source_fingerprints, target_fingerprints, cfg.rbo_p)
    drift = rank_shift(source_fingerprints, target_fingerprints)

    status, label = _classify(
        source_ids=source_ids,
        target_ids=target_ids,
        id_jaccard=id_jaccard,
        content_jaccard=content_jaccard,
        rbo=rbo,
        source_total=source_total,
        target_total=target_total,
        cfg=cfg,
    )

    return SearchDiffRow(
        connection_id=short_connection_id(entry.get("connectionId")),
        query_description=shorten(describe_query(request_body, request_uri)),
        top_n=request_body.get("size", 10),
        source_total=source_total,
        target_total=target_total,
        id_jaccard=id_jaccard,
        content_jaccard=content_jaccard,
        rbo=rbo,
        rank_drift=drift.format(source_fingerprints, target_fingerprints),
        status=status,
        status_label=label,
    )
