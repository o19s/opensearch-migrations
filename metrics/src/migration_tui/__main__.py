"""CLI entrypoint.

    migration-tui run         # full pipeline then live dashboard
    migration-tui dashboard   # skip the pipeline, just tail a source and show tables
    migration-tui pipeline    # run the pipeline only, print progress to stdout (no TUI)

Tuple-source selection (dashboard/run):
    --source local --log-path output.log
    --source s3    --s3-bucket my-bucket --s3-key migrations/tuples.log
    --source pod   --pod main-replayer-0 --pod-file /data/tuples.log
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import click

from migration_tui.config import AppConfig, LocalSourceConfig, PodSourceConfig, S3SourceConfig
from migration_tui.pipeline.shell import StepFailed
from migration_tui.pipeline.steps import FULL_PIPELINE, PipelineContext


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        filename="migration-tui.log",  # never log to stdout -- Textual owns the terminal
    )


def _common_source_options(f):
    f = click.option(
        "--source",
        "source_kind",
        type=click.Choice(["local", "s3", "pod"]),
        default="local",
        show_default=True,
        help="Where to read the tuple log from.",
    )(f)
    f = click.option("--log-path", default="output.log", show_default=True, help="[local] path to tail.")(f)
    f = click.option("--s3-bucket", default="", help="[s3] bucket name.")(f)
    f = click.option("--s3-key", default="", help="[s3] object key.")(f)
    f = click.option("--s3-region", default=None, help="[s3] AWS region.")(f)
    f = click.option("--pod", "pod_name", default="main-replayer-0", show_default=True, help="[pod] pod name.")(f)
    f = click.option("--pod-namespace", default="ma", show_default=True, help="[pod] namespace.")(f)
    f = click.option(
        "--pod-file", default="/data/tuples.log", show_default=True, help="[pod] file path inside the pod."
    )(f)
    f = click.option("--poll-interval", default=2.0, show_default=True, help="Seconds between source polls.")(f)
    return f


def _build_config(**kwargs) -> AppConfig:
    config = AppConfig()
    config.source.kind = kwargs["source_kind"]
    config.source.local = LocalSourceConfig(
        path=Path(kwargs["log_path"]), poll_interval_seconds=kwargs["poll_interval"]
    )
    config.source.s3 = S3SourceConfig(
        bucket=kwargs["s3_bucket"],
        key=kwargs["s3_key"],
        region=kwargs["s3_region"],
        poll_interval_seconds=kwargs["poll_interval"],
    )
    config.source.pod = PodSourceConfig(
        pod=kwargs["pod_name"],
        namespace=kwargs["pod_namespace"],
        file_path=kwargs["pod_file"],
        poll_interval_seconds=kwargs["poll_interval"],
    )
    config.k8s.namespace = kwargs["pod_namespace"]
    return config


@click.group()
def cli() -> None:
    """OpenSearch Migration Assistant capture/replay validation dashboard."""


@cli.command()
@_common_source_options
@click.option("--verbose", is_flag=True, help="Write debug logs to migration-tui.log.")
def run(**kwargs) -> None:
    """Run the full pipeline, then open the live dashboard."""

    _configure_logging(kwargs.pop("verbose"))
    config = _build_config(**kwargs)

    from migration_tui.ui.app import MigrationDashboardApp

    MigrationDashboardApp(config, run_pipeline=True).run()


@cli.command()
@_common_source_options
@click.option("--verbose", is_flag=True, help="Write debug logs to migration-tui.log.")
def dashboard(**kwargs) -> None:
    """Skip the pipeline; just tail a tuple source and show live metrics."""

    _configure_logging(kwargs.pop("verbose"))
    config = _build_config(**kwargs)

    from migration_tui.ui.app import MigrationDashboardApp

    MigrationDashboardApp(config, run_pipeline=False).run()


@cli.command()
@click.option("--namespace", default="ma", show_default=True)
@click.option(
    "--from-step",
    type=click.IntRange(min=1),
    default=1,
    show_default=True,
    help="Start the pipeline from this step number.",
)
def pipeline(namespace: str, from_step: int) -> None:
    """Run setup only, printing progress to stdout. No TUI, no teardown."""

    logging.basicConfig(level=logging.INFO)
    config = AppConfig()
    config.k8s.namespace = namespace

    async def _run() -> None:
        ctx = PipelineContext(config=config)
        try:
            for step in FULL_PIPELINE:
                if step.number < from_step:
                    continue

                click.echo(f"\n=== {step.number}. {step.name} ===")
                async for line in step.run(ctx):
                    click.echo(line)
        except StepFailed as exc:
            click.echo(f"\nFAILED: {exc}", err=True)
            raise SystemExit(1)
        finally:
            # Leave the proxy port-forward running for `dashboard`/query use;
            # only tear down the Elasticsearch one (already stopped by step 4).
            pass

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
