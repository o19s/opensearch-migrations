#!/usr/bin/env bash
#
# populate_solr_tenants.sh
#
# Creates 10 collections (techproducts_tenant0 .. techproducts_tenant9) on a
# Solr 9.7 instance using the Collections API (v1, /solr/admin/collections),
# all backed by the same configset "products", each with a different
# shard/replica topology, then indexes the stock techproducts.xml sample
# dataset into every collection.
#
# Requirements: bash, curl, awk. Optionally `bin/solr` if you want the script
# to upload the configset for you (see UPLOAD_CONFIGSET below).
#
# Usage:
#   ./populate_solr_tenants.sh
#
# Env overrides:
#   SOLR_URL            (default: http://localhost:8983)
#   CONFIGSET_NAME       (default: products)
#   CONFIGSET_DIR        (default: unset -> skip upload, assume it exists)
#   TECHPRODUCTS_XML     (default: downloads from Solr's GitHub repo)
#   ZK_HOST              (optional, only needed for bin/solr zk upconfig)

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SOLR_URL="${SOLR_URL:-http://localhost:8983}"
CONFIGSET_NAME="${CONFIGSET_NAME:-products}"
CONFIGSET_DIR="${CONFIGSET_DIR:-}"        # e.g. /opt/solr/server/solr/configsets/sample_techproducts_configs/conf
ZK_HOST="${ZK_HOST:-}"                    # e.g. localhost:9983
TECHPRODUCTS_XML="${TECHPRODUCTS_XML:-./techproducts.xml}"
TECHPRODUCTS_XML_URL="https://raw.githubusercontent.com/apache/solr/main/solr/solrj/src/test-files/solrj/techproducts.xml"

COLLECTIONS_API="${SOLR_URL}/solr/admin/collections"
CONFIGS_API="${SOLR_URL}/solr/admin/configs"

