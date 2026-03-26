#!/usr/bin/env bash
# =============================================================================
# Connected Smoke Tests — Solr → OpenSearch Migration E2E
#
# Proves a minimal migration pipeline works end-to-end against real Docker
# containers:
#
#   1. Seed data into Solr (the SOURCE of truth)
#   2. Export data FROM Solr via its JSON API
#   3. Transform Solr docs → OpenSearch bulk format
#   4. Load into OpenSearch
#   5. Verify data landed correctly + shim proxy translates queries
#
# Uses non-standard host ports (38983, 39200, 38080) to avoid conflicts with
# local dev services. Container-internal ports are unchanged.
#
# Usage:
#   ./run_connected_tests.sh                # full build + test + teardown
#   ./run_connected_tests.sh --skip-build   # skip gradle/npm (already built)
#   ./run_connected_tests.sh --no-teardown  # leave containers running
#
# Prerequisites:
#   - Docker & docker compose
#   - Java 11+ and JAVA_HOME set (for Gradle)
#   - Node.js 18+ (for TypeScript transform build)
#   - curl, python3 (for JSON parsing & transform)
#
# Exit codes:
#   0  All assertions passed
#   1  One or more assertions failed
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.ports.yml"
TRANSFORMS_DIR="$REPO_ROOT/TrafficCapture/SolrTransformations/transforms"

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
for arg in "$@"; do
  case "$arg" in
    --skip-build)  SKIP_BUILD=true ;;
    --no-teardown) NO_TEARDOWN=true ;;
  esac
done

# --- Colors & helpers --------------------------------------------------------
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
DIM='\033[2m'
RESET='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

banner()  { echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════${RESET}"; echo -e "${BOLD}${CYAN}  $1${RESET}"; echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${RESET}\n"; }
step()    { echo -e "${BOLD}${GREEN}▶ $1${RESET}"; }
info()    { echo -e "${DIM}  $1${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $1${RESET}"; }
detail()  { echo -e "  ${CYAN}→${RESET} $1"; }

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc"
    echo -e "         expected: ${BOLD}$expected${RESET}"
    echo -e "         actual:   ${BOLD}$actual${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -qi "$needle"; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc"
    echo -e "         expected to contain: ${BOLD}$needle${RESET}"
    echo -e "         response (first 200 chars): ${DIM}${haystack:0:200}${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_http_ok() {
  local desc="$1" url="$2"
  local status
  status=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null) || status="000"
  if [ "$status" = "200" ]; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc"
    echo -e "         expected HTTP 200, got: ${BOLD}$status${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

wait_for() {
  local name="$1" url="$2" max_wait="${3:-120}"
  info "Waiting for $name at $url ..."
  local elapsed=0
  while ! curl -sf "$url" >/dev/null 2>&1; do
    sleep 2; elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge "$max_wait" ]; then
      echo -e "${RED}✗ $name did not become healthy after ${max_wait}s${RESET}"; exit 1
    fi
  done
  info "$name is ready (${elapsed}s)"
}

