#!/usr/bin/env python3
"""
Promptfoo custom script provider that calls the real skill code.

Promptfoo exec provider passes the prompt via environment variable PROMPT.
The script prints the response to stdout as JSON: {"output": "..."}

This bridges promptfoo to skill.handle_message() — the same code path
that Kiro/Claude Code would use via MCP.

Usage in promptfooconfig:
  providers:
    - "exec:python skill_provider.py"
"""

import json
import os
import sys

# Add the scripts directory to sys.path
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
sys.path.insert(0, SCRIPT_DIR)

from skill import SolrToOpenSearchMigrationSkill
from storage import InMemoryStorage


def main():
    # Promptfoo exec provider passes the prompt via PROMPT env var
    prompt = os.environ.get("PROMPT", "")
    if not prompt:
        # Fallback: try stdin or argv
        if len(sys.argv) > 1:
            prompt = sys.argv[1]
        else:
            prompt = sys.stdin.read().strip()

    if not prompt:
        print(json.dumps({"output": "ERROR: No prompt received"}))
        sys.exit(0)

    # Create a fresh skill instance with in-memory storage
    skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
    session_id = "promptfoo-eval"

    # Send the prompt through handle_message (the real skill engagement path)
    response = skill.handle_message(prompt, session_id)

    # Generate report if the skill processed a schema
    state = skill._storage.load(session_id)
    if state and state.get_fact("schema_migrated"):
        report = skill.generate_report(session_id)
        response += "\n\n---\n\n" + report

    # Output as JSON (promptfoo exec provider format)
    print(json.dumps({"output": response}))


if __name__ == "__main__":
    main()