# ---------------------------------------------------------------------------
# Per-tenant topology definitions
#
# Each entry is: "name|extraParams"
# extraParams is a literal query-string fragment appended to the CREATE call.
# This is where the "varying collection creation params" live: different
# numShards / replicationFactor combos, named shards via the `shards` param,
# and per-replica-type counts (nrt/tlog/pull replicas).
# ---------------------------------------------------------------------------
declare -a TENANTS=(
  # tenant0: the simplest possible topology - single shard, single replica
  "techproducts_tenant0|numShards=1&replicationFactor=1"

  # tenant1: single shard, 3 replicas (read-heavy, small dataset)
  "techproducts_tenant1|numShards=1&replicationFactor=3"

  # tenant2: 2 shards, 2 replicas each
  "techproducts_tenant2|numShards=2&replicationFactor=2"

  # tenant3: 3 auto-named shards, replicationFactor 1
  "techproducts_tenant3|numShards=3&replicationFactor=1"

  # tenant4: named shards instead of auto-generated shard1/shard2/...
  "techproducts_tenant4|shards=east,west&replicationFactor=1&router.name=implicit"

  # tenant5: another named-shard layout, single replica per shard
  "techproducts_tenant5|shards=alpha,beta,gamma&replicationFactor=1&router.name=implicit"

  # tenant6: 4 shards, single replica each (max horizontal split, no HA)
  "techproducts_tenant6|numShards=4&replicationFactor=1"

  # tenant7: 2 shards using explicit replica-type counts: 2 NRT + 1 TLOG + 1 PULL per shard
  "techproducts_tenant7|numShards=2&nrtReplicas=2&tlogReplicas=1&pullReplicas=1"

  # tenant8: single shard, single replica, but capped placement via maxShardsPerNode
  "techproducts_tenant8|numShards=1&replicationFactor=1&maxShardsPerNode=1"

  # tenant9: 3 shards, mixed replication (2 NRT + 1 PULL per shard) for a search-heavy tenant
  "techproducts_tenant9|numShards=3&nrtReplicas=2&pullReplicas=1"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()  { printf '[%(%H:%M:%S)T] %s\n' -1 "$*"; }
die()  { log "ERROR: $*"; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command '$1' not found on PATH"
}

check_solr_up() {
  log "Checking Solr is reachable at ${SOLR_URL} ..."
  curl -sf "${SOLR_URL}/solr/admin/info/system" >/dev/null \
    || die "Solr does not appear to be up at ${SOLR_URL}"
  log "Solr is up."
}

# ---------------------------------------------------------------------------
# Step 0: sanity checks
# ---------------------------------------------------------------------------
require_cmd curl
require_cmd awk
check_solr_up

# ---------------------------------------------------------------------------
# Step 1: make sure the "products" configset exists
# ---------------------------------------------------------------------------
configset_exists() {
  local resp
  resp="$(curl -sf "${CONFIGS_API}?action=LIST&wt=json")" || die "failed to list configsets"
  # crude but dependency-free JSON check: look for "products" in the configSets array
  echo "$resp" | grep -q "\"${CONFIGSET_NAME}\""
}

if configset_exists; then
  log "Configset '${CONFIGSET_NAME}' already exists in Solr — reusing it."
else
  if [[ -n "${CONFIGSET_DIR}" ]]; then
    log "Configset '${CONFIGSET_NAME}' not found. Uploading from ${CONFIGSET_DIR} ..."
    if [[ -n "${ZK_HOST}" ]] && command -v solr >/dev/null 2>&1; then
      solr zk upconfig -z "${ZK_HOST}" -n "${CONFIGSET_NAME}" -d "${CONFIGSET_DIR}"
    else
      # Fallback: Configsets API upload requires a zipped configset
      TMP_ZIP="$(mktemp -d)/${CONFIGSET_NAME}.zip"
      (cd "${CONFIGSET_DIR}" && zip -r "${TMP_ZIP}" . >/dev/null)
      curl -sf -X POST --header "Content-Type:application/octet-stream" \
        --data-binary @"${TMP_ZIP}" \
        "${CONFIGS_API}?action=UPLOAD&name=${CONFIGSET_NAME}" \
        || die "failed to upload configset via Configs API"
    fi
    log "Configset '${CONFIGSET_NAME}' uploaded."
  else
    die "Configset '${CONFIGSET_NAME}' does not exist in Solr and CONFIGSET_DIR was not provided to upload it. \
Set CONFIGSET_DIR (and optionally ZK_HOST) or upload the configset manually first, e.g.: \
bin/solr zk upconfig -z <zkhost> -n ${CONFIGSET_NAME} -d /path/to/products/conf"
  fi
fi

# ---------------------------------------------------------------------------
# Step 2: fetch techproducts.xml if not already present locally
# ---------------------------------------------------------------------------
if [[ ! -f "${TECHPRODUCTS_XML}" ]]; then
  log "Downloading sample dataset techproducts.xml ..."
  curl -sf -o "${TECHPRODUCTS_XML}" "${TECHPRODUCTS_XML_URL}" \
    || die "failed to download techproducts.xml from ${TECHPRODUCTS_XML_URL}"
fi
[[ -s "${TECHPRODUCTS_XML}" ]] || die "techproducts.xml is missing or empty at ${TECHPRODUCTS_XML}"
log "Using dataset: ${TECHPRODUCTS_XML}"

# ---------------------------------------------------------------------------
# Step 3: create collections + index data
# ---------------------------------------------------------------------------
create_collection() {
  local name="$1" extra="$2"
  local url="${COLLECTIONS_API}?action=CREATE&name=${name}&collection.configName=${CONFIGSET_NAME}&${extra}&wt=json"

  log "Creating collection '${name}' with params: ${extra}"
  local resp status
  resp="$(curl -sf -w '\n%{http_code}' "${url}")" || die "CREATE request failed for ${name}"
  status="$(echo "$resp" | tail -n1)"
  body="$(echo "$resp" | sed '$d')"

  if [[ "$status" != "200" ]]; then
    die "Failed to create collection '${name}' (HTTP ${status}): ${body}"
  fi
  log "Collection '${name}' created successfully."
}

wait_for_collection_active() {
  local name="$1"
  local tries=30
  log "Waiting for '${name}' to become active ..."
  until curl -sf "${SOLR_URL}/solr/${name}/admin/ping?wt=json" \
        | grep -q '"status":"OK"'; do
    tries=$((tries - 1))
    if [[ $tries -le 0 ]]; then
      die "Collection '${name}' did not become active in time"
    fi
    sleep 2
  done
  log "Collection '${name}' is active."
}

index_techproducts() {
  local name="$1"
  log "Indexing techproducts.xml into '${name}' ..."
  curl -sf -X POST "${SOLR_URL}/solr/${name}/update?commit=true" \
    -H "Content-Type: application/xml" \
    --data-binary @"${TECHPRODUCTS_XML}" \
    || die "Failed to index data into '${name}'"

  local count
  count="$(curl -sf "${SOLR_URL}/solr/${name}/select?q=*:*&rows=0&wt=json" \
    | awk -F'"numFound":' '{print $2}' | awk -F',' '{print $1}')"
  log "Collection '${name}' now has ${count:-?} documents."
}

for entry in "${TENANTS[@]}"; do
  name="${entry%%|*}"
  extra="${entry#*|}"

  create_collection "$name" "$extra"
  wait_for_collection_active "$name"
  index_techproducts "$name"
  echo
done

log "All 10 tenant collections created and populated successfully."
