FROM python:3.11-slim

# Create non-root user
RUN groupadd -r advisor && useradd -r -g advisor advisor

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy all source files (setuptools needs scripts/ dir during install)
COPY pyproject.toml uv.lock README.md SKILL.md ./
COPY scripts/ scripts/
COPY steering/ steering/
COPY references/ references/
COPY tests/ tests/

# Install dependencies (with dev extras for pytest)
RUN uv sync --frozen --extra dev

# Set up skill discovery for Claude Code
RUN mkdir -p .claude/skills/solr-to-opensearch-migration \
    && ln -s /app/SKILL.md .claude/skills/solr-to-opensearch-migration/SKILL.md

# Create sessions and cache directories for non-root user
RUN mkdir -p sessions /home/advisor/.cache \
    && chown -R advisor:advisor /app /home/advisor

USER advisor

# Validate skill loads correctly
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["uv", "run", "python", "-c", "from scripts.skill import SolrToOpenSearchMigrationSkill; print('ok')"]

# Default: run unit tests to prove the skill works
ENTRYPOINT ["uv", "run"]
CMD ["pytest", "tests/", "-x", "--ignore=tests/evals", "--ignore=tests/conversational-eval", "--ignore=tests/scenario-evals", "--ignore=tests/connected"]
