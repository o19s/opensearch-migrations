#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE="${1:-both}"
OPENSEARCH_URL="${OPENSEARCH_URL:-http://localhost:9200}"
ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9201}"

cd "$ROOT_DIR"

wait_for_cluster() {
  local name="$1"
  local url="$2"

  echo "Waiting for ${name} at ${url}..."
  for _ in $(seq 1 60); do
    if curl -fsS "${url}/_cluster/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "${name} did not become healthy in time" >&2
  return 1
}

case "$ENGINE" in
  opensearch)
    docker compose --profile opensearch-demo up -d
    wait_for_cluster "OpenSearch" "$OPENSEARCH_URL"
    python tools/bootstrap_search_demos.py --engine opensearch --opensearch-url "$OPENSEARCH_URL" --recreate
    ;;
  elasticsearch)
    docker compose --profile elasticsearch-demo up -d
    wait_for_cluster "Elasticsearch" "$ELASTICSEARCH_URL"
    python tools/bootstrap_search_demos.py --engine elasticsearch --elasticsearch-url "$ELASTICSEARCH_URL" --recreate
    ;;
  both)
    docker compose --profile opensearch-demo --profile elasticsearch-demo up -d
    wait_for_cluster "OpenSearch" "$OPENSEARCH_URL"
    wait_for_cluster "Elasticsearch" "$ELASTICSEARCH_URL"
    python tools/bootstrap_search_demos.py --engine both --opensearch-url "$OPENSEARCH_URL" --elasticsearch-url "$ELASTICSEARCH_URL" --recreate
    ;;
  *)
    echo "Usage: $0 [opensearch|elasticsearch|both]" >&2
    exit 1
    ;;
esac

echo "Search demo stack is ready."
echo "OpenSearch: ${OPENSEARCH_URL}"
echo "OpenSearch Dashboards: http://localhost:${OPENSEARCH_DASHBOARDS_PORT:-5601}"
echo "Elasticsearch: ${ELASTICSEARCH_URL}"
echo "Kibana: http://localhost:${KIBANA_HOST_PORT:-5602}"
echo "Northstar app: cd 01-sources/samples/northstar-enterprise-app/northstar-enterprise-app && GRADLE_USER_HOME=.gradle gradle bootRun"