cleanup() {
  if [ "$NO_TEARDOWN" = false ]; then
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
# 0. PRE-FLIGHT: Clean up any previous run, then check ports
# =============================================================================
# Tear down containers from a previous run of this script (same compose project)
$COMPOSE down -v --remove-orphans 2>/dev/null || true

REQUIRED_PORTS=($SOLR_PORT $OS_PORT $SHIM_PORT)
BUSY_PORTS=()
for port in "${REQUIRED_PORTS[@]}"; do
  if ss -tlnH "sport = :$port" 2>/dev/null | grep -q . || \
     lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    BUSY_PORTS+=("$port")
  fi
done

if [ ${#BUSY_PORTS[@]} -gt 0 ]; then
  echo -e "${RED}Pre-flight check failed: required ports already in use${RESET}"
  echo ""
  for port in "${BUSY_PORTS[@]}"; do
    echo -e "  ${BOLD}$port${RESET}  — stop whatever is listening on this port"
  done
  echo ""
  info "These ports are needed by docker-compose. Free them and re-run."
  exit 1
fi
info "Ports ${REQUIRED_PORTS[*]} are free — OK"
echo ""

# =============================================================================
# 1. BUILD
# =============================================================================
if [ "$SKIP_BUILD" = false ]; then
  banner "Step 1/5: Build"

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
banner "Step 2/5: Start Services"

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

# =============================================================================
# 3. SEED SOLR (SOURCE)
# =============================================================================
banner "Step 3/5: Seed Solr (SOURCE)"

COLLECTION="techproducts"

step "Creating SolrCloud collection '$COLLECTION'..."
detail "GET ${SOLR_URL}/solr/admin/collections?action=CREATE&name=${COLLECTION}&numShards=1&replicationFactor=1"
curl -sf "${SOLR_URL}/solr/admin/collections?action=CREATE&name=${COLLECTION}&numShards=1&replicationFactor=1" >/dev/null
info "SolrCloud collection created (1 shard, RF=1)"

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
# 4. MIGRATE: Export from Solr → Transform → Load into OpenSearch
# =============================================================================
banner "Step 4/5: Migrate Data (Solr → OpenSearch)"

echo -e "  ${BOLD}Migration pipeline:${RESET}"
echo -e "  ${CYAN}┌──────────────┐     ┌───────────┐     ┌──────────────────┐${RESET}"
echo -e "  ${CYAN}│ Solr :${SOLR_PORT} │────▶│ Transform │────▶│ OpenSearch :${OS_PORT} │${RESET}"
echo -e "  ${CYAN}│   (export)   │     │ (python3) │     │    (bulk API)    │${RESET}"
echo -e "  ${CYAN}└──────────────┘     └───────────┘     └──────────────────┘${RESET}"
echo ""

# --- 4a. Export all docs from Solr -------------------------------------------
step "4a. Exporting all documents from Solr..."
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

# --- 4b. Transform: Solr JSON → OpenSearch index + bulk format ----------------
step "4b. Transforming Solr docs → OpenSearch mappings + bulk format..."
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
step "4c. Converting Solr export to OpenSearch _bulk format..."
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

# --- 4d. Load into OpenSearch via _bulk API -----------------------------------
step "4d. Loading into OpenSearch via _bulk API..."
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
# 5. RUN ASSERTIONS
# =============================================================================
banner "Step 5/5: Verify Migration"

# --- Health checks ---
step "Health checks"
assert_http_ok "Solr is reachable (port ${SOLR_PORT})" \
  "${SOLR_URL}/solr/admin/info/system"
assert_http_ok "OpenSearch is reachable (port ${OS_PORT})" \
  "${OS_URL}"
assert_http_ok "Shim proxy is reachable (port ${SHIM_PORT})" \
  "${SHIM_URL}"
echo ""

# --- Source verification: Solr still has the data ---
step "Source verification: Solr (SOURCE) doc count"
detail "GET ${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&rows=0"
SOLR_RESP=$(curl -sf "${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&rows=0")
SOLR_COUNT=$(echo "$SOLR_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['response']['numFound'])")
assert_eq "Solr (SOURCE) still has 5 documents" "5" "$SOLR_COUNT"
echo ""

# --- Target verification: OpenSearch received the data ---
step "Target verification: OpenSearch (TARGET) doc count"
detail "GET ${OS_URL}/${COLLECTION}/_count"
OS_RESP=$(curl -sf "${OS_URL}/${COLLECTION}/_count")
OS_COUNT=$(echo "$OS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['count'])")
assert_eq "OpenSearch (TARGET) has 5 migrated documents" "5" "$OS_COUNT"
echo ""

# --- Target verification: spot-check a specific document ---
step "Target verification: spot-check migrated document TP-002"
detail "GET ${OS_URL}/${COLLECTION}/_doc/TP-002"
DOC_RESP=$(curl -sf "${OS_URL}/${COLLECTION}/_doc/TP-002")
assert_contains "Doc TP-002 exists in OpenSearch" '"found":true' "$DOC_RESP"
assert_contains "Doc TP-002 has correct name" "OpenSearch Migration Guide" "$DOC_RESP"
assert_contains "Doc TP-002 has correct category" '"cat"' "$DOC_RESP"
assert_contains "Doc TP-002 category is 'migration'" 'migration' "$DOC_RESP"
echo ""

# --- Shim proxy: match-all query ---
step "Shim proxy: Solr-format query → OpenSearch (via proxy)"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&wt=json"
info "This sends a Solr query to the proxy, which translates it to OpenSearch Query DSL"
PROXY_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&wt=json")
assert_contains "Proxy response has Solr 'responseHeader'" "responseHeader" "$PROXY_RESP"
assert_contains "Proxy response has Solr 'response' wrapper" '"response"' "$PROXY_RESP"
assert_contains "Proxy response has 'numFound'" "numFound" "$PROXY_RESP"

PROXY_COUNT=$(echo "$PROXY_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['response']['numFound'])" 2>/dev/null || echo "PARSE_ERROR")
assert_eq "Proxy returns all 5 migrated docs" "5" "$PROXY_COUNT"
echo ""

# --- Shim proxy: keyword query ---
step "Shim proxy: keyword search through proxy"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=OpenSearch&wt=json"
info "Tests that Solr q= parameter is translated to OpenSearch query_string"
KEYWORD_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=OpenSearch&wt=json")
assert_contains "Keyword query returns results" "numFound" "$KEYWORD_RESP"
assert_contains "Keyword 'OpenSearch' finds doc TP-002" "TP-002" "$KEYWORD_RESP"
echo ""

# --- Shim proxy: field list ---
step "Shim proxy: field list (fl) parameter"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&fl=id,name&rows=1"
FL_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&fl=id,name&rows=1")
assert_contains "fl=id,name returns id field" '"id"' "$FL_RESP"
assert_contains "fl=id,name returns name field" '"name"' "$FL_RESP"
echo ""

# --- Shim proxy: rows parameter ---
step "Shim proxy: rows parameter limits results"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&rows=2"
ROWS_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&rows=2")
ROWS_COUNT=$(echo "$ROWS_RESP" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['response']['docs']))" 2>/dev/null || echo "PARSE_ERROR")
assert_eq "rows=2 returns exactly 2 docs" "2" "$ROWS_COUNT"
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
banner "Results"

TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo -e "  ${BOLD}Passed: ${GREEN}${PASS_COUNT}${RESET}${BOLD} / ${TOTAL}${RESET}"

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo -e "  ${BOLD}Failed: ${RED}${FAIL_COUNT}${RESET}"
  echo ""
  if [ "$NO_TEARDOWN" = false ]; then
    info "Tip: re-run with --no-teardown to inspect containers after failure"
  fi
  exit 1
else
  echo -e "  ${GREEN}All assertions passed.${RESET}"
  echo ""
  echo -e "  ${BOLD}What was proven:${RESET}"
  info "  1. Solr seeded with TechProducts data (SOURCE)"
  info "  2. Data exported FROM Solr via /select JSON API"
  info "  3. Solr docs transformed → OpenSearch bulk format (field type mapping)"
  info "  4. Data loaded INTO OpenSearch via _bulk API (TARGET)"
  info "  5. Migrated data verified in OpenSearch (count + spot-check)"
  info "  6. Shim proxy translates Solr queries → OpenSearch against migrated data"
  echo ""
  exit 0
fi
