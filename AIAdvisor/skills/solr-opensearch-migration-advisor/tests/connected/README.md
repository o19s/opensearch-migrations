# Connected Smoke Tests — Solr → OpenSearch Migration E2E

Minimal proof-of-operation that data can be migrated from a live Solr instance to
OpenSearch. Runs against real Docker containers.

## Two Modes

### Default: Connectivity + skill eval (no migration)

```bash
./run_connected_tests.sh
```

Starts Docker services, seeds Solr with TechProducts data, and runs a **promptfoo eval**
that does two things:
1. **Infrastructure checks** — verifies Solr and OpenSearch are reachable via HTTP
2. **Skill eval** — calls the migration advisor (LLM) with the TechProducts schema in YOLO mode,
   then scores the generated migration spec for structural markers, domain correctness, and quality

Does NOT run the migration pipeline. This is the safe default for CI and quick checks.
Reports are saved to `connected/reports/` by default.

### Full migration: `--migrate`

```bash
./run_connected_tests.sh --migrate
```

Runs the complete pipeline: seed Solr → export → transform → bulk load into OpenSearch →
verify with 8 assertions.

## What This Proves

### Default mode (connectivity + skill eval)

| Check | Type | What it proves |
|-------|------|----------------|
| Solr health | HTTP | Solr is running and returns system info |
| Solr doc count | HTTP | Seeded TechProducts data is queryable |
| OpenSearch health | HTTP | OpenSearch cluster is reachable |
| YOLO TechProducts spec | LLM | Skill generates valid migration spec with structural markers, BM25 flag, opensearch-java, multi_match, and quality rubric |

### Migration mode (`--migrate`)

The full migration pipeline:

```
Seed Solr ──▶ Export from Solr ──▶ Transform ──▶ Load into OpenSearch
 (SOURCE)     (curl /select?q=*:*)  (python3:      (POST /_bulk)
                                     Solr fields
                                     → OS mappings)
```

Then verifies:

| Assertion group | Count | What it proves |
|-----------------|-------|----------------|
| Health checks | 2 | Solr and OpenSearch are reachable |
| Source verification | 1 | Solr (SOURCE) still has all 5 documents |
| Target verification | 5 | OpenSearch (TARGET) received all 5 docs, spot-check on fields |

**Key point**: Data is seeded ONLY into Solr. OpenSearch starts empty. The migration
step exports from Solr, transforms field types, and bulk-loads into OpenSearch. Every
step is logged with the exact `curl` command and a sample of the data flowing through.

## Prerequisites

- Docker & `docker compose`
- Node.js 18+ (runs promptfoo)
- `curl`, `python3`
- AWS credentials with Bedrock access (for the LLM skill eval — see below)

## AWS Credentials

The promptfoo skill eval calls **Amazon Bedrock** (`amazon.nova-pro-v1:0` in `us-east-1`).
The AWS SDK picks up credentials in the standard order:

**Option 1 — Environment variables (quickest for local runs)**

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...        # if using short-lived/SSO credentials
export AWS_DEFAULT_REGION=us-east-1
```

**Option 2 — AWS CLI profile**

```bash
aws configure                       # sets ~/.aws/credentials + config
# or, for SSO:
aws sso login --profile my-profile
export AWS_PROFILE=my-profile
```

**Option 3 — IAM role / instance profile** (CI / EC2 / ECS)

No configuration needed — the SDK picks up the role automatically.

**Verify access before running:**

```bash
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?modelId==`amazon.nova-pro-v1:0`]'
```

> The skill eval is the only step that needs AWS credentials. The infrastructure
> checks (Solr/OpenSearch health) and the `--migrate` pipeline are credential-free.

## Running

```bash
# Connectivity + skill eval (default — reports saved to connected/reports/)
./run_connected_tests.sh

# Full migration + verification
./run_connected_tests.sh --migrate

# Leave containers running after tests (useful for debugging failures)
./run_connected_tests.sh --no-teardown

# Custom report directory
./run_connected_tests.sh --output-dir /tmp/my-reports

# Suppress report files entirely
./run_connected_tests.sh --no-output
```

### Re-running verification only

After a `--no-teardown` run, you can re-run just the migration assertions without
rebuilding or restarting containers:

```bash
# Against default ports (38983, 39200)
./verify_migration.sh

# With custom ports and report output
./verify_migration.sh --solr-port 8983 --os-port 9200 --output-dir ./reports
```

### Re-running promptfoo eval only

After a `--no-teardown` run, you can re-run the promptfoo connectivity eval directly:

```bash
# From the connected/ directory (ports default to 38983/39200)
npx promptfoo eval

# View results in browser
npx promptfoo view
```

### Test reports

Reports are saved to `connected/reports/` by default. Override with `--output-dir`
or suppress with `--no-output`.

| File | Format | Use case |
|------|--------|----------|
| `promptfoo-results.json` | Promptfoo JSON | Infrastructure + skill eval results |
| `results-YYYYMMDD-HHMMSS.xml` | JUnit XML | CI integration (Jenkins, GitHub Actions, etc.) |
| `results-YYYYMMDD-HHMMSS.txt` | Plain text | Human review, commit artifacts |

## Ports

The test uses non-standard host ports to avoid conflicts with local dev services:

| Service | Host port | Container port |
|---------|-----------|----------------|
| Solr | 38983 | 8983 |
| OpenSearch | 39200 | 9200 |

Port remapping is handled by `docker-compose.ports.yml` (a compose override file).

## Architecture

```
                         MIGRATION (one-time, --migrate only)
  ┌────────────────┐     ┌───────────┐     ┌────────────────────┐
  │ Solr :38983    │────▶│ Transform │────▶│ OpenSearch :39200  │
  │   (export)     │     │ (python3) │     │    (bulk API)      │
  └────────────────┘     └───────────┘     └────────────────────┘
```

## File Structure

```
connected/
├── run_connected_tests.sh      # Orchestrator: build → start → seed → eval → [migrate] → verify
├── verify_migration.sh         # Standalone migration assertions (8 checks)
├── test_helpers.sh             # Shared assertion functions + JUnit/text report generation
├── promptfooconfig.yaml        # Promptfoo eval: HTTP connectivity + LLM skill assessment
├── skill-system-prompt.txt     # Migration advisor system prompt (used by promptfoo)
├── docker-compose.ports.yml    # Standalone compose (Solr + ZK, OpenSearch)
├── reports/                    # Default output directory (gitignored)
└── README.md
```

## Relationship to Other Tests

```
AIAdvisor/skills/solr-opensearch-migration-advisor/tests/
├── evals/        ← PR 1: promptfoo eval of the AI advisor's generated specs
└── connected/    ← PR 2: THIS — live Docker connectivity + migration verification
```

- **evals/** tests the *advisor's output quality* (LLM-as-judge on migration specs)
- **connected/** tests the *migration infrastructure* (real Solr → export → transform → OpenSearch)
