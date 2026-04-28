#!/usr/bin/env bash
# Clone solr-tmdb, start Solr on port 38984, load TMDB data.
#
# Usage:
#   bash setup.sh          # start and load
#   bash setup.sh teardown # stop and clean up

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLONE_DIR="$SCRIPT_DIR/solr-tmdb"
SOLR_PORT=38984
SOLR_URL="http://localhost:$SOLR_PORT"

if [[ "${1:-}" == "teardown" ]]; then
  cd "$CLONE_DIR" 2>/dev/null && docker compose down -v || true
  # Files owned by Solr uid 8983 need docker to remove
  docker run --rm -v "$CLONE_DIR:/clone" alpine rm -rf /clone 2>/dev/null || rm -rf "$CLONE_DIR"
  echo "Cleaned up."
  exit 0
fi

if [[ ! -d "$CLONE_DIR" ]]; then
  git clone --depth 1 https://github.com/o19s/solr-tmdb.git "$CLONE_DIR"
fi

cd "$CLONE_DIR"

# Remap to port 38984 to avoid conflicts with local Solr instances
sed -i "s/\"8983:8983\"/\"${SOLR_PORT}:8983\"/" docker-compose.yml

# Fix permissions for Linux (Solr runs as uid 8983 inside the container).
# Use docker to avoid requiring sudo.
if [[ "$(uname -s)" == "Linux" ]]; then
  docker run --rm -v "$PWD/solr_home:/solr_home" alpine chown -R 8983:8983 /solr_home
fi

docker compose up -d --build

echo "Waiting for Solr on port $SOLR_PORT..."
for i in $(seq 1 30); do
  if curl -sf "$SOLR_URL/solr/tmdb/admin/ping" >/dev/null 2>&1; then
    echo "Solr is up. Loading data..."
    if [[ ! -f tmdb_solr.json ]]; then
      unzip tmdb_solr.json.zip
    fi
    curl -s "$SOLR_URL/solr/tmdb/update?commit=true" \
      --data-binary @tmdb_solr.json -H 'Content-type:application/json' >/dev/null
    echo "Done. Solr TMDB ready at $SOLR_URL"
    exit 0
  fi
  sleep 2
done

echo "ERROR: Solr did not become healthy in time" >&2
exit 1
