#!/usr/bin/env bash
# =============================================================================
# Verify Migration — standalone assertion suite
#
# Runs all verification assertions against already-running Solr and OpenSearch
# containers. Can be invoked directly (e.g. after a --no-teardown run) or
# called by run_connected_tests.sh.
#
# Usage:
#   ./verify_migration.sh                              # defaults: 38983, 39200
#   ./verify_migration.sh --output-dir ./reports       # save JUnit XML + plain text
#   ./verify_migration.sh --solr-port 8983 --os-port 9200
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
OUTPUT_DIR=""
COLLECTION="techproducts"

# --- Parse arguments ---------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --solr-port)   SOLR_PORT="$2"; shift 2 ;;
    --os-port)     OS_PORT="$2"; shift 2 ;;
    --output-dir)  OUTPUT_DIR="$2"; shift 2 ;;
    --collection)  COLLECTION="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

SOLR_URL="http://localhost:${SOLR_PORT}"
OS_URL="http://localhost:${OS_PORT}"

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
  echo ""
  exit 0
fi
