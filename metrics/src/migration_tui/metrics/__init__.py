"""Comparison metrics for source vs. target tuple entries.

This package consolidates the logic that used to live spread across
comparison_matrix.py, comparison_matrix_alt.py and query_diff_visualization.py
into three focused modules:

- similarity.py  -> jaccard / RBO / rank-shift primitives (pure functions)
- search_diff.py -> per-search-query comparison rows (hits, ordering, content)
- docs_diff.py   -> per-index document-count comparison rows
- agg_diff.py    -> per-aggregation-bucket comparison rows
"""
