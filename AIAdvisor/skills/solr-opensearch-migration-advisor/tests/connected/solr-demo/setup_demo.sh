#!/usr/bin/env bash
# ============================================================================
# Full demo setup: create collection, load 200K docs, generate traffic.
#
# Prerequisites:
#   cd tests/connected && docker compose up -d
#
# Usage:
#   bash solr-demo/setup_demo.sh                    # full setup (200K docs, 15 min traffic)
#   bash solr-demo/setup_demo.sh --quick            # quick setup (10K docs, 2 min traffic)
#   bash solr-demo/setup_demo.sh --data-only        # data only, no traffic
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOLR_URL="${SOLR_URL:-http://localhost:38983}"
COLLECTION="ecommerce"

MODE="${1:---full}"

case "$MODE" in
  --quick)
    NUM_DOCS=10000
    TRAFFIC_MINUTES=2
    ;;
  --data-only)
    NUM_DOCS=200000
    TRAFFIC_MINUTES=0
    ;;
  *)
    NUM_DOCS=200000
    TRAFFIC_MINUTES=15
    ;;
esac

echo "============================================================"
echo "  Solr Migration Demo Setup"
echo "  Mode: ${MODE}"
echo "  Solr: ${SOLR_URL}"
echo "  Docs: ${NUM_DOCS}"
echo "  Traffic: ${TRAFFIC_MINUTES} minutes"
echo "============================================================"
echo ""

# --- Wait for Solr ---
echo "Waiting for Solr..."
for i in {1..30}; do
  if curl -sf "${SOLR_URL}/solr/admin/info/system?wt=json" > /dev/null 2>&1; then
    echo "  Solr is ready."
    break
  fi
  [ "$i" -eq 30 ] && echo "ERROR: Solr not available at ${SOLR_URL}" && exit 1
  sleep 2
done

# --- Create collection with custom configset ---
echo ""
echo "Creating collection '${COLLECTION}' with ecommerce configset..."

# Copy configset into Solr's configset directory (already mounted via docker-compose volume)
# Create the core using the configset
if curl -sf "${SOLR_URL}/solr/${COLLECTION}/admin/ping?wt=json" > /dev/null 2>&1; then
  echo "  Collection '${COLLECTION}' already exists, skipping creation."
else
  curl -sf "${SOLR_URL}/solr/admin/cores?action=CREATE&name=${COLLECTION}&configSet=ecommerce" > /dev/null 2>&1 || {
    echo "  Failed to create core. Trying via docker exec..."
    docker compose exec -T solr solr create_core -c "${COLLECTION}" -d ecommerce 2>/dev/null || true
  }
  echo "  Collection created."
fi

# --- Load data ---
echo ""
bash "${SCRIPT_DIR}/generate_data.sh" "${SOLR_URL}" "${NUM_DOCS}"

# Verify
doc_count=$(curl -sf "${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&rows=0&wt=json" | \
  jq -r '.response.numFound' 2>/dev/null || echo "?")
echo ""
echo "Indexed documents: ${doc_count}"

# --- Generate traffic ---
if [ "$TRAFFIC_MINUTES" -gt 0 ]; then
  echo ""
  bash "${SCRIPT_DIR}/generate_traffic.sh" "${SOLR_URL}" "${TRAFFIC_MINUTES}"
fi

echo ""
echo "============================================================"
echo "  Demo setup complete!"
echo ""
echo "  Inspect with migration advisor:"
echo "    python -c \""
echo "    from solr_inspector import SolrInspector"
echo "    si = SolrInspector('${SOLR_URL}')"
echo "    import json"
echo "    print(json.dumps(si.get_system_info()['lucene'], indent=2))"
echo "    print('Collections:', si.list_collections())"
echo "    luke = si.get_luke('${COLLECTION}')"
echo "    print('Documents:', luke['index']['numDocs'])"
echo "    \""
echo ""
echo "  Or run the full test suite:"
echo "    python -m pytest tests/connected/test_solr_inspector.py -v"
echo "============================================================"
