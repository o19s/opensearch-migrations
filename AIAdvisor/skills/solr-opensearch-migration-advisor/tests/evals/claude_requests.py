import io
import os
import sys
import threading

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

script_path = "/".join(os.path.realpath(__file__).split("/")[:-1])
cwd = f"{script_path}/../../../solr-opensearch-migration-advisor"


class _StderrFilter(io.TextIOWrapper):
    """Filters known-harmless asyncio noise from stderr."""

    def __init__(self, original):
        self._original = original

    def write(self, s):
        if "Loop" in s and "is closed" in s:
            return len(s)  # swallow it
        return self._original.write(s)

    def flush(self):
        self._original.flush()

    def fileno(self):
        return self._original.fileno()

    def __getattr__(self, name):
        return getattr(self._original, name)


sys.stderr = _StderrFilter(sys.stderr)


async def call_api(prompt: str, options: dict, context: dict) -> dict:
    # check if test has continue flag set, and only then continue sessions
    continue_conversation = (context.get("test", {}).get("metadata", {}).get("continue", False))
    agent_options = ClaudeAgentOptions(
        # picks up most revent conversation (allows sequential tests, would fail on parallelized)
        continue_conversation=continue_conversation,
        allowed_tools=["Read", "Edit", "Glob", "Grep", "Skill", "WebFetch"],  # Tools Claude can use
        # permission_mode="acceptEdits",  # Auto-approve file edits
        setting_sources=["project"],  # for paths: https://platform.claude.com/docs/en/agent-sdk/skills
        effort="medium",
        cwd=cwd
    )
    async for message in query(
            prompt=prompt,
            options=agent_options
    ):
        if isinstance(message, ResultMessage):
            return {"output": message.result}
