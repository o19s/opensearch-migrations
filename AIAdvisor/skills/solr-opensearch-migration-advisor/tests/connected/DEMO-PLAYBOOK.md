# Migration Advisor — Demo Playbook

Step-by-step guide for demoing the Solr-to-OpenSearch migration advisor
against a live Solr instance.

## Prerequisites

- Docker (for Solr)
- Python 3.11+ (skill venv at `../../.venv/`)
- promptfoo (`npm install -g promptfoo`) — optional, for eval step
- ~10 min for quick demo, ~25 min for full demo

## Setup (one-time)

```bash
# Clone and switch to the demo branch
git clone git@github.com:o19s/opensearch-migrations.git
cd opensearch-migrations
git checkout feature/sma-solr-inspector

# Navigate to the skill
cd AIAdvisor/skills/solr-opensearch-migration-advisor

# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Demo Flow

### Option A: One-Command Demo (~3 min)

```bash
cd tests/connected
bash run_demo.sh --quick
```

This will:
1. Start Solr 8 in Docker (port 38983)
2. Create an `ecommerce` collection with custom schema (22 fields, 12 types, 7 copyFields, synonyms, phonetic search, geo-spatial, deprecated TrieIntField)
3. Load 10,000 product documents
4. Generate 2 minutes of mixed search traffic (eDisMax, autocomplete, geo, standard)
5. Inspect the live Solr instance via the SolrInspector API
6. Generate a migration report with stage plan
7. Run promptfoo eval (11 assertions, all should pass)

### Option B: Full Demo (~25 min)

```bash
cd tests/connected
bash run_demo.sh
```

Same as above but with 200,000 documents and 15 minutes of traffic.
Produces more realistic handler stats and cache metrics.

### Option C: Step-by-Step (for narrated demos)

```bash
cd tests/connected

# 1. Start Solr
docker compose up -d
# Open http://localhost:38983/solr/ in browser to show Solr Admin UI

# 2. Load data
bash solr-demo/setup_demo.sh --quick

# 3. Show the live Solr — browse the Admin UI
#    - Collections: "demo" (built-in) + "ecommerce" (our custom one)
#    - Schema: 22 fields including geo_point, deprecated Trie types
#    - Query tab: try "laptop" against /product-search handler

# 4. Inspect Solr and generate report
source ../../.venv/bin/activate
python3 solr-demo/inspect_and_report.py

# 5. Show the report
cat solr-demo/migration-report.md
#    Key sections to highlight:
#    - Stage Plan (5 stages with success criteria and stop conditions)
#    - Solr Instance Summary (real version, doc count, field stats)
#    - Query Handler Stats (real request counts and latency)
#    - Generated OpenSearch Mapping (with dynamic_templates)

# 6. Run eval (optional)
cd ../skill-impact
bash run_eval.sh --mcp-only
# Shows: 11/11 assertions pass

# 7. Interactive eval view (optional)
promptfoo view
# Opens browser with detailed assertion results

# 8. Cleanup
cd ../connected
docker compose down
```

## What to Highlight

### The Schema Has Migration Challenges
- **7 copyField directives** → each needs `copy_to` in OpenSearch
- **TrieIntField** (deprecated) → advisor should flag this
- **LatLonPointSpatialField** → maps to `geo_point`
- **Custom analyzers**: synonyms, stemming, edge ngrams, phonetic (DoubleMetaphone)
- **Dynamic fields** (`*_s`, `*_i`, etc.) → different pattern syntax in OpenSearch
- **4 custom SearchHandlers** → each has different query defaults

### The Report Is Actionable
- **Stage Plan** with 5 stages, each with prerequisites, actions, success criteria, and stop conditions
- **Handler Stats** show which query paths get the most traffic (prioritize migration effort)
- **OpenSearch Mapping** is ready to use — not a generic template, generated from the actual live schema

### The Eval Proves Quality
- 11 assertions verify schema mapping, report structure, and stage plan content
- Deterministic (no LLM) — same result every time
- Tests the real MCP transport layer (same path IDE agents use)

## Troubleshooting

**Port conflict on 38983:**
```bash
SOLR_PORT=48983 docker compose up -d
SOLR_URL=http://localhost:48983 bash run_demo.sh --quick
```

**Solr takes too long to start:**
The healthcheck retries for 50 seconds. If it still fails, check Docker:
```bash
docker compose logs solr
```

**promptfoo not found:**
The eval step is optional. Install with `npm install -g promptfoo` or skip it.

**Python venv issues:**
```bash
cd ../../   # back to skill root
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
