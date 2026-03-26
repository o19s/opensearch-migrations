# Connected Smoke Tests — Solr → OpenSearch Migration E2E

Minimal proof-of-operation that data can be migrated from a live Solr instance to
OpenSearch and queried through the transformation shim. Runs against real Docker containers.

## What This Proves

The script runs a complete migration pipeline:

```
Step 3: Seed Solr ──▶ Step 4a: Export from Solr ──▶ Step 4b: Transform ──▶ Step 4d: Load into OpenSearch
   (SOURCE)              (curl /select?q=*:*)        (python3: Solr         (POST /_bulk)
                                                      fields → OS mappings)
```

Then verifies the result:

| Assertion group | Count | What it proves |
|-----------------|-------|----------------|
| Health checks | 3 | Solr, OpenSearch, and shim proxy are all reachable |
| Source verification | 1 | Solr (SOURCE) still has all 5 documents |
| Target verification | 5 | OpenSearch (TARGET) received all 5 docs, spot-check on fields |
| Proxy match-all | 4 | Shim returns Solr-format JSON backed by migrated OpenSearch data |
| Proxy keyword query | 2 | Query translation works against migrated data |
| Proxy field list | 2 | `fl` parameter passes through the transform |
| Proxy rows limit | 1 | Pagination parameter passes through the transform |

**Key point**: Data is seeded ONLY into Solr. OpenSearch starts empty. The migration
step exports from Solr, transforms field types, and bulk-loads into OpenSearch. Every
step is logged with the exact `curl` command and a sample of the data flowing through.

## Prerequisites

- Docker & `docker compose`
- Java 11+ with `JAVA_HOME` set (Gradle builds the shim image)
- Node.js 18+ (builds the TypeScript transforms)
- `curl`, `python3`

## Running

```bash
# Full run: build → start containers → seed Solr → migrate → test → teardown
./run_connected_tests.sh

# Skip the Gradle/npm build (if you've already built recently)
./run_connected_tests.sh --skip-build

# Leave containers running after tests (useful for debugging failures)
./run_connected_tests.sh --no-teardown

# Save JUnit XML + plain text report to a directory
./run_connected_tests.sh --output-dir ./reports
```

### Re-running verification only

After a `--no-teardown` run, you can re-run just the assertions without rebuilding
or restarting containers:

```bash
# Against default ports (38983, 39200, 38080)
./verify_migration.sh

# With custom ports and report output
./verify_migration.sh --solr-port 8983 --os-port 9200 --shim-port 8080 --output-dir ./reports
```

### Test reports

When `--output-dir` is specified, two files are written:

| File | Format | Use case |
|------|--------|----------|
| `results-YYYYMMDD-HHMMSS.xml` | JUnit XML | CI integration (Jenkins, GitHub Actions, etc.) |
| `results-YYYYMMDD-HHMMSS.txt` | Plain text | Human review, commit artifacts |

Expected output on success:

```
  Passed: 18 / 18
  All assertions passed.

  What was proven:
    1. Solr seeded with TechProducts data (SOURCE)
    2. Data exported FROM Solr via /select JSON API
    3. Solr docs transformed → OpenSearch bulk format (field type mapping)
    4. Data loaded INTO OpenSearch via _bulk API (TARGET)
    5. Migrated data verified in OpenSearch (count + spot-check)
    6. Shim proxy translates Solr queries → OpenSearch against migrated data
```

## Ports

The test uses non-standard host ports to avoid conflicts with local dev services:

| Service | Host port | Container port |
|---------|-----------|----------------|
| Solr | 38983 | 8983 |
| OpenSearch | 39200 | 9200 |
| Shim proxy | 38080 | 8080 |

Port remapping is handled by `docker-compose.ports.yml` (a compose override file).

## Architecture

```
                         MIGRATION (one-time)
  ┌────────────────┐     ┌───────────┐     ┌────────────────────┐
  │ Solr :38983    │────▶│ Transform │────▶│ OpenSearch :39200  │
  │   (export)     │     │ (python3) │     │    (bulk API)      │
  └────────────────┘     └───────────┘     └────────────────────┘

                     QUERY PATH (ongoing)
  Solr Client  ──▶  Shim Proxy (:38080)  ──▶  OpenSearch (:39200)
                          │                         ▲
                     request.transform.ts    response.transform.ts
```

## File Structure

```
connected/
├── run_connected_tests.sh      # Full pipeline: build → start → seed → migrate → verify
├── verify_migration.sh         # Standalone assertions (re-runnable against live containers)
├── test_helpers.sh             # Shared assertion functions + report generation
├── docker-compose.ports.yml    # Standalone compose (Solr, OpenSearch, shim, ZK)
└── README.md
```

## Relationship to Other Tests

```
AIAdvisor/skills/solr-opensearch-migration-advisor/tests/
├── evals/        ← PR 1: promptfoo eval of the AI advisor's generated specs
└── connected/    ← PR 2: THIS — live Docker migration + shim proxy verification
```

- **evals/** tests the *advisor's output quality* (LLM-as-judge on migration specs)
- **connected/** tests the *migration infrastructure* (real Solr → export → transform → OpenSearch)
