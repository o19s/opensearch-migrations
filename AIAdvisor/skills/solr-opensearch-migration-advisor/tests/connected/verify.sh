#!/usr/bin/env bash
# Verify Solr TechProducts is running and loaded.
# Expects: docker compose up -d (from this directory) already done.
#
# Usage: bash verify.sh

set -euo pipefail

SOLR_URL="${SOLR_URL:-http://localhost:38983}"
PASS=0
FAIL=0

check() {
  if eval "$2" >/dev/null 2>&1; then
    echo "  PASS: $1"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $1"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Solr TechProducts verification ==="

check "Solr is reachable" \
  "curl -sf ${SOLR_URL}/solr/admin/info/system | jq -e '.lucene'"

check "techproducts collection exists (SolrCloud)" \
  "curl -sf '${SOLR_URL}/solr/admin/collections?action=LIST&wt=json' | jq -e '.collections | index(\"techproducts\")'"

check "techproducts has documents" \
  "curl -sf '${SOLR_URL}/solr/techproducts/select?q=*:*&rows=0&wt=json' | jq -e '.response.numFound > 0'"

check "schema has expected fields" \
  "curl -sf '${SOLR_URL}/solr/techproducts/schema/fields?wt=json' | jq -e '[.fields[].name] | contains([\"id\",\"name\",\"manu\",\"cat\"])'"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] || exit 1
