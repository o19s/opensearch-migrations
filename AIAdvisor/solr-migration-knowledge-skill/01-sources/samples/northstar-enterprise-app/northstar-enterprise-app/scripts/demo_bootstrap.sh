#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENSEARCH_URL="${NORTHSTAR_OPENSEARCH_URL:-http://localhost:9200}"

cd "$APP_DIR"

echo "Starting OpenSearch demo stack..."
docker compose up -d

echo "Waiting for OpenSearch at ${OPENSEARCH_URL}..."
for _ in $(seq 1 45); do
  if curl -fsS "${OPENSEARCH_URL}/_cluster/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Creating index and bulk-loading sample corpus..."
python scripts/reindex_northstar.py \
  --opensearch-url "${OPENSEARCH_URL}" \
  --create-index \
  --recreate

echo "Demo bootstrap complete."
echo "OpenSearch: ${OPENSEARCH_URL}"
echo "Dashboards: http://localhost:${NORTHSTAR_DASHBOARDS_PORT:-5601}"
echo "Start app: GRADLE_USER_HOME=.gradle gradle bootRun"
