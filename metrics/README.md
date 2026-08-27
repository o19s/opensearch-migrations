# migration-tui

A Textual terminal dashboard for validating an [OpenSearch Migration
Assistant](https://github.com/opensearch-project/opensearch-migrations) capture/replay
run: it drives the workflow end to end (kind cluster → populate data →
configure/submit migration workflow → run a query workload) and then shows
**live**, continuously-refreshing tables comparing source vs. target:

- **Search Diff** — per-query `_id` overlap (Jaccard), content overlap (via a
  SHA-256 fingerprint of `_source`, so reindexed IDs don't look like data
  loss), ordering similarity (RBO), and positional rank drift.
- **Index Counts** — per-index `docs.count` delta between source and target,
  from `/_cat/indices` tuples.
- **Aggregation Diff** — per-bucket/metric aggregation value comparison
  (terms, stats, histograms, nested aggs), flattened and diffed.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires `kubectl` on `PATH` (and a working context) if you use `run` /
`pipeline`, and AWS credentials in the environment if you use `--source s3`.

## Usage

```bash
# Full pipeline + live dashboard, tailing a local log file
# that the replayer is writing to:
migration-tui run --source local --log-path output.log

# Same, but the tuple log lives in S3 and is updated by the replayer:
migration-tui run --source s3 --s3-bucket my-migration-bucket --s3-key logs/tuples.log

# Cluster + workflow already exist, proxy is already running -- just watch
# an existing/growing log:
migration-tui dashboard --source local --log-path output.log

# Tail directly from the replayer pod (no `kubectl cp` needed/available --
# this shells out to `kubectl exec ... tail -c +N` for incremental reads):
migration-tui dashboard --source pod --pod main-replayer-0 --pod-namespace ma --pod-file /logs/temp/progress/tuples.log

# Headless: run the pipeline only, print progress, no TUI (e.g. CI):
migration-tui pipeline --namespace ma
```

Run `migration-tui run --help` / `dashboard --help` for the full flag list
(ports, index name, thresholds are all in `config.py` if you need to go
beyond flags).

## Project layout

```
src/migration_tui/
  config.py            # every tunable in one place (k8s, OpenSearch, workflow, source, thresholds)
  __main__.py           # CLI (click): run / dashboard / pipeline
  metrics/
    similarity.py        # jaccard / RBO / rank-shift / content fingerprint (pure functions)
    search_diff.py        # per-search-query comparison row (was comparison_matrix*.py)
    docs_diff.py           # per-index doc-count comparison row (was get_query.sh)
    agg_diff.py             # per-aggregation comparison row (was query_diff_visualization.py)
    models.py                # row dataclasses + Status enum (shared coloring/labels)
  data/
    tuple_log.py           # parses tuple-log lines -> MetricsStore (the live source of truth)
    sources.py              # LocalFileSource / S3Source / PodSource, one poll() interface
  pipeline/
    shell.py                # async subprocess helpers (streamed + background processes)
    k8s.py                    # kubectl wrappers (port-forward, exec; no `kubectl cp`)
    opensearch_client.py       # httpx: create index, bulk load, run query workload (was populate_data.sh / curl in query_data.sh)
    workflow.py                 # renders + submits the migration workflow JSON
    queries.py                   # the validation query catalog (was query_data.sh)
    steps.py                      # orchestrates the above into FULL_PIPELINE
  ui/
    app.py                        # Textual App: pipeline log tab + 3 live metrics tabs
    widgets.py                     # DataTable rendering with status coloring
tests/
  test_metrics.py                 # unit tests for the comparison logic (pure, no I/O)
sample-data/
  products_index.json, products.ndjson   # unchanged from the original setup
```

## Tests

```bash
pytest
```

Covers the pure comparison logic in `metrics/` (Jaccard, RBO, rank shift,
classification) against constructed and real sample tuple entries.
