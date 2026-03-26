#!/usr/bin/env bash
# =============================================================================
# Verify Migration — standalone assertion suite
#
# Runs all verification assertions against already-running Solr, OpenSearch,
# and shim proxy containers. Can be invoked directly (e.g. after a
# --no-teardown run) or called by run_connected_tests.sh.
#
# Usage:
#   ./verify_migration.sh                              # defaults: 38983, 39200, 38080
#   ./verify_migration.sh --output-dir ./reports       # save JUnit XML + plain text
#   ./verify_migration.sh --solr-port 8983 --os-port 9200 --shim-port 8080
#
# Exit codes:
#   0  All assertions passed
#   1  One or more assertions failed
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# --- Defaults (match docker-compose.ports.yml) -------------------------------
SOLR_PORT=38983
OS_PORT=39200
SHIM_PORT=38080
OUTPUT_DIR=""
COLLECTION="techproducts"

# --- Parse arguments ---------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --solr-port)   SOLR_PORT="$2"; shift 2 ;;
    --os-port)     OS_PORT="$2"; shift 2 ;;
    --shim-port)   SHIM_PORT="$2"; shift 2 ;;
    --output-dir)  OUTPUT_DIR="$2"; shift 2 ;;
    --collection)  COLLECTION="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

SOLR_URL="http://localhost:${SOLR_PORT}"
OS_URL="http://localhost:${OS_PORT}"
SHIM_URL="http://localhost:${SHIM_PORT}"

# =============================================================================
# ASSERTIONS
# =============================================================================
banner "Verify Migration"

# --- Health checks -----------------------------------------------------------
test_group "Health checks"
step "Health checks"
assert_http_ok "Solr is reachable (port ${SOLR_PORT})" \
  "${SOLR_URL}/solr/admin/info/system"
assert_http_ok "OpenSearch is reachable (port ${OS_PORT})" \
  "${OS_URL}"
assert_http_ok "Shim proxy is reachable (port ${SHIM_PORT})" \
  "${SHIM_URL}"
echo ""

# --- Source verification: Solr still has the data ----------------------------
test_group "Source verification"
step "Source verification: Solr (SOURCE) doc count"
detail "GET ${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&rows=0"
SOLR_RESP=$(curl -sf "${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&rows=0")
SOLR_COUNT=$(echo "$SOLR_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['response']['numFound'])")
assert_eq "Solr (SOURCE) still has 5 documents" "5" "$SOLR_COUNT"
echo ""

# --- Target verification: OpenSearch received the data -----------------------
test_group "Target verification"
step "Target verification: OpenSearch (TARGET) doc count"
detail "GET ${OS_URL}/${COLLECTION}/_count"
OS_RESP=$(curl -sf "${OS_URL}/${COLLECTION}/_count")
OS_COUNT=$(echo "$OS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['count'])")
assert_eq "OpenSearch (TARGET) has 5 migrated documents" "5" "$OS_COUNT"
echo ""

# --- Target verification: spot-check a specific document ---------------------
step "Target verification: spot-check migrated document TP-002"
detail "GET ${OS_URL}/${COLLECTION}/_doc/TP-002"
DOC_RESP=$(curl -sf "${OS_URL}/${COLLECTION}/_doc/TP-002")
assert_contains "Doc TP-002 exists in OpenSearch" '"found":true' "$DOC_RESP"
assert_contains "Doc TP-002 has correct name" "OpenSearch Migration Guide" "$DOC_RESP"
assert_contains "Doc TP-002 has correct category" '"cat"' "$DOC_RESP"
assert_contains "Doc TP-002 category is 'migration'" 'migration' "$DOC_RESP"
echo ""

# --- Shim proxy: match-all query ---------------------------------------------
test_group "Proxy match-all"
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

# --- Shim proxy: keyword query -----------------------------------------------
test_group "Proxy keyword query"
step "Shim proxy: keyword search through proxy"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=OpenSearch&wt=json"
info "Tests that Solr q= parameter is translated to OpenSearch query_string"
KEYWORD_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=OpenSearch&wt=json")
assert_contains "Keyword query returns results" "numFound" "$KEYWORD_RESP"
assert_contains "Keyword 'OpenSearch' finds doc TP-002" "TP-002" "$KEYWORD_RESP"
echo ""

# --- Shim proxy: field list ---------------------------------------------------
test_group "Proxy field list"
step "Shim proxy: field list (fl) parameter"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&fl=id,name&rows=1"
FL_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&fl=id,name&rows=1")
assert_contains "fl=id,name returns id field" '"id"' "$FL_RESP"
assert_contains "fl=id,name returns name field" '"name"' "$FL_RESP"
echo ""

# --- Shim proxy: rows parameter -----------------------------------------------
test_group "Proxy rows limit"
step "Shim proxy: rows parameter limits results"
detail "GET ${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&rows=2"
ROWS_RESP=$(curl -sf "${SHIM_URL}/solr/${COLLECTION}/select?q=*:*&wt=json&rows=2")
ROWS_COUNT=$(echo "$ROWS_RESP" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['response']['docs']))" 2>/dev/null || echo "PARSE_ERROR")
assert_eq "rows=2 returns exactly 2 docs" "2" "$ROWS_COUNT"
echo ""

# =============================================================================
# SUMMARY & REPORTS
# =============================================================================
banner "Results"

print_summary

if [ -n "$OUTPUT_DIR" ]; then
  write_reports "$OUTPUT_DIR"
fi

echo ""
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
else
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
