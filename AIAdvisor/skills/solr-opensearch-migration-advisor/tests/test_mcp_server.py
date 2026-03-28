"""
Smoke tests for the MCP server stub.

Verifies that the MCP server starts, lists the expected tools, and can
handle a basic tools/call request.  No LLM, no AWS, no Docker required.

NOTE: This is a minimal "hello MCP server" test.  It will be replaced
when Jeff's production MCP server lands — see the tracking issue on GitHub.
"""

import json
import subprocess
import sys
import os

import pytest

# Path to the MCP server script
MCP_SERVER = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "mcp_server.py"
)

# The tools we expect the stub server to expose
EXPECTED_TOOLS = {
    "convert_schema_xml",
    "convert_schema_json",
    "convert_query",
    "handle_message",
    "get_migration_checklist",
    "generate_report",
}


def _jsonrpc(method: str, params: dict | None = None, req_id: int = 1) -> bytes:
    """Build a JSON-RPC 2.0 request line (newline-terminated)."""
    msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg).encode("utf-8") + b"\n"


def _send_receive(messages: list[bytes], timeout: int = 30) -> list[dict]:
    """Start the MCP server, send JSON-RPC messages, collect responses."""
    proc = subprocess.Popen(
        [sys.executable, MCP_SERVER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "SKILL_STORAGE_DIR": ""},
    )
    try:
        stdout, stderr = proc.communicate(
            input=b"".join(messages), timeout=timeout
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail("MCP server did not respond within timeout")

    # The MCP SDK may use Content-Length framing or newline-delimited JSON.
    # Parse all JSON objects we can find in stdout.
    responses = []
    text = stdout.decode("utf-8", errors="replace")
    # Try to find JSON objects — they may be wrapped in Content-Length headers
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    # If Content-Length framing is used, JSON won't be on neat lines.
    # Fall back to scanning for complete JSON objects.
    if not responses:
        depth = 0
        start = None
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        responses.append(json.loads(text[start : i + 1]))
                    except json.JSONDecodeError:
                        pass
                    start = None

    return responses


@pytest.fixture(scope="module")
def mcp_available():
    """Skip all tests in this module if the mcp package is not installed."""
    try:
        import mcp  # noqa: F401
    except ImportError:
        pytest.skip("mcp package not installed (install with: pip install 'mcp>=1.9')")


class TestMCPServerSmoke:
    """Minimal smoke tests — does the MCP server start and respond?"""

    def test_server_starts_and_responds(self, mcp_available):
        """Server should start over stdio and respond to initialize."""
        messages = [
            _jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            }),
        ]
        responses = _send_receive(messages)
        assert len(responses) >= 1, (
            "Expected at least one response from MCP server"
        )
        # The first response should be the initialize result
        init_resp = responses[0]
        assert "error" not in init_resp, f"Server returned error: {init_resp}"

    def test_tools_list(self, mcp_available):
        """Server should list all expected tools."""
        messages = [
            _jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            }, req_id=1),
            _jsonrpc("notifications/initialized", req_id=2),
            _jsonrpc("tools/list", req_id=3),
        ]
        responses = _send_receive(messages)

        # Find the tools/list response (look for the one with id=3)
        tools_resp = None
        for r in responses:
            if r.get("id") == 3:
                tools_resp = r
                break

        if tools_resp is None:
            # Fall back: find any response that has a "tools" key in result
            for r in responses:
                if "result" in r and "tools" in r.get("result", {}):
                    tools_resp = r
                    break

        assert tools_resp is not None, (
            f"No tools/list response found. Got: {responses}"
        )
        assert "error" not in tools_resp, (
            f"tools/list returned error: {tools_resp}"
        )

        tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
        missing = EXPECTED_TOOLS - tool_names
        assert not missing, (
            f"Missing expected tools: {missing}. Got: {tool_names}"
        )

    def test_convert_schema_xml_via_mcp(self, mcp_available):
        """A basic tools/call should return a valid OpenSearch mapping."""
        simple_schema = (
            '<schema name="test" version="1.6">'
            '<fieldType name="string" class="solr.StrField"/>'
            '<field name="id" type="string" indexed="true" stored="true"/>'
            "</schema>"
        )
        messages = [
            _jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            }, req_id=1),
            _jsonrpc("notifications/initialized", req_id=2),
            _jsonrpc("tools/call", {
                "name": "convert_schema_xml",
                "arguments": {"schema_xml": simple_schema},
            }, req_id=3),
        ]
        responses = _send_receive(messages)

        call_resp = None
        for r in responses:
            if r.get("id") == 3:
                call_resp = r
                break

        assert call_resp is not None, (
            f"No tools/call response found. Got: {responses}"
        )
        assert "error" not in call_resp, (
            f"tools/call returned error: {call_resp}"
        )

        # The result should contain content with the mapping JSON
        content = call_resp["result"]["content"]
        assert len(content) > 0
        text = content[0]["text"]
        mapping = json.loads(text)
        assert "mappings" in mapping
        assert "id" in mapping["mappings"]["properties"]
