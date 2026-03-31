#!/usr/bin/env python3
"""
Promptfoo exec provider that bridges to the MCP server over stdio.

Starts mcp_server.py as a subprocess, sends JSON-RPC tool calls
(handle_message + generate_report), and returns the combined output.

This tests the real MCP transport layer — the same path that
Kiro, Claude Code, and Cursor use when invoking the skill.

Usage in promptfooconfig.yaml:
  providers:
    - "exec:python3 mcp_provider.py"
"""

import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER = os.path.join(SCRIPT_DIR, "..", "..", "scripts", "mcp_server.py")
SESSION_ID = "promptfoo-eval"


def _jsonrpc(method, params=None, req_id=1):
    """Build a JSON-RPC 2.0 request line (newline-terminated)."""
    msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg).encode("utf-8") + b"\n"


def _parse_responses(stdout_bytes):
    """Parse JSON-RPC responses from stdout (handles both framing styles)."""
    responses = []
    text = stdout_bytes.decode("utf-8", errors="replace")

    # Try newline-delimited JSON first
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    # Fall back to scanning for complete JSON objects (Content-Length framing)
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


def _find_response(responses, req_id):
    """Find the response matching a request ID."""
    for r in responses:
        if r.get("id") == req_id:
            return r
    return None


def _extract_text(response):
    """Extract text content from an MCP tools/call response."""
    if not response or "error" in response:
        error = response.get("error", {}) if response else {}
        return f"ERROR: {error.get('message', 'unknown error')}"
    result = response.get("result", {})
    content = result.get("content", [])
    return "\n".join(
        item.get("text", "") for item in content if item.get("type") == "text"
    )


def main():
    # Promptfoo exec provider passes the rendered prompt as argv[1]
    prompt = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROMPT", "")
    if not prompt:
        print(json.dumps({"output": "ERROR: No prompt received"}))
        return

    # Extract schema XML from the prompt if present
    schema_start = prompt.find("<schema")
    schema_end = prompt.find("</schema>")
    schema_xml = ""
    if schema_start != -1 and schema_end != -1:
        schema_xml = prompt[schema_start : schema_end + len("</schema>")]

    # Build the JSON-RPC message sequence.
    # We call individual MCP tools in sequence, simulating the multi-turn
    # workflow that an IDE agent (Kiro, Claude Code) would perform:
    #   1. convert_schema_xml — get the OpenSearch mapping
    #   2. handle_message with schema — updates session state (schema_migrated)
    #   3. generate_report — produces the full migration report
    messages = [
        _jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "promptfoo-mcp-provider", "version": "0.1"},
        }, req_id=1),
        json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }).encode("utf-8") + b"\n",
    ]

    req_id = 2

    # Call convert_schema_xml for the mapping output
    if schema_xml:
        messages.append(_jsonrpc("tools/call", {
            "name": "convert_schema_xml",
            "arguments": {"schema_xml": schema_xml},
        }, req_id=req_id))
        schema_req_id = req_id
        req_id += 1

        # Also send via handle_message to update session state
        # (handle_message with schema sets schema_migrated=True)
        schema_msg = f"Convert this schema: {schema_xml}"
        messages.append(_jsonrpc("tools/call", {
            "name": "handle_message",
            "arguments": {"message": schema_msg, "session_id": SESSION_ID},
        }, req_id=req_id))
        req_id += 1
    else:
        schema_req_id = None

    # Generate the report (uses session state from handle_message above)
    messages.append(_jsonrpc("tools/call", {
        "name": "generate_report",
        "arguments": {"session_id": SESSION_ID},
    }, req_id=req_id))
    report_req_id = req_id

    proc = subprocess.Popen(
        [sys.executable, MCP_SERVER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "SKILL_STORAGE_DIR": ""},
    )

    try:
        stdout, stderr = proc.communicate(
            input=b"".join(messages), timeout=30
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        print(json.dumps({"output": "ERROR: MCP server timed out"}))
        return

    responses = _parse_responses(stdout)

    parts = []
    if schema_req_id:
        schema_resp = _find_response(responses, schema_req_id)
        schema_text = _extract_text(schema_resp)
        if schema_text and not schema_text.startswith("ERROR"):
            parts.append(schema_text)

    report_resp = _find_response(responses, report_req_id)
    report_text = _extract_text(report_resp)
    if report_text and not report_text.startswith("ERROR"):
        parts.append(report_text)

    combined = "\n\n---\n\n".join(parts) if parts else "ERROR: no output"

    # Save report artifact if output dir is set
    artifact_dir = os.environ.get("REPORT_ARTIFACT_DIR")
    if artifact_dir and not combined.startswith("ERROR"):
        os.makedirs(artifact_dir, exist_ok=True)
        path = os.path.join(artifact_dir, "migration-report-py.md")
        with open(path, "w") as f:
            f.write(f"<!-- Generated by mcp_provider.py (deterministic MCP path) -->\n\n")
            f.write(combined)

    print(json.dumps({"output": combined}))


if __name__ == "__main__":
    main()
