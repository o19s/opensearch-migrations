# Services

Shared Solr instances used by skill tests and evals.

Each subdirectory is a named instance with:
- **Setup**: `setup.sh` to start/teardown the service
- **Health check**: `verify.py` — run with `pytest verify.py -v` to confirm the service is up and loaded

## Instances

| Name | Port | Description |
|------|------|-------------|
| `tmdb` | 38984 | Solr 8 with ~10K TMDB movie documents (text-heavy) |

## Usage

```bash
cd tmdb && bash setup.sh
pytest verify.py -v
bash setup.sh teardown
```

## Running evals

Evals use the Claude Agent SDK which requires Python setup first:

```bash
cd AIAdvisor/skills/solr-opensearch-migration-advisor
uv sync --extra eval
source .venv/bin/activate
cp .env.example .env   # fill in CLAUDE_CODE_OAUTH_TOKEN
```

See `tests/evals/README.md` for Claude auth and Bedrock setup details.
