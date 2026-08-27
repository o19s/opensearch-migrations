from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    IDENTICAL = "identical"
    ACCEPTABLE = "acceptable"
    WARNING = "warning"
    REGRESSION = "regression"

    @property
    def icon(self) -> str:
        return {
            Status.IDENTICAL: "\u2705",
            Status.ACCEPTABLE: "\u26a0\ufe0f",
            Status.WARNING: "\u26a0\ufe0f",
            Status.REGRESSION: "\u274c",
        }[self]

    @property
    def style(self) -> str:
        """Rich/Textual style name for coloring table cells."""
        return {
            Status.IDENTICAL: "bold green",
            Status.ACCEPTABLE: "yellow",
            Status.WARNING: "yellow",
            Status.REGRESSION: "bold red",
        }[self]


@dataclass(slots=True)
class SearchDiffRow:
    connection_id: str
    query_description: str
    top_n: int
    source_total: int
    target_total: int
    id_jaccard: float
    content_jaccard: float
    rbo: float
    rank_drift: str
    status: Status
    status_label: str


@dataclass(slots=True)
class IndexCountRow:
    index: str
    source_count: int
    target_count: int
    delta: int
    delta_percent: float
    status: Status
    status_label: str


@dataclass(slots=True)
class AggDiffRow:
    query_description: str
    metric: str
    source_value: float | int | str | None
    target_value: float | int | str | None
    variance_percent: float | None
    status: Status
    status_label: str
