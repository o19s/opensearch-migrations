#!/usr/bin/env python3
"""
Promptfoo exec provider for sequential multi-turn conversation eval.

Maintains a Claude Code session across test cases using --resume and
--session-id flags. Tests with metadata.continue=true continue the
previous session; tests with continue=false start a fresh session.

The provider reads the prompt from argv[1] (promptfoo exec convention)
and session control metadata from the PROMPTFOO_VAR_* env vars.

Usage in eval.yaml:
  providers:
    - id: "exec:python3 claude_sequential_provider.py"
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "scripts", "mcp_server.py")
)

# Session ID file — persists across invocations within a single eval run
_SESSION_FILE = os.path.join(tempfile.gettempdir(), "sma-conv-eval-session-id.txt")


def _get_or_create_session_id(continue_conversation: bool) -> str:
    """Return the current session ID, or generate a new one if starting fresh."""
    if continue_conversation and os.path.isfile(_SESSION_FILE):
        with open(_SESSION_FILE) as f:
            return f.read().strip()
    # New session
    session_id = str(uuid.uuid4())
    with open(_SESSION_FILE, "w") as f:
        f.write(session_id)
    return session_id


def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROMPT", "")
    if not prompt:
        print(json.dumps({"output": "ERROR: No prompt received"}))
        return

    claude_path = shutil.which("claude")
    if not claude_path:
        print(json.dumps({"output": "SKIPPED: claude CLI not found"}))
        return

    # promptfoo passes test vars as PROMPTFOO_VAR_<name> env vars
    continue_flag = os.environ.get("PROMPTFOO_VAR_continue", "false").lower() == "true"
    session_id = _get_or_create_session_id(continue_flag)

    # Build MCP config for the skill server
    mcp_config = {
        "mcpServers": {
            "solr-to-opensearch": {
                "command": sys.executable,
                "args": [MCP_SERVER],
                "env": {"SKILL_STORAGE_DIR": ""},
            }
        }
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(mcp_config, f)
        mcp_config_path = f.name

    try:
        cmd = [
            claude_path, "-p",
            "--output-format", "text",
            "--max-turns", "5",
            "--mcp-config", mcp_config_path,
            "--dangerously-skip-permissions",
        ]

        if continue_flag:
            # --resume <id> continues an existing session
            cmd.extend(["--resume", session_id])
        else:
            # --session-id <uuid> sets the ID for a new session
            cmd.extend(["--session-id", session_id])

        cmd.append(prompt)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout.strip()
        if not output and result.stderr:
            output = f"ERROR: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        output = "ERROR: claude CLI timed out after 300s"
    except Exception as e:
        output = f"ERROR: {e}"
    finally:
        os.unlink(mcp_config_path)

    print(json.dumps({"output": output}))


if __name__ == "__main__":
    main()
