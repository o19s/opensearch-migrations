"""
Minimal MCP server exposing the Solr-to-OpenSearch migration skill.

This is a **stub** that proves the MCP transport works end-to-end.
It wraps the existing skill methods as MCP tools so any MCP-compatible
client (Kiro, Claude Code, Cursor, etc.) can call them over stdio.

TODO: Replace with Jeff's production MCP server implementation, which
      will add richer error handling, streaming, and additional tools.
      See: https://github.com/o19s/opensearch-migrations/issues/TBD
"""

from __future__ import annotations

import os
import sys

# Ensure the scripts directory is importable regardless of how
# this module is launched (e.g. `python scripts/mcp_server.py`).
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from skill import SolrToOpenSearchMigrationSkill  # noqa: E402
from storage import InMemoryStorage  # noqa: E402
from solr_inspector import SolrInspector  # noqa: E402

mcp = FastMCP("solr-to-opensearch")

# Use in-memory storage by default — callers that need persistence
# can set SKILL_STORAGE_DIR in the environment.
_storage_dir = os.environ.get("SKILL_STORAGE_DIR")
if _storage_dir:
    from storage import FileStorage  # noqa: E402
    _skill = SolrToOpenSearchMigrationSkill(storage=FileStorage(_storage_dir))
else:
    _skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())


@mcp.tool()
def convert_schema_xml(schema_xml: str) -> str:
    """Convert a Solr schema.xml to an OpenSearch index mapping (JSON)."""
    return _skill.convert_schema_xml(schema_xml)


@mcp.tool()
def convert_schema_json(schema_json: str) -> str:
    """Convert a Solr Schema API JSON response to an OpenSearch index mapping."""
    return _skill.convert_schema_json(schema_json)


@mcp.tool()
def convert_query(solr_query: str) -> str:
    """Translate a Solr query string to OpenSearch Query DSL (JSON)."""
    return _skill.convert_query(solr_query)


@mcp.tool()
def handle_message(message: str, session_id: str = "default") -> str:
    """Send a message to the migration advisor and get a response.

    The advisor maintains session state across calls with the same session_id.
    """
    return _skill.handle_message(message, session_id)


@mcp.tool()
def get_migration_checklist() -> str:
    """Return a human-readable migration checklist."""
    return _skill.get_migration_checklist()


@mcp.tool()
def generate_report(session_id: str = "default") -> str:
    """Generate a comprehensive migration report for a session."""
    return _skill.generate_report(session_id)


# ---------------------------------------------------------------------------
# Solr inspection tools — read-only queries against a running Solr instance
# ---------------------------------------------------------------------------

@mcp.tool()
def inspect_solr_schema(
    collection: str, solr_url: str = "http://localhost:8983"
) -> str:
    """Fetch the live schema from a running Solr instance."""
    import json as _json
    return _json.dumps(SolrInspector(solr_url).get_schema(collection), indent=2)


@mcp.tool()
def inspect_solr_metrics(
    group: str = "core", solr_url: str = "http://localhost:8983"
) -> str:
    """Fetch Solr metrics (cache stats, query/update rates, JVM heap)."""
    import json as _json
    return _json.dumps(SolrInspector(solr_url).get_metrics(group), indent=2)


@mcp.tool()
def inspect_solr_mbeans(
    collection: str,
    category: str = "QUERYHANDLER",
    solr_url: str = "http://localhost:8983",
) -> str:
    """Fetch MBean stats (request counts, latency, errors per handler)."""
    import json as _json
    return _json.dumps(
        SolrInspector(solr_url).get_mbeans(collection, category), indent=2
    )


@mcp.tool()
def inspect_solr_luke(
    collection: str, solr_url: str = "http://localhost:8983"
) -> str:
    """Fetch index statistics (document count, field cardinality)."""
    import json as _json
    return _json.dumps(SolrInspector(solr_url).get_luke(collection), indent=2)


@mcp.tool()
def inspect_solr_collections(
    solr_url: str = "http://localhost:8983",
) -> str:
    """List all Solr collections or cores."""
    import json as _json
    return _json.dumps(SolrInspector(solr_url).list_collections(), indent=2)


@mcp.tool()
def inspect_solr_system(
    solr_url: str = "http://localhost:8983",
) -> str:
    """Fetch Solr system info (version, JVM, heap, CPU)."""
    import json as _json
    return _json.dumps(SolrInspector(solr_url).get_system_info(), indent=2)


@mcp.tool()
def inspect_solr(
    collection: str,
    solr_url: str = "http://localhost:8983",
    session_id: str = "default",
) -> str:
    """Run a full Solr inspection and store findings in the session.

    Calls schema, metrics, luke, and system APIs, then stores
    the results in session state for use in report generation.
    """
    return _skill.inspect_solr(solr_url, collection, session_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
