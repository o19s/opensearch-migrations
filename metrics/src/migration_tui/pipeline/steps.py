"""Orchestrates all setup steps.

Each step is an async generator that yields human-readable log lines as it
progresses (consumed by the TUI's pipeline screen, or printed directly by
the `pipeline` CLI subcommand) and raises on failure. Steps that start a
long-running process (port-forwards) stash the handle on the shared
`PipelineContext` so a later step -- or shutdown -- can stop it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from migration_tui.config import AppConfig
from migration_tui.pipeline import k8s, opensearch_client, workflow
from migration_tui.pipeline.queries import build_catalog
from migration_tui.pipeline.shell import BackgroundProcess, wait_for_port


@dataclass
class PipelineContext:
    config: AppConfig
    es_port_forward: BackgroundProcess = None
    proxy_port_forward: BackgroundProcess = None
    log: list[str] = field(default_factory=list)

    async def teardown(self) -> None:
        for proc in (self.es_port_forward, self.proxy_port_forward):
            if proc is not None:
                await proc.stop()


@dataclass
class PipelineStep:
    number: int
    name: str
    run: "callable"  # async generator function(ctx) -> AsyncIterator[str]


async def step_kind_cluster(ctx: PipelineContext) -> AsyncIterator[str]:
    yield f"Running {ctx.config.k8s.kind_script} ..."
    async for line in k8s.run_kind_script(str(ctx.config.k8s.kind_script)):
        yield line
    yield "kind cluster ready."

async def step_prepare_environment(ctx: PipelineContext) -> AsyncIterator[str]:
    yield f"Preparing environment ..."
    await workflow.create_s3_bucket(ctx.config.k8s, ctx.config.workflow.s3_bucket)
    await workflow.create_basic_auth_secret(ctx.config.k8s, workflow.source_creds_secret)
    await workflow.create_basic_auth_secret(ctx.config.k8s, workflow.target_creds_secret)

async def step_port_forward_elasticsearch(ctx: PipelineContext) -> AsyncIterator[str]:
    cfg = ctx.config.k8s
    yield f"Port-forwarding {cfg.elasticsearch_service} -> localhost:{cfg.elasticsearch_local_port}"
    ctx.es_port_forward = k8s.port_forward(
        cfg, cfg.elasticsearch_service, cfg.elasticsearch_local_port, cfg.elasticsearch_remote_port
    )
    await ctx.es_port_forward.start()
    await wait_for_port("localhost", cfg.elasticsearch_local_port)
    yield "Elasticsearch port-forward is up."


async def step_populate_data(ctx: PipelineContext) -> AsyncIterator[str]:
    base_url = f"https://localhost:{ctx.config.k8s.elasticsearch_local_port}"
    async for line in opensearch_client.populate_index(base_url, ctx.config.opensearch):
        yield line


async def step_stop_es_port_forward(ctx: PipelineContext) -> AsyncIterator[str]:
    if ctx.es_port_forward is not None:
        await ctx.es_port_forward.stop()
        ctx.es_port_forward = None
    yield "Stopped Elasticsearch port-forward."


async def step_configure_workflow(ctx: PipelineContext) -> AsyncIterator[str]:
    yield "Writing workflow configuration to migration-console..."
    output = await workflow.configure_workflow(ctx.config.k8s, ctx.config.workflow)
    for line in output.splitlines():
        yield line
    yield "Workflow configured."


async def step_submit_workflow(ctx: PipelineContext) -> AsyncIterator[str]:
    yield "Submitting workflow..."
    output = await workflow.submit_workflow(ctx.config.k8s)
    for line in output.splitlines():
        yield line
    yield "Workflow submitted."


async def step_wait_workflow_completion(ctx: PipelineContext) -> AsyncIterator[str]:
    yield "Waiting for workflow completion..."
    status = await workflow.wait_for_workflow(
        ctx.config.k8s,
        poll_interval=10,
        timeout=6 * 60 * 60,
    )
    if workflow.workflow_has_failed_step(status):
        raise RuntimeError(
            f"Migration workflow contains a failed step:\n{status}"
        )
    yield f"Workflow completed with status: {status}"

async def step_port_forward_proxy(ctx: PipelineContext) -> AsyncIterator[str]:
    cfg = ctx.config.k8s
    yield f"Port-forwarding {cfg.proxy_service} -> localhost:{cfg.proxy_local_port}"
    ctx.proxy_port_forward = k8s.port_forward(
        cfg, cfg.proxy_service, cfg.proxy_local_port, cfg.proxy_remote_port
    )
    await ctx.proxy_port_forward.start()
    await wait_for_port("localhost", cfg.proxy_local_port)
    yield "Proxy port-forward is up."


async def step_run_queries(ctx: PipelineContext) -> AsyncIterator[str]:
    base_url = f"http://localhost:{ctx.config.k8s.proxy_local_port}"
    catalog = build_catalog(ctx.config.opensearch.index_name)
    yield f"Running {len(catalog)} validation queries against {base_url} ..."
    async for line in opensearch_client.run_query_workload(base_url, ctx.config.opensearch, catalog):
        yield line
    yield "Validation workload completed."


FULL_PIPELINE: list[PipelineStep] = [
    PipelineStep(1, "Provision kind test cluster", step_kind_cluster),
    # PipelineStep(10, "Prepare environment", step_prepare_environment)
    PipelineStep(2, "Port-forward Elasticsearch", step_port_forward_elasticsearch),
    PipelineStep(3, "Populate index + bulk data", step_populate_data),
    PipelineStep(4, "Stop Elasticsearch port-forward", step_stop_es_port_forward),
    PipelineStep(5, "Configure migration workflow", step_configure_workflow),
    PipelineStep(6, "Submit workflow", step_submit_workflow),
    PipelineStep(7, "Wait for workflow completion", step_wait_workflow_completion),
    PipelineStep(8, "Port-forward capture proxy", step_port_forward_proxy),
    PipelineStep(9, "Run validation query workload", step_run_queries),

]

# Subset useful when the cluster/workflow already exists and you just want
# to (re)generate traffic against an already-running proxy.
QUERY_ONLY_PIPELINE: list[PipelineStep] = [
    PipelineStep(1, "Port-forward capture proxy", step_port_forward_proxy),
    PipelineStep(2, "Run validation query workload", step_run_queries),
]

