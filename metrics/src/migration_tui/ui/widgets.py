"""Helpers for rendering metric rows into Textual DataTables with status coloring."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import DataTable

from migration_tui.metrics.models import AggDiffRow, IndexCountRow, SearchDiffRow, Status


def _status_cell(status: Status, label: str) -> Text:
    return Text(f"{status.icon} {label}", style=status.style)


def refresh_search_table(table: DataTable, rows: list[SearchDiffRow]) -> None:
    table.clear()
    for row in reversed(rows[-500:]):
        table.add_row(
            row.connection_id,
            row.query_description,
            f"Top {row.top_n}",
            f"{row.source_total:,}",
            f"{row.target_total:,}",
            f"{row.id_jaccard:.2f}",
            f"{row.content_jaccard:.2f}",
            f"{row.rbo:.2f}",
            row.rank_drift,
            _status_cell(row.status, row.status_label),
        )


def refresh_index_table(table: DataTable, rows: list[IndexCountRow]) -> None:
    table.clear()
    for row in rows:
        style = "bold" if row.index == "TOTAL" else ""
        table.add_row(
            Text(row.index, style=style),
            f"{row.source_count:,}",
            f"{row.target_count:,}",
            f"{row.delta:+,}",
            f"{row.delta_percent:+.3f}%",
            _status_cell(row.status, row.status_label),
        )


def refresh_agg_table(table: DataTable, rows: list[AggDiffRow]) -> None:
    table.clear()
    for row in reversed(rows[-500:]):
        variance = "N/A" if row.variance_percent is None else f"{row.variance_percent:+.3f}%"
        table.add_row(
            row.query_description,
            row.metric,
            _format_value(row.source_value),
            _format_value(row.target_value),
            variance,
            _status_cell(row.status, row.status_label),
        )


def _format_value(value: float | int | str | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
