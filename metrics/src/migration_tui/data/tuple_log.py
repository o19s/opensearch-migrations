"""Parses capture/replay tuple-log lines and accumulates them into metric rows.

Each line of a tuple log is one JSON object shaped like:

    {
      "sourceRequest": {...}, "sourceResponse": {...},
      "targetRequest": {...}, "targetResponses": [...],
      "connectionId": "...", "numRequests": 1, "numErrors": 0
    }

A `MetricsStore` is the single source of truth the dashboard reads from: it
owns the running tables and knows how to fold a new line into them. It is
intentionally dumb about *where* lines come from -- see sources.py.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from migration_tui.config import AppConfig
from migration_tui.metrics import agg_diff, docs_diff, search_diff
from migration_tui.metrics.models import AggDiffRow, IndexCountRow, SearchDiffRow

logger = logging.getLogger(__name__)

# Cap on how many rows we keep for high-churn tables so the dashboard stays
# responsive on long-running replays. Index counts are always deduped by
# index name instead, so they don't need a cap.
MAX_ROWS = 1000


@dataclass(slots=True)
class ParseStats:
    lines_seen: int = 0
    lines_parsed: int = 0
    lines_skipped: int = 0
    parse_errors: int = 0


@dataclass(slots=True)
class MetricsStore:
    config: AppConfig

    search_rows: list[SearchDiffRow] = field(default_factory=list)
    agg_rows: list[AggDiffRow] = field(default_factory=list)
    index_rows: dict[str, IndexCountRow] = field(default_factory=dict)

    stats: ParseStats = field(default_factory=ParseStats)

    def ingest_line(self, line: str) -> None:
        line = line.strip()
        if not line:
            return

        self.stats.lines_seen += 1

        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            self.stats.parse_errors += 1
            logger.warning("Could not parse tuple-log line: %s", exc)
            return

        matched = False

        for row in docs_diff.build_index_count_rows(entry, self.config):
            self.index_rows[row.index] = row
            matched = True

        search_row = search_diff.build_search_diff_row(entry, self.config)
        if search_row is not None:
            self.search_rows.append(search_row)
            if len(self.search_rows) > MAX_ROWS:
                self.search_rows.pop(0)
            matched = True

        for row in agg_diff.build_agg_diff_rows(entry, self.config):
            self.agg_rows.append(row)
            if len(self.agg_rows) > MAX_ROWS:
                self.agg_rows.pop(0)
            matched = True

        self.stats.lines_parsed += 1
        if not matched:
            self.stats.lines_skipped += 1

    def ingest_bytes(self, chunk: bytes) -> None:
        for raw_line in chunk.splitlines():
            if raw_line:
                self.ingest_line(raw_line.decode("utf-8", errors="replace"))

    @property
    def sorted_index_rows(self) -> list[IndexCountRow]:
        rows = sorted(self.index_rows.values(), key=lambda r: r.index)
        total = docs_diff.totals_row(rows, self.config)
        return rows + ([total] if total else [])
