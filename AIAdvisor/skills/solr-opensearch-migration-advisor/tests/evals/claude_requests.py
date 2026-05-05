from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
import os
import shutil
import sys
import tempfile

# Suppress asyncio "event loop is closed" noise from subprocess cleanup.
# The SDK spawns a subprocess; when the event loop closes, Python writes
# a warning to stderr. Promptfoo captures all stderr as ERROR, so we
# filter it out here.
_original_stderr = sys.stderr


class _FilteredStderr:
    def write(self, msg):
        if "is closed" not in msg:
            _original_stderr.write(msg)

    def flush(self):
        _original_stderr.flush()


sys.stderr = _FilteredStderr()

script_path = "/".join(os.path.realpath(__file__).split("/")[:-1])
default_cwd = f"{script_path}/../../../solr-opensearch-migration-advisor"


def _resolve_cwd(config: dict) -> tuple[str, list[str]]:
    """Resolve cwd and setting_sources from provider config.

    When config.cwd points to a fixture directory (e.g. fixtures/skill-bare/),
    copy it to /tmp so the agent can't traverse up into the real skill directory
    and discover reference docs that should be hidden.

    Returns (cwd, setting_sources).
    """
    raw_cwd = config.get("cwd")
    if not raw_cwd:
        return default_cwd, ["project"]

    # Resolve relative paths against the script directory
    if not os.path.isabs(raw_cwd):
        raw_cwd = os.path.join(script_path, raw_cwd)

    # Copy to /tmp for isolation — prevents traversing up to find parent SKILL.md/references
    isolated_dir = tempfile.mkdtemp(prefix="sma-eval-")
    shutil.copytree(raw_cwd, isolated_dir, dirs_exist_ok=True)

    # Use setting_sources=["project"] so SKILL.md gets discovered as a project skill.
    # The /tmp isolation prevents walking up to find the real skill references.
    return isolated_dir, ["project"]


async def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    cwd, setting_sources = _resolve_cwd(config)

    # Allow provider config to restrict tools (e.g. bare tests shouldn't use WebFetch)
    allowed_tools = config.get("allowed_tools") or ["Read", "Edit", "Glob", "Grep", "Skill", "WebFetch"]

    # check if test has continue flag set, and only then continue sessions
    continue_conversation = (context.get("test", {}).get("metadata", {}).get("continue", False))
    agent_options = ClaudeAgentOptions(
        # picks up most recent conversation (allows sequential tests, would fail on parallelized)
        continue_conversation=continue_conversation,
        allowed_tools=allowed_tools,
        permission_mode="acceptEdits",  # Auto-approve file edits
        setting_sources=setting_sources,
        effort="medium",
        cwd=cwd
    )
    async for message in query(
            prompt=prompt,
            options=agent_options
    ):
        if isinstance(message, ResultMessage):
            return {"output": message.result}
