"""The Textual dashboard app.

Layout: a `Pipeline` tab (live log of the orchestration steps, only shown
when the pipeline is actually run) plus three metrics tabs that are kept
continuously up to date as the tuple source grows: Search Diff, Index
Counts, and Aggregation Diff.
"""

from __future__ import annotations

import logging

from textual import work
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Label, RichLog, TabbedContent, TabPane

from migration_tui.config import AppConfig
from migration_tui.data.sources import TupleSource, create_source
from migration_tui.data.tuple_log import MetricsStore
from migration_tui.pipeline.shell import StepFailed
from migration_tui.pipeline.steps import FULL_PIPELINE, PipelineContext
from migration_tui.ui.widgets import refresh_agg_table, refresh_index_table, refresh_search_table

logger = logging.getLogger(__name__)

SEARCH_COLUMNS = [
    "Conn ID",
    "Search Query",
    "Top-N",
    "Source Hits",
    "Target Hits",
    "ID Jaccard",
    "Content Jaccard",
    "RBO (p=0.9)",
    "Rank Drift",
    "Status",
]
INDEX_COLUMNS = ["Index", "Source Count", "Target Count", "Delta", "Delta %", "Status"]
AGG_COLUMNS = ["Query", "Metric", "Source Value", "Target Value", "Variance", "Status"]


class StatusBar(Label):
    text: reactive[str] = reactive("Starting...")

    def render(self) -> str:
        return self.text


class MigrationDashboardApp(App):
    CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, config: AppConfig, *, run_pipeline: bool) -> None:
        super().__init__()
        self.config = config
        self.run_pipeline_flag = run_pipeline
        self.store = MetricsStore(config=config)
        self._source: TupleSource | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="search"):
            if self.run_pipeline_flag:
                with TabPane("Pipeline", id="pipeline"):
                    yield RichLog(id="pipeline-log", wrap=True, markup=False)
            with TabPane("Search Diff", id="search"):
                yield DataTable(id="search-table")
            with TabPane("Index Counts", id="indices"):
                yield DataTable(id="index-table")
            with TabPane("Aggregation Diff", id="aggs"):
                yield DataTable(id="agg-table")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        search_table = self.query_one("#search-table", DataTable)
        search_table.add_columns(*SEARCH_COLUMNS)
        search_table.zebra_stripes = True

        index_table = self.query_one("#index-table", DataTable)
        index_table.add_columns(*INDEX_COLUMNS)
        index_table.zebra_stripes = True

        agg_table = self.query_one("#agg-table", DataTable)
        agg_table.add_columns(*AGG_COLUMNS)
        agg_table.zebra_stripes = True

        self.run_pipeline_and_tail()

    @work(exclusive=True)
    async def run_pipeline_and_tail(self) -> None:
        if self.run_pipeline_flag:
            ok = await self._run_pipeline()
            if not ok:
                return
        await self._tail_loop()

    async def _run_pipeline(self) -> bool:
        log_widget = self.query_one("#pipeline-log", RichLog)
        ctx = PipelineContext(config=self.config)

        for step in FULL_PIPELINE:
            self._set_status(f"Pipeline: {step.name}")
            log_widget.write(f"\n=== {step.name} ===")
            try:
                async for line in step.run(ctx):
                    log_widget.write(line)
            except StepFailed as exc:
                log_widget.write(f"\n[FAILED] {exc}")
                self._set_status(f"Pipeline failed at: {step.name} (see Pipeline tab)")
                return False

        log_widget.write("\nPipeline complete. Switching to live metrics...\n")
        self.query_one(TabbedContent).active = "search"
        return True

    async def _tail_loop(self) -> None:
        import asyncio

        self._source = create_source(self.config.source)
        self._set_status(f"Tailing tuple log ({self.config.source.kind})...")

        while True:
            try:
                chunk = await self._source.poll()
            except Exception as exc:  # noqa: BLE001 - surface, don't crash the dashboard
                logger.exception("source poll failed")
                self._set_status(f"Source error: {exc}")
                await asyncio.sleep(self._source.poll_interval_seconds)
                continue

            if chunk:
                self.store.ingest_bytes(chunk)
                self._refresh_tables()

            self._set_status(
                f"Source: {self.config.source.kind} | "
                f"lines parsed: {self.store.stats.lines_parsed} | "
                f"errors: {self.store.stats.parse_errors} | "
                f"search rows: {len(self.store.search_rows)} | "
                f"agg rows: {len(self.store.agg_rows)} | "
                f"indices: {len(self.store.index_rows)}"
            )
            await asyncio.sleep(self._source.poll_interval_seconds)

    def _refresh_tables(self) -> None:
        refresh_search_table(self.query_one("#search-table", DataTable), self.store.search_rows)
        refresh_index_table(self.query_one("#index-table", DataTable), self.store.sorted_index_rows)
        refresh_agg_table(self.query_one("#agg-table", DataTable), self.store.agg_rows)

    def _set_status(self, text: str) -> None:
        self.query_one("#status-bar", StatusBar).text = text

    async def on_unmount(self) -> None:
        if self._source is not None:
            await self._source.close()
