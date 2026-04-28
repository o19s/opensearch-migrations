## Migration Advisor Usage

There are two ways to run the Agent Skill:

### 1. AI CLI

Run your favorite AI CLI directly on your machine. The skill is compatible with any CLI that supports agent skills, 
such as [Kiro CLI](https://kiro.dev/) or [Claude Code CLI](https://claude.ai/code).

**Session and report persistence:** The skill saves a human-readable progress file to `sessions/<session_id>.md` in the 
project root, updated after every step. Sessions can be resumed after interruption by reusing the same `session_id`.

### 2. Docker Container

Run a pre-configured Docker container that includes all dependencies and automatically starts an agent session with the 
skill loaded.

**Isolation:** The container runs in an isolated environment. The agent can only access the mounted volume 
(`CLAUDE_ADVISOR_VOLUME/`) and files baked into the image at build time — the rest of the host filesystem is not 
reachable. This makes the Docker setup a good choice when data privacy or security is a concern.

**Rebuilding:** The image must be rebuilt whenever skill content changes (e.g. after pulling updates). 
See the [Docker setup README](AIAdvisor/skills/opensearch-migration-advisor/setup/docker/claude/README.md) for build 
and startup instructions.

**Session and report persistence:** The start script creates a `CLAUDE_ADVISOR_VOLUME` folder next to the script itself 
(`AIAdvisor/skills/opensearch-migration-advisor/setup/docker/claude/CLAUDE_ADVISOR_VOLUME/`) and mounts it as the 
working directory inside the container. Session progress files and migration reports are written to 
`CLAUDE_ADVISOR_VOLUME/sessions/`, so they persist after the container is stopped and sessions can be resumed in a later 
run.