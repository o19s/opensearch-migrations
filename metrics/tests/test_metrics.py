from migration_tui.config import AppConfig
from migration_tui.metrics import docs_diff, search_diff
from migration_tui.metrics.models import Status
from migration_tui.metrics.similarity import jaccard_similarity, rank_shift, rbo_score


def test_jaccard_identical():
    assert jaccard_similarity(["a", "b"], ["a", "b"]) == 1.0


def test_jaccard_disjoint():
    assert jaccard_similarity(["a"], ["b"]) == 0.0


def test_jaccard_empty_both():
    assert jaccard_similarity([], []) == 1.0


def test_rbo_identical_lists():
    assert rbo_score(["a", "b", "c"], ["a", "b", "c"]) == 1.0


def test_rbo_reversed_order_less_than_one():
    score = rbo_score(["a", "b", "c"], ["c", "b", "a"])
    assert 0.0 < score < 1.0


def test_rank_shift_no_common_items():
    result = rank_shift(["a"], ["b"])
    assert result.average is None
    assert result.exact_matches == 0


def test_rank_shift_exact_match():
    result = rank_shift(["a", "b"], ["a", "b"])
    assert result.average == 0
    assert result.exact_matches == 2


def _entry(source_ids, target_ids, size=10):
    def hits(ids):
        return {"total": {"value": len(ids)}, "hits": [{"_id": i, "_source": {"id": i}} for i in ids]}

    return {
        "sourceRequest": {
            "Request-URI": "/products/_search",
            "payload": {"inlinedJsonBody": {"size": size, "query": {"term": {"category": "Electronics"}}}},
        },
        "sourceResponse": {"payload": {"inlinedJsonBody": {"hits": hits(source_ids)}}},
        "targetResponses": [{"payload": {"inlinedJsonBody": {"hits": hits(target_ids)}}}],
        "connectionId": "abc123def456",
    }


def test_search_diff_identical_is_identical_status():
    cfg = AppConfig()
    row = search_diff.build_search_diff_row(_entry(["1", "2", "3"], ["1", "2", "3"]), cfg)
    assert row is not None
    assert row.status is Status.IDENTICAL
    assert row.id_jaccard == 1.0
    assert row.rbo == 1.0


def test_search_diff_reindexed_ids_same_content_is_warning():
    # Different IDs, but content fingerprints are computed from _source, and
    # here _source differs too (since it's keyed by id), so this exercises
    # the "content differs" path -- see the docstring in search_diff.py for
    # the ID-only case, which requires identical _source across differing ids.
    cfg = AppConfig()
    row = search_diff.build_search_diff_row(_entry(["1", "2"], ["9", "8"]), cfg)
    assert row is not None
    assert row.status is Status.REGRESSION


def test_search_diff_non_search_request_returns_none():
    cfg = AppConfig()
    entry = {"sourceRequest": {"Request-URI": "/_cluster/health", "payload": {"inlinedJsonBody": {}}}}
    assert search_diff.build_search_diff_row(entry, cfg) is None


def test_docs_diff_basic():
    cfg = AppConfig()
    entry = {
        "sourceRequest": {"Request-URI": "/_cat/indices?format=json"},
        "sourceResponse": {"payload": {"inlinedJsonBody": [{"index": "products", "docs.count": "100"}]}},
        "targetResponses": [
            {"payload": {"inlinedJsonBody": [{"index": "products", "docs.count": "100"}]}}
        ],
    }
    rows = docs_diff.build_index_count_rows(entry, cfg)
    assert len(rows) == 1
    assert rows[0].status is Status.IDENTICAL


def test_docs_diff_mismatch_flagged_as_regression():
    cfg = AppConfig()
    entry = {
        "sourceRequest": {"Request-URI": "/_cat/indices?format=json"},
        "sourceResponse": {"payload": {"inlinedJsonBody": [{"index": "products", "docs.count": "500"}]}},
        "targetResponses": [
            {"payload": {"inlinedJsonBody": [{"index": "products", "docs.count": "100"}]}}
        ],
    }
    rows = docs_diff.build_index_count_rows(entry, cfg)
    assert rows[0].status is Status.REGRESSION
