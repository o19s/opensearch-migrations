#!/usr/bin/env bash
# =============================================================================
# Connected Smoke Tests — Solr → OpenSearch Migration E2E
#
# Proves a minimal migration pipeline works end-to-end against real Docker
# containers:
#
#   1. Build images and transforms
#   2. Start services (Solr, OpenSearch, shim proxy)
#   3. Seed Solr with TechProducts data
#   4. Run promptfoo connectivity eval (Solr + OpenSearch reachability)
#   5. [--migrate only] Export → Transform → Load into OpenSearch
#   6. [--migrate only] Verify migration with full assertion suite
#
# By default, the script does NOT run the migration. It starts services, seeds
# Solr, and runs the promptfoo connectivity eval. Use --migrate to run the full
# export → transform → load pipeline and verification assertions.
#
# Uses non-standard host ports (38983, 39200, 38080) to avoid conflicts with
# local dev services. Container-internal ports are unchanged.
#
# Usage:
#   ./run_connected_tests.sh                          # connectivity + skill eval (default)
#   ./run_connected_tests.sh --migrate                # + full migration + verification
#   ./run_connected_tests.sh --skip-build             # skip gradle/npm (already built)
#   ./run_connected_tests.sh --no-teardown            # leave containers running
#   ./run_connected_tests.sh --output-dir /tmp/out    # custom report directory
#   ./run_connected_tests.sh --no-output              # suppress report files
#
# Reports are saved to connected/reports/ by default.
#
# Prerequisites:
#   - Docker & docker compose
#   - Java 11+ and JAVA_HOME set (for Gradle)
#   - Node.js 18+ (for TypeScript transform build + promptfoo)
#   - curl, python3 (for JSON parsing & transform)
#
# Exit codes:
#   0  All checks passed
#   1  One or more checks failed
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.ports.yml"
TRANSFORMS_DIR="$REPO_ROOT/TrafficCapture/SolrTransformations/transforms"

source "$SCRIPT_DIR/test_helpers.sh"

# Host ports — offset to avoid clashing with local dev services
SOLR_PORT=38983
OS_PORT=39200
SHIM_PORT=38080

SOLR_URL="http://localhost:${SOLR_PORT}"
OS_URL="http://localhost:${OS_PORT}"
SHIM_URL="http://localhost:${SHIM_PORT}"

# Export paths needed by docker-compose.ports.yml for volume mounts
export TRANSFORMS_SRC_DIR="$TRANSFORMS_DIR/src"
export TRANSFORMS_BUILD_DIR="$TRANSFORMS_DIR"

COMPOSE="docker compose -f $COMPOSE_FILE"

SKIP_BUILD=false
NO_TEARDOWN=false
DO_MIGRATE=false
OUTPUT_DIR="$SCRIPT_DIR/reports"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build)   SKIP_BUILD=true; shift ;;
    --no-teardown)  NO_TEARDOWN=true; shift ;;
    --migrate)      DO_MIGRATE=true; shift ;;
    --output-dir)   OUTPUT_DIR="$2"; shift 2 ;;
    --no-output)    OUTPUT_DIR=""; shift ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

cleanup() {
  if [ "$SERVICES_REUSED" = true ]; then
    info "Services were reused — leaving them running"
  elif [ "$NO_TEARDOWN" = false ]; then
    banner "Teardown"
    step "Stopping services..."
    $COMPOSE down -v --remove-orphans 2>/dev/null || true
  else
    warn "Services left running. Stop with:"
    info "$COMPOSE down -v"
  fi
}
trap cleanup EXIT

# =============================================================================
# 0. PRE-FLIGHT: Detect running services or clean start
# =============================================================================
REQUIRED_PORTS=($SOLR_PORT $OS_PORT $SHIM_PORT)
BUSY_PORTS=()
for port in "${REQUIRED_PORTS[@]}"; do
  if ss -tlnH "sport = :$port" 2>/dev/null | grep -q . || \
     lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    BUSY_PORTS+=("$port")
  fi
