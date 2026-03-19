"""
MCP stdio server for the Solr to OpenSearch Migration Advisor skill.

Run directly:
    python mcp_server.py

Or configure in your MCP client (.kiro/settings/mcp.json):
    {
      "mcpServers": {
        "solr-to-opensearch": {
          "command": "python3",
          "args": [".kiro/skills/solr-to-opensearch/scripts/mcp_server.py"]
        },
        "aws-knowledge-mcp-server": {
          "url": "https://knowledge-mcp.global.api.aws",
          "type": "http",
          "disabled": false
        }
      }
    }
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Ensure the scripts directory is on the path when invoked directly.
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP
from skill import SolrToOpenSearchMigrationSkill

mcp = FastMCP("solr-to-opensearch")
_skill = SolrToOpenSearchMigrationSkill()


@mcp.tool()
def handle_message(message: str, session_id: str) -> str:
    """Send a message to the Solr to OpenSearch migration advisor.

    Supports schema conversion (paste your schema.xml), query translation,
    migration checklists, and report generation. Session state is persisted
    across calls using session_id.

    Args:
        message: The user message or request.
        session_id: A unique identifier for the migration session.

    Returns:
        The advisor's response as a string.
    """
    return _skill.handle_message(message, session_id)


@mcp.tool()
def generate_report(session_id: str) -> str:
    """Generate a comprehensive migration report for the given session.

    Produces a structured report covering major milestones, potential blockers,
    implementation points, and cost estimates based on the session's history.

    Args:
        session_id: The session identifier used during the migration conversation.

    Returns:
        A Markdown-formatted migration report.
    """
    return _skill.generate_report(session_id)


@mcp.tool()
def convert_schema_xml(schema_xml: str) -> str:
    """Convert a Solr schema.xml document to an OpenSearch index mapping.

    Args:
        schema_xml: The full text content of a Solr schema.xml file.

    Returns:
        A JSON string representing the OpenSearch index mapping.
    """
    return _skill.convert_schema_xml(schema_xml)


@mcp.tool()
def convert_schema_json(schema_api_json: str) -> str:
    """Convert a Solr Schema API JSON response to an OpenSearch index mapping.

    The Solr Schema API is available at GET /solr/<collection>/schema.

    Args:
        schema_api_json: JSON string returned by the Solr Schema API.

    Returns:
        A JSON string representing the OpenSearch index mapping.
    """
    return _skill.convert_schema_json(schema_api_json)


@mcp.tool()
def convert_query(solr_query: str) -> str:
    """Translate a Solr query string to an OpenSearch Query DSL JSON string.

    Supports field:value, phrase, wildcard, range, boolean (AND/OR/NOT),
    and match_all (*:*) patterns.

    Args:
        solr_query: A Solr query string (the value of the q parameter).

    Returns:
        A JSON string representing the OpenSearch Query DSL.
    """
    return _skill.convert_query(solr_query)


@mcp.tool()
def get_migration_checklist() -> str:
    """Return a human-readable checklist of all migration steps.

    Covers preparation, schema migration, index settings, query migration,
    data migration, client migration, testing, and cutover.

    Returns:
        A plain-text migration checklist.
    """
    return _skill.get_migration_checklist()


@mcp.tool()
def get_field_type_mapping_reference() -> str:
    """Return a Markdown reference table of Solr to OpenSearch field type mappings.

    Returns:
        A Markdown-formatted table mapping Solr field type class names to
        their OpenSearch equivalents.
    """
    return _skill.get_field_type_mapping_reference()


@mcp.tool()
def create_opensearch_index(index_name: str, mapping_json: str) -> str:
    """Create an OpenSearch index using the provided index name and mapping.

    This step is OPTIONAL. Only call this tool if the user has explicitly agreed
    to create the index in OpenSearch. Always ask for confirmation before calling.

    Requires the opensearch-py MCP server (or equivalent) to be configured and
    reachable. This tool delegates to the OpenSearch MCP server's index creation
    capability by constructing the appropriate request body.

    Args:
        index_name: The name of the OpenSearch index to create.
        mapping_json: A JSON string representing the OpenSearch index mapping
                      (as produced by convert_schema_xml or convert_schema_json).

    Returns:
        A message indicating success or describing the error encountered.
    """
    import json
    import urllib.request
    import urllib.error

    # Parse and validate the mapping JSON before attempting creation.
    try:
        mapping = json.loads(mapping_json)
    except json.JSONDecodeError as exc:
        return f"Invalid mapping JSON: {exc}"

    # Build the index creation request body.
    body = json.dumps(mapping).encode("utf-8")

    # Default to localhost; users can override via OPENSEARCH_URL env var.
    base_url = os.environ.get("OPENSEARCH_URL", "http://localhost:9200").rstrip("/")
    url = f"{base_url}/{index_name}"

    req = urllib.request.Request(
        url,
        data=body,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )

    # Support basic auth via OPENSEARCH_USER / OPENSEARCH_PASSWORD env vars.
    user = os.environ.get("OPENSEARCH_USER")
    password = os.environ.get("OPENSEARCH_PASSWORD")
    if user and password:
        import base64
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        req.add_header("Authorization", f"Basic {credentials}")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("acknowledged"):
                return f"Index '{index_name}' created successfully."
            return f"Unexpected response: {result}"
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return f"HTTP {exc.code} error creating index '{index_name}': {error_body}"
    except urllib.error.URLError as exc:
        return (
            f"Could not connect to OpenSearch at {base_url}: {exc.reason}. "
            "Check that OpenSearch is running and OPENSEARCH_URL is set correctly."
        )


_AWS_KNOWLEDGE_URL = "https://knowledge-mcp.global.api.aws"


def _call_aws_knowledge(tool_name: str, arguments: dict) -> str:
    """Call a tool on the AWS Knowledge MCP server via HTTP/JSON-RPC."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }).encode("utf-8")
    req = urllib.request.Request(
        _AWS_KNOWLEDGE_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("result", {}).get("content", [])
            return "\n".join(
                item.get("text", "") for item in content if item.get("type") == "text"
            ) or json.dumps(result)
    except urllib.error.URLError as exc:
        return f"AWS Knowledge MCP server unreachable: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return f"Error calling AWS Knowledge MCP server: {exc}"


@mcp.tool()
def aws_knowledge_search(query: str, topic: str = "general") -> str:
    """Search AWS documentation and knowledge base for accurate AWS information.

    Uses the AWS Knowledge MCP Server to retrieve up-to-date documentation,
    best practices, API references, and architectural guidance — especially
    useful for OpenSearch service details, regional availability, and
    migration guidance.

    Valid topics: general, reference_documentation, troubleshooting,
    current_awareness, amplify_docs, cdk_docs, cdk_constructs,
    cloudformation, agent_sops.

    Args:
        query: The search query (e.g. "OpenSearch index settings best practices").
        topic: Documentation topic to narrow the search (default: "general").

    Returns:
        Relevant AWS documentation excerpts as a string.
    """
    return _call_aws_knowledge(
        "search_documentation",
        {"search_phrase": query, "topics": [topic]},
    )


@mcp.tool()
def aws_opensearch_regional_availability(region: str = "") -> str:
    """Check regional availability of Amazon OpenSearch Service.

    Uses the AWS Knowledge MCP Server to retrieve accurate regional
    availability data for OpenSearch Service features and APIs.

    Args:
        region: Optional AWS region code (e.g. "us-east-1"). If omitted,
                returns availability across all regions.

    Returns:
        Regional availability information as a string.
    """
    args: dict = {
        "resource_type": "product",
        "filters": ["Amazon OpenSearch Service"],
    }
    if region:
        args["region"] = region
    return _call_aws_knowledge("get_regional_availability", args)


if __name__ == "__main__":
    mcp.run(transport="stdio")
