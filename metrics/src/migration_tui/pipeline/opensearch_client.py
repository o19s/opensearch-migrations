"""httpx replacements for populate_data.sh and the curl calls in query_data.sh."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from migration_tui.config import OpenSearchConfig
from migration_tui.pipeline.queries import Query


def _client(base_url: str, cfg: OpenSearchConfig) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        auth=(cfg.username, cfg.password),
        verify=cfg.verify_tls,
        timeout=30.0,
    )


async def populate_index(base_url: str, cfg: OpenSearchConfig) -> AsyncIterator[str]:
    """Create the index from its mapping file, then bulk-load the NDJSON file."""

    mapping = json.loads(cfg.index_file.read_text())
    bulk_body = cfg.bulk_file.read_text()

    async with _client(base_url, cfg) as client:
        yield f"Creating index '{cfg.index_name}'..."
        response = await client.put(f"/{cfg.index_name}", json=mapping)
        if response.status_code == 400 and "resource_already_exists_exception" in response.text:
            yield f"  -> '{cfg.index_name}' already exists, skipping creation."
        else:
            response.raise_for_status()
            yield f"  -> {response.status_code} {response.reason_phrase}"

        yield f"Bulk loading '{cfg.bulk_file.name}' into '{cfg.index_name}'..."
        response = await client.post(
            f"/{cfg.index_name}/_bulk",
            content=bulk_body,
            headers={"Content-Type": "application/x-ndjson"},
        )
        response.raise_for_status()
        result = response.json()
        errored = result.get("errors", False)
        took = result.get("took")
        yield f"  -> took {took}ms, errors={errored}, items={len(result.get('items', []))}"


async def run_query_workload(
    base_url: str, cfg: OpenSearchConfig, queries: list[Query]
) -> AsyncIterator[str]:
    """Fire the validation query catalog at `base_url` (the capture proxy).

    Responses aren't inspected here -- the point is to generate the
    request/response tuples that the proxy/replayer captures to the tuple
    log, which is where MetricsStore does the real comparison.
    """

    async with _client(base_url, cfg) as client:
        for query in queries:
            yield f"-> {query.method} {query.path}  ({query.name})"
            if query.method == "GET":
                response = await client.get(query.path)
            else:
                response = await client.post(query.path, json=query.body)
            yield f"   {response.status_code} {response.reason_phrase}"