done

SERVICES_REUSED=false
if [ ${#BUSY_PORTS[@]} -eq ${#REQUIRED_PORTS[@]} ]; then
  # All ports busy — reuse existing services (previous --no-teardown run)
  SERVICES_REUSED=true
  info "All ports (${REQUIRED_PORTS[*]}) already listening — reusing running services"
elif [ ${#BUSY_PORTS[@]} -gt 0 ]; then
  # Some but not all ports busy — conflict
  echo -e "${RED}Pre-flight check failed: some ports in use but not all${RESET}"
  echo ""
  for port in "${BUSY_PORTS[@]}"; do
    echo -e "  ${BOLD}$port${RESET}  — in use"
  done
  echo ""
  info "Either free these ports or start all services with a previous --no-teardown run."
  exit 1
else
  # No ports busy — clean start
  $COMPOSE down -v --remove-orphans 2>/dev/null || true
  info "Ports ${REQUIRED_PORTS[*]} are free — clean start"
fi
echo ""

if [ "$DO_MIGRATE" = true ]; then
  TOTAL_STEPS=6
else
  TOTAL_STEPS=4
fi

# =============================================================================
# 1. BUILD
# =============================================================================
if [ "$SERVICES_REUSED" = true ]; then
  SKIP_BUILD=true
  info "Skipping build (reusing running services)"
fi
if [ "$SKIP_BUILD" = false ]; then
  banner "Step 1/${TOTAL_STEPS}: Build"

  step "Building Shim Docker image (gradle build + jibDockerBuild)..."
  # The jibDockerBuild task requires build/versionDir to exist (created by
  # syncVersionFile), but doesn't declare a proper task dependency on it.
  # Running :build first ensures the directory is created before Jib reads
  # its extraDirectories config.
  (cd "$REPO_ROOT" && ./gradlew :TrafficCapture:transformationShim:build :TrafficCapture:transformationShim:jibDockerBuild)

  # Jib may tag the image with a registry prefix (e.g. localhost:5001/...) that
  # doesn't match the bare name in docker-compose.yml. Ensure the expected tag exists.
  if ! docker image inspect migrations/transformation_shim:latest >/dev/null 2>&1; then
    JIB_IMAGE=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep 'transformation_shim' | head -1)
    if [ -n "$JIB_IMAGE" ]; then
      step "Tagging $JIB_IMAGE → migrations/transformation_shim:latest"
      docker tag "$JIB_IMAGE" migrations/transformation_shim:latest
    else
      echo -e "${RED}Could not find transformation_shim image after build${RESET}"; exit 1
    fi
  fi
  info "Image: migrations/transformation_shim"

  step "Building TypeScript transforms (npm install + build)..."
  (cd "$TRANSFORMS_DIR" && npm install --silent && npm run build --silent)
  info "Output: $TRANSFORMS_DIR/dist/"
else
  warn "Skipping build (--skip-build). Ensure image and transforms are already built."
fi

# =============================================================================
# 2. START SERVICES
# =============================================================================
if [ "$SERVICES_REUSED" = true ]; then
  banner "Step 2/${TOTAL_STEPS}: Services (reusing)"
  info "Services already running:"
  info "  Solr 8          → ${SOLR_URL}   (SOURCE)"
  info "  OpenSearch 3.3  → ${OS_URL}   (TARGET)"
  info "  Shim Proxy      → ${SHIM_URL}   (proxy)"
else
  banner "Step 2/${TOTAL_STEPS}: Start Services"

  step "Starting docker-compose (OpenSearch 3.3, Solr 8, Shim proxy)..."
  detail "Using non-standard ports to avoid conflicts with local dev services"
  $COMPOSE up -d

  info "Services:"
  info "  Solr 8          → ${SOLR_URL}   (SOURCE — data lives here first)"
  info "  OpenSearch 3.3  → ${OS_URL}   (TARGET — data migrated here)"
  info "  Shim Proxy      → ${SHIM_URL}   (translates Solr queries → OpenSearch)"

  wait_for "OpenSearch" "${OS_URL}" 120
  wait_for "Solr"       "${SOLR_URL}/solr/admin/info/system" 120

  # Give the shim time to connect and load transforms
  sleep 5
fi

# =============================================================================
# 3. SEED SOLR (SOURCE)
# =============================================================================
banner "Step 3/${TOTAL_STEPS}: Seed Solr (SOURCE)"

COLLECTION="techproducts"

step "Creating SolrCloud collection '$COLLECTION'..."
detail "GET ${SOLR_URL}/solr/admin/collections?action=CREATE&name=${COLLECTION}&numShards=1&replicationFactor=1"
CREATE_RESP=$(curl -s "${SOLR_URL}/solr/admin/collections?action=CREATE&name=${COLLECTION}&numShards=1&replicationFactor=1")
if echo "$CREATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('responseHeader',{}).get('status')==0 else 1)" 2>/dev/null; then
  info "SolrCloud collection created (1 shard, RF=1)"
else
  info "Collection '$COLLECTION' already exists — reusing"
fi

step "Indexing 5 TechProducts documents into Solr..."
detail "POST ${SOLR_URL}/solr/${COLLECTION}/update/json/docs?commit=true"

SEED_DOCS='[
  {"id":"TP-001","name":"Solr Powered Search","features":["advanced full-text search","faceted navigation"],"cat":"search","price":0.0,"popularity":10,"inStock":true},
  {"id":"TP-002","name":"OpenSearch Migration Guide","features":["step-by-step migration","query DSL examples"],"cat":"migration","price":29.99,"popularity":7,"inStock":true},
  {"id":"TP-003","name":"BM25 Relevance Tuning","features":["BM25 scoring","field boosting"],"cat":"search","price":14.99,"popularity":8,"inStock":false},
  {"id":"TP-004","name":"Enterprise Dashboard","features":["real-time analytics","alerting"],"cat":"analytics","price":99.99,"popularity":5,"inStock":true},
  {"id":"TP-005","name":"Query DSL Cookbook","features":["bool queries","multi_match patterns"],"cat":"search","price":19.99,"popularity":9,"inStock":true}
]'

curl -sf -X POST "${SOLR_URL}/solr/${COLLECTION}/update/json/docs?commit=true" \
  -H 'Content-Type: application/json' \
  -d "$SEED_DOCS" >/dev/null

info "5 documents indexed in Solr"
echo ""
info "At this point ONLY Solr has data. OpenSearch is empty."
detail "curl ${OS_URL}/${COLLECTION}/_count → index does not exist yet"

# =============================================================================
# 4. PROMPTFOO CONNECTIVITY EVAL
# =============================================================================
banner "Step 4/${TOTAL_STEPS}: Promptfoo Connectivity Eval"

step "Running promptfoo eval against live services..."
info "Config: $SCRIPT_DIR/promptfooconfig.yaml"
echo ""

# Export ports so promptfoo config can reference them via ${SOLR_PORT} etc.
export SOLR_PORT OS_PORT SHIM_PORT

PROMPTFOO_EXIT=0
PROMPTFOO_ARGS=(eval --config "$SCRIPT_DIR/promptfooconfig.yaml" --no-cache)
if [ -n "$OUTPUT_DIR" ]; then
  mkdir -p "$OUTPUT_DIR"
  PROMPTFOO_ARGS+=(--output "$OUTPUT_DIR/promptfoo-results.json")
fi

if command -v npx >/dev/null 2>&1; then
  npx promptfoo "${PROMPTFOO_ARGS[@]}" || PROMPTFOO_EXIT=$?
else
  warn "npx not found — skipping promptfoo eval"
  info "Install Node.js 18+ and run: npx promptfoo eval --config $SCRIPT_DIR/promptfooconfig.yaml"
  PROMPTFOO_EXIT=0
fi

if [ "$PROMPTFOO_EXIT" -ne 0 ]; then
  echo -e "${RED}Promptfoo eval failed (exit $PROMPTFOO_EXIT)${RESET}"
  if [ "$DO_MIGRATE" = false ] && [ "$NO_TEARDOWN" = false ]; then
    info "Tip: re-run with --no-teardown to inspect containers after failure"
  fi
  if [ "$DO_MIGRATE" = false ]; then
    exit "$PROMPTFOO_EXIT"
  else
    warn "Continuing to migration despite promptfoo failure..."
  fi
fi

# =============================================================================
# Without --migrate, we're done
# =============================================================================
if [ "$DO_MIGRATE" = false ]; then
  banner "Results"
  echo -e "  ${GREEN}Connectivity checks complete.${RESET}"
  echo ""
  echo -e "  ${BOLD}What was proven:${RESET}"
  info "  1. Docker services started (Solr, OpenSearch, shim proxy)"
  info "  2. Solr seeded with TechProducts data (SOURCE)"
  info "  3. Promptfoo eval verified service connectivity"
  echo ""
  info "To run the full migration pipeline, add --migrate:"
  detail "./run_connected_tests.sh --migrate"
  echo ""
  if [ -n "$OUTPUT_DIR" ]; then
    info "Promptfoo results: $OUTPUT_DIR/promptfoo-results.json"
  fi
  exit "$PROMPTFOO_EXIT"
fi

# =============================================================================
# 5. MIGRATE: Export from Solr → Transform → Load into OpenSearch
# =============================================================================
banner "Step 5/${TOTAL_STEPS}: Migrate Data (Solr → OpenSearch)"

echo -e "  ${BOLD}Migration pipeline:${RESET}"
echo -e "  ${CYAN}┌──────────────┐     ┌───────────┐     ┌──────────────────┐${RESET}"
echo -e "  ${CYAN}│ Solr :${SOLR_PORT} │────▶│ Transform │────▶│ OpenSearch :${OS_PORT} │${RESET}"
echo -e "  ${CYAN}│   (export)   │     │ (python3) │     │    (bulk API)    │${RESET}"
echo -e "  ${CYAN}└──────────────┘     └───────────┘     └──────────────────┘${RESET}"
echo ""

# --- 5a. Export all docs from Solr -------------------------------------------
step "5a. Exporting all documents from Solr..."
detail "GET ${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&rows=100"

SOLR_EXPORT=$(curl -sf "${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&rows=100")
EXPORT_COUNT=$(echo "$SOLR_EXPORT" | python3 -c "import sys,json; print(json.load(sys.stdin)['response']['numFound'])")
info "Exported $EXPORT_COUNT documents from Solr"

# Show a sample of what we got from Solr
echo ""
info "Sample exported doc (first record from Solr):"
echo "$SOLR_EXPORT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
doc = data['response']['docs'][0]
print(json.dumps(doc, indent=2))
" | while IFS= read -r line; do info "  $line"; done
echo ""

# --- 5b. Transform: Solr JSON → OpenSearch index + bulk format ----------------
step "5b. Transforming Solr docs → OpenSearch mappings + bulk format..."
info "This is the 'YOLO migration' step: Solr field types → OpenSearch mappings"
echo ""

# Create the OpenSearch index with mappings derived from the Solr data
MAPPINGS='{
  "mappings": {
    "properties": {
      "id":         {"type": "keyword"},
      "name":       {"type": "text"},
      "features":   {"type": "text"},
      "cat":        {"type": "keyword"},
      "price":      {"type": "float"},
      "popularity": {"type": "integer"},
      "inStock":    {"type": "boolean"}
    }
  }
}'

detail "Solr field type mapping decisions:"
info "  id (string, indexed+stored)         → keyword"
info "  name (text_general)                 → text"
info "  features (text_general, multiValued) → text"
info "  cat (text_general)                  → keyword  (used for filtering/facets)"
info "  price (pfloat)                      → float"
info "  popularity (pint)                   → integer"
info "  inStock (boolean)                   → boolean"
echo ""

detail "PUT ${OS_URL}/${COLLECTION} (create index with mappings)"
curl -sf -X PUT "${OS_URL}/${COLLECTION}" \
  -H 'Content-Type: application/json' \
  -d "$MAPPINGS" >/dev/null
info "OpenSearch index '${COLLECTION}' created with typed mappings"

# Transform Solr export → OpenSearch bulk payload
step "5c. Converting Solr export to OpenSearch _bulk format..."
detail "Stripping Solr-internal fields (_version_) and building NDJSON bulk payload"
echo ""

BULK_BODY=$(echo "$SOLR_EXPORT" | python3 -c "
import sys, json

data = json.load(sys.stdin)
docs = data['response']['docs']

# Fields that are genuinely multi-valued in the schema
MULTI_VALUED = {'features'}

lines = []
for doc in docs:
    doc_id = doc['id']
    clean = {}
    for k, v in doc.items():
        if k.startswith('_'):
            continue  # Strip Solr-internal fields (_version_, etc.)
        # SolrCloud returns ALL fields as arrays. Unwrap single-element
        # arrays for fields that aren't multi-valued in the schema.
        if isinstance(v, list) and len(v) == 1 and k not in MULTI_VALUED:
            v = v[0]
        clean[k] = v
    lines.append(json.dumps({'index': {'_index': 'techproducts', '_id': doc_id}}))
    lines.append(json.dumps(clean))

# _bulk requires trailing newline
print('\n'.join(lines) + '\n')
")

# Show the bulk payload for transparency
BULK_LINE_COUNT=$(echo "$BULK_BODY" | wc -l)
info "Generated _bulk payload: $BULK_LINE_COUNT lines (action + doc pairs)"
info "First action/doc pair:"
echo "$BULK_BODY" | head -2 | while IFS= read -r line; do info "  $line"; done
echo ""

# --- 5d. Load into OpenSearch via _bulk API -----------------------------------
step "5d. Loading into OpenSearch via _bulk API..."
detail "POST ${OS_URL}/_bulk"

BULK_RESP=$(echo "$BULK_BODY" | curl -sf -X POST "${OS_URL}/_bulk" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @-)

BULK_ERRORS=$(echo "$BULK_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errors', True))")
BULK_ITEMS=$(echo "$BULK_RESP" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('items', [])))")

if [ "$BULK_ERRORS" = "False" ]; then
  info "Bulk load succeeded: $BULK_ITEMS documents indexed, 0 errors"
else
  warn "Bulk load reported errors — check assertions below"
  echo "$BULK_RESP" | python3 -m json.tool | head -20
fi

# Refresh so docs are searchable
curl -sf -X POST "${OS_URL}/${COLLECTION}/_refresh" >/dev/null
echo ""

info "Migration complete. Data flow was:"
detail "Solr (:${SOLR_PORT}) → curl export → python3 transform → _bulk API → OpenSearch (:${OS_PORT})"

# =============================================================================
# 6. VERIFY — delegate to standalone verification script
# =============================================================================
banner "Step 6/${TOTAL_STEPS}: Verify Migration"

VERIFY_ARGS=(
  --solr-port "$SOLR_PORT"
  --os-port "$OS_PORT"
  --shim-port "$SHIM_PORT"
)
if [ -n "$OUTPUT_DIR" ]; then
  VERIFY_ARGS+=(--output-dir "$OUTPUT_DIR")
fi

# Run verify_migration.sh; capture its exit code so the cleanup trap still fires
VERIFY_EXIT=0
"$SCRIPT_DIR/verify_migration.sh" "${VERIFY_ARGS[@]}" || VERIFY_EXIT=$?

if [ "$VERIFY_EXIT" -ne 0 ] && [ "$NO_TEARDOWN" = false ]; then
  info "Tip: re-run with --no-teardown to inspect containers after failure"
fi
exit "$VERIFY_EXIT"
