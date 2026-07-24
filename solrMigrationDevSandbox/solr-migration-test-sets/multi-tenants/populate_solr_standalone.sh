#!/usr/bin/env bash
#
# populate_solr_standalone.sh
#
# Standalone / user-managed-mode counterpart to populate_solr_solrcloud.sh.
#
# Creates 10 cores (techproducts_tenant0 .. techproducts_tenant9) on a
# Solr 9.7 instance running WITHOUT SolrCloud/ZooKeeper, using the Core
# Admin API (/solr/admin/cores), all derived from the same on-disk
# configset "products", each with a different core-level creation
# topology (there are no shards/replicas in standalone mode, so the
# "varying params" here are the standalone-relevant ones: dataDir,
# transient/loadOnStartup, custom core.properties, isolated vs. shared
# instance dirs, and async creation). Finally indexes the stock
# techproducts.xml sample dataset into every core.
#
# Key differences from the SolrCloud version:
#   * No Collections API                -> Core Admin API (/solr/admin/cores)
#   * No collection.configName / ZK     -> configsets live on local disk
#     under $CONFIGSET_BASE_DIR, referenced via the CREATE action's
#     `configSet` param (Solr copies them into each core's instanceDir)
#   * No numShards/replicationFactor/etc -> per-core params instead:
#     dataDir, instanceDir, transient, loadOnStartup, property.*, async
#   * Schema API edits on a SolrCloud collection land in the shared ZK
#     configset automatically; in standalone mode a core's conf/ is a
#     private COPY the moment it's created, so to keep the shared
#     "products" configset optimized for future cores we edit it via a
#     throwaway bootstrap core and then copy its conf/ back over the
#     shared configset directory before deleting the bootstrap core.
#
# Requirements: bash, curl, awk, cp/rsync. This script assumes it runs on
# the same host/filesystem as the Solr instance (or a shared volume/mount),
# since standalone-mode configsets are plain directories on disk rather
# than something reachable purely over HTTP the way SolrCloud's Configs
# API is.
#
# Usage:
#   ./populate_solr_standalone.sh
#
# Env overrides:
#   SOLR_URL              (default: http://localhost:8983)
#   SOLR_HOME              (default: /var/solr/data) filesystem path to the
#                          Solr home directory used by the running instance
#   CONFIGSET_BASE_DIR     (default: ${SOLR_HOME}/configsets) directory Solr
#                          scans for shared configsets referenced by name
#                          via the CREATE action's `configSet` param
#   CONFIGSET_NAME         (default: products)
#   BASE_CONFIGSET_DIR     (default: unset) filesystem path to an existing
#                          configset's conf/ dir (e.g. Solr's bundled
#                          _default) used to seed CONFIGSET_NAME if it
#                          doesn't exist yet on disk
#   TECHPRODUCTS_XML       (default: ./techproducts.xml)
#   OPTIMIZE_SCHEMA        (default: true) apply techproducts-specific field
#                          definitions to the shared "products" configset
#                          after it is seeded from BASE_CONFIGSET_DIR
#   CORE_PREFIX            (default: techproducts_tenant)
#   SOLR_BASIC_AUTH        (default: unset) "user:pass" for curl -u

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SOLR_URL="${SOLR_URL:-http://localhost:8983}"
SOLR_HOME="${SOLR_HOME:-/var/solr/data}"
CONFIGSET_BASE_DIR="${CONFIGSET_BASE_DIR:-${SOLR_HOME}/configsets}"
CONFIGSET_NAME="${CONFIGSET_NAME:-products}"
BASE_CONFIGSET_DIR="${BASE_CONFIGSET_DIR:-}"   # e.g. /opt/solr/server/solr/configsets/_default/conf
OPTIMIZE_SCHEMA="${OPTIMIZE_SCHEMA:-true}"
TECHPRODUCTS_XML="${TECHPRODUCTS_XML:-./techproducts.xml}"
TECHPRODUCTS_XML_URL="https://raw.githubusercontent.com/apache/solr/main/solr/solrj/src/test-files/solrj/techproducts.xml"
CORE_PREFIX="${CORE_PREFIX:-techproducts_tenant}"
SOLR_BASIC_AUTH="${SOLR_BASIC_AUTH:-}"
if [[ "$SOLR_BASIC_AUTH" != "" ]]; then
  SOLR_BASIC_AUTH="-u ${SOLR_BASIC_AUTH}"
fi

CORE_ADMIN_API="${SOLR_URL}/solr/admin/cores"

CONFIGSET_DEST_DIR="${CONFIGSET_BASE_DIR}/${CONFIGSET_NAME}"
CONFIGSET_DEST_CONF="${CONFIGSET_DEST_DIR}/conf"

# ---------------------------------------------------------------------------
# Per-tenant core-creation params
#
# Each entry is: "name|extraParams"
# extraParams is a literal query-string fragment appended to the CREATE
# call. Standalone cores have no shard/replica topology, so instead this
# demonstrates the knobs that actually vary per-core in user-managed mode:
# custom dataDir locations, transient/lazy-loaded cores, isolated (private,
# non-shared) instance dirs, custom core.properties passed via property.*,
# and asynchronous core creation.
# ---------------------------------------------------------------------------
declare -a TENANTS=(
  # tenant0: the simplest possible core - shared configset, default dataDir
  "${CORE_PREFIX}0|configSet=${CONFIGSET_NAME}"

  # tenant1: shared configset, but data lives on a custom dataDir path
  "${CORE_PREFIX}1|configSet=${CONFIGSET_NAME}&dataDir=data_${CORE_PREFIX}1"

  # tenant2: lazily loaded / unloadable core (transient), good for a
  # low-traffic tenant that shouldn't consume resources until first hit
  "${CORE_PREFIX}2|configSet=${CONFIGSET_NAME}&transient=true&loadOnStartup=false"

  # tenant3: shared configset, but a custom update-log directory via a
  # core.properties override (solrconfig.xml can reference \${tenant.ulogDir})
  "${CORE_PREFIX}3|configSet=${CONFIGSET_NAME}&property.tenant.ulogDir=ulog_${CORE_PREFIX}3"

  # tenant4: shared configset with explicit, non-default config/schema
  # filenames (useful once a tenant needs a bespoke solrconfig later)
  "${CORE_PREFIX}4|configSet=${CONFIGSET_NAME}&config=solrconfig.xml&schema=schema.xml"

  # tenant5: fully isolated instance dir with its OWN private copy of the
  # configset (not the shared one) - use when a tenant needs config that
  # can diverge from the rest without touching the shared configset
  "${CORE_PREFIX}5|instanceDir=${CORE_PREFIX}5&configSet=${CONFIGSET_NAME}"

  # tenant6: custom user-defined property injected into core.properties,
  # e.g. for a solrconfig.xml conditional on tenant tier
  "${CORE_PREFIX}6|configSet=${CONFIGSET_NAME}&property.tenant.tier=premium"

  # tenant7: created asynchronously (returns a requestid we poll instead of
  # blocking on the CREATE call itself)
  "${CORE_PREFIX}7|configSet=${CONFIGSET_NAME}&async=create_${CORE_PREFIX}7"

  # tenant8: shared configset, custom dataDir simulating cold/archive
  # storage tiering for an infrequently-queried tenant
  "${CORE_PREFIX}8|configSet=${CONFIGSET_NAME}&dataDir=archive_${CORE_PREFIX}8/data"

  # tenant9: always-on primary tenant - explicit loadOnStartup=true,
  # transient=false, plus its own ulog dir override
  "${CORE_PREFIX}9|configSet=${CONFIGSET_NAME}&loadOnStartup=true&transient=false&property.tenant.ulogDir=ulog_${CORE_PREFIX}9"
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
  curl "${SOLR_BASIC_AUTH}" -sf "${SOLR_URL}/solr/admin/info/system" >/dev/null \
    || die "Solr does not appear to be up at ${SOLR_URL}"
  log "Solr is up."
}

check_not_cloud_mode() {
  # Best-effort sanity check that we're talking to a standalone instance,
  # not SolrCloud (where /solr/admin/collections would be the right tool).
  local resp
  resp="$(curl "${SOLR_BASIC_AUTH}" -sf "${SOLR_URL}/solr/admin/info/system?wt=json" || true)"
  if echo "$resp" | grep -q '"mode":"solrcloud"'; then
    die "This Solr instance is running in SolrCloud mode. Use populate_solr_tenants.sh (Collections API) instead."
  fi
}

# ---------------------------------------------------------------------------
# Step 0: sanity checks
# ---------------------------------------------------------------------------
require_cmd curl
require_cmd awk
require_cmd cp
check_solr_up
check_not_cloud_mode

[[ -d "${CONFIGSET_BASE_DIR}" ]] || die "CONFIGSET_BASE_DIR '${CONFIGSET_BASE_DIR}' does not exist or is not reachable from this host. \
Set CONFIGSET_BASE_DIR to the configsets directory Solr reads from (often \${SOLR_HOME}/configsets), \
mounted or accessible from wherever this script runs."

# ---------------------------------------------------------------------------
# New: derive "products" from an existing configset (e.g. bundled
# "_default"), then optimize its schema for the techproducts dataset
# (explicit field types instead of relying on schemaless field guessing).
# Because standalone cores copy their conf/ at creation time rather than
# sharing it live, the edits are made on a throwaway bootstrap core and
# then copied back onto the shared on-disk configset.
# ---------------------------------------------------------------------------
create_configset_from_base() {
  log "Seeding configset '${CONFIGSET_NAME}' at ${CONFIGSET_DEST_CONF} from ${BASE_CONFIGSET_DIR} ..."
  mkdir -p "${CONFIGSET_DEST_CONF}"
  cp -r "${BASE_CONFIGSET_DIR}/." "${CONFIGSET_DEST_CONF}/" \
    || die "failed to copy base configset from '${BASE_CONFIGSET_DIR}' to '${CONFIGSET_DEST_CONF}'"
  log "Configset '${CONFIGSET_NAME}' seeded from '${BASE_CONFIGSET_DIR}'."
}

optimize_products_schema() {
  local bootstrap="${CONFIGSET_NAME}_schema_bootstrap"

  # Spin up a throwaway core purely to reach the Schema REST API, which in
  # standalone mode edits that core's own (private) conf/ directory.
  log "Creating temporary bootstrap core '${bootstrap}' to edit configset '${CONFIGSET_NAME}' ..."
  curl "${SOLR_BASIC_AUTH}" -sf "${CORE_ADMIN_API}?action=CREATE&name=${bootstrap}&instanceDir=${bootstrap}&configSet=${CONFIGSET_NAME}&wt=json" \
    || die "failed to create bootstrap core for schema optimization"

  local tries=30
  until curl "${SOLR_BASIC_AUTH}" -sf "${SOLR_URL}/solr/${bootstrap}/admin/ping?wt=json" | grep -q '"status":"OK"'; do
    tries=$((tries - 1))
    [[ $tries -gt 0 ]] || die "bootstrap core '${bootstrap}' never became active"
    sleep 2
  done

  local schema_url="${SOLR_URL}/solr/${bootstrap}/schema"

  add_schema_field() {
    local field_json="$1"
    local resp status body
    resp="$(curl "${SOLR_BASIC_AUTH}" -s -w '\n%{http_code}' -X POST -H 'Content-Type: application/json' \
      --data-binary "{\"add-field\": ${field_json}}" "${schema_url}")"
    status="$(echo "$resp" | tail -n1)"
    body="$(echo "$resp" | sed '$d')"
    if [[ "$status" != "200" ]]; then
      log "WARNING: could not add field ${field_json} (HTTP ${status}): ${body}"
    fi
  }

  log "Applying techproducts-optimized field definitions to bootstrap core '${bootstrap}' ..."

  # Explicit types tuned to techproducts.xml, instead of schemaless guessing:
  add_schema_field '{"name":"name","type":"text_general","indexed":true,"stored":true}'
  add_schema_field '{"name":"manu","type":"text_general","indexed":true,"stored":true}'
  add_schema_field '{"name":"manu_id_s","type":"string","indexed":true,"stored":true}'
  add_schema_field '{"name":"cat","type":"strings","indexed":true,"stored":true}'
  add_schema_field '{"name":"features","type":"text_general","indexed":true,"stored":true,"multiValued":true}'
  add_schema_field '{"name":"includes","type":"text_general","indexed":true,"stored":true}'
  add_schema_field '{"name":"weight","type":"pfloat","indexed":true,"stored":true}'
  add_schema_field '{"name":"price","type":"pfloat","indexed":true,"stored":true}'
  add_schema_field '{"name":"popularity","type":"pint","indexed":true,"stored":true}'
  add_schema_field '{"name":"inStock","type":"boolean","indexed":true,"stored":true}'
  add_schema_field '{"name":"manufacturedate_dt","type":"pdate","indexed":true,"stored":true}'
  add_schema_field '{"name":"store","type":"location","indexed":true,"stored":true}'

  # Route key text fields into the catch-all _text_ field for better full-text relevance
  curl "${SOLR_BASIC_AUTH}" -s -X POST -H 'Content-Type: application/json' \
    --data-binary '{"add-copy-field":[
      {"source":"name","dest":"_text_"},
      {"source":"manu","dest":"_text_"},
      {"source":"features","dest":"_text_"},
      {"source":"includes","dest":"_text_"}
    ]}' "${schema_url}" >/dev/null || log "WARNING: could not add copy-fields to bootstrap core"

  # Reload so the on-disk conf/ reflects the managed-schema edits before we copy it out.
  curl "${SOLR_BASIC_AUTH}" -sf "${CORE_ADMIN_API}?action=RELOAD&core=${bootstrap}&wt=json" \
    || log "WARNING: failed to reload bootstrap core before copying its conf/ back out"

  local bootstrap_conf
  bootstrap_conf="$(curl "${SOLR_BASIC_AUTH}" -sf "${CORE_ADMIN_API}?action=STATUS&core=${bootstrap}&wt=json" \
    | awk -F'"instanceDir":"' '{print $2}' | awk -F'"' '{print $1}')"
  bootstrap_conf="${bootstrap_conf%/}/conf"

  if [[ -d "$bootstrap_conf" ]]; then
    log "Copying optimized schema from bootstrap core's conf/ back onto shared configset '${CONFIGSET_NAME}' ..."
    cp -r "${bootstrap_conf}/." "${CONFIGSET_DEST_CONF}/" \
      || log "WARNING: failed to copy '${bootstrap_conf}' back to '${CONFIGSET_DEST_CONF}' - shared configset may be stale"
  else
    log "WARNING: could not resolve bootstrap core's instanceDir/conf on disk (${bootstrap_conf}) - shared configset may be stale"
  fi

  log "Removing bootstrap core '${bootstrap}' (shared configset '${CONFIGSET_NAME}' is preserved) ..."
  curl "${SOLR_BASIC_AUTH}" -sf "${CORE_ADMIN_API}?action=UNLOAD&core=${bootstrap}&deleteInstanceDir=true&deleteDataDir=true&wt=json" \
    || log "WARNING: failed to unload bootstrap core '${bootstrap}' - please remove it manually"
}

# ---------------------------------------------------------------------------
# Step 1: make sure the "products" configset exists on disk
# ---------------------------------------------------------------------------
if [[ -d "${CONFIGSET_DEST_CONF}" ]]; then
  log "Configset '${CONFIGSET_NAME}' already exists at ${CONFIGSET_DEST_CONF} — reusing it."
else
  if [[ -n "${BASE_CONFIGSET_DIR}" ]]; then
    [[ -d "${BASE_CONFIGSET_DIR}" ]] || die "BASE_CONFIGSET_DIR '${BASE_CONFIGSET_DIR}' does not exist"
    create_configset_from_base
    if [[ "${OPTIMIZE_SCHEMA}" == "true" ]]; then
      optimize_products_schema
    else
      log "OPTIMIZE_SCHEMA=false — skipping techproducts schema optimization."
    fi
  else
    die "Configset '${CONFIGSET_NAME}' does not exist at ${CONFIGSET_DEST_CONF}, and BASE_CONFIGSET_DIR was not provided. \
Set BASE_CONFIGSET_DIR to an existing configset's conf/ directory (e.g. Solr's bundled server/solr/configsets/_default/conf) \
to derive '${CONFIGSET_NAME}' from it, or pre-populate ${CONFIGSET_DEST_CONF} manually."
  fi
fi

# ---------------------------------------------------------------------------
# Step 2: fetch techproducts.xml if not already present locally
# ---------------------------------------------------------------------------
if [[ ! -f "${TECHPRODUCTS_XML}" ]]; then
  log "Downloading sample dataset techproducts.xml ..."
  curl "${SOLR_BASIC_AUTH}" -sf -o "${TECHPRODUCTS_XML}" "${TECHPRODUCTS_XML_URL}" \
    || die "failed to download techproducts.xml from ${TECHPRODUCTS_XML_URL}"
fi
[[ -s "${TECHPRODUCTS_XML}" ]] || die "techproducts.xml is missing or empty at ${TECHPRODUCTS_XML}"
log "Using dataset: ${TECHPRODUCTS_XML}"

# ---------------------------------------------------------------------------
# Step 3: create cores + index data
# ---------------------------------------------------------------------------
create_core() {
  local name="$1" extra="$2"
  local url="${CORE_ADMIN_API}?action=CREATE&name=${name}&${extra}&wt=json"

  log "Creating core '${name}' with params: ${extra}"
  local resp status body
  resp="$(curl "${SOLR_BASIC_AUTH}" -sf -w '\n%{http_code}' "${url}")" || die "CREATE request failed for ${name}"
  status="$(echo "$resp" | tail -n1)"
  body="$(echo "$resp" | sed '$d')"

  if [[ "$status" != "200" ]]; then
    die "Failed to create core '${name}' (HTTP ${status}): ${body}"
  fi

  if [[ "$extra" == *"async="* ]]; then
    local request_id
    request_id="$(echo "$extra" | awk -F'async=' '{print $2}' | awk -F'&' '{print $1}')"
    wait_for_async "$request_id"
  fi

  log "Core '${name}' created successfully."
}

wait_for_async() {
  local request_id="$1"
  local tries=30
  log "Waiting for async core creation request '${request_id}' to complete ..."
  until curl "${SOLR_BASIC_AUTH}" -sf "${CORE_ADMIN_API}?action=REQUESTSTATUS&requestid=${request_id}&wt=json" \
        | grep -q '"state":"completed"'; do
    tries=$((tries - 1))
    [[ $tries -gt 0 ]] || die "async request '${request_id}' did not complete in time"
    sleep 2
  done
  log "Async request '${request_id}' completed."
}

wait_for_core_active() {
  local name="$1"
  local tries=30
  log "Waiting for '${name}' to become active ..."
  until curl "${SOLR_BASIC_AUTH}" -sf "${SOLR_URL}/solr/${name}/admin/ping?wt=json" \
        | grep -q '"status":"OK"'; do
    tries=$((tries - 1))
    if [[ $tries -le 0 ]]; then
      die "Core '${name}' did not become active in time"
    fi
    sleep 2
  done
  log "Core '${name}' is active."
}

index_techproducts() {
  local name="$1"
  log "Indexing techproducts.xml into '${name}' ..."
  curl "${SOLR_BASIC_AUTH}" -sf -X POST "${SOLR_URL}/solr/${name}/update?commit=true" \
    -H "Content-Type: application/xml" \
    --data-binary @"${TECHPRODUCTS_XML}" \
    || die "Failed to index data into '${name}'"

  local count
  count="$(curl "${SOLR_BASIC_AUTH}" -sf "${SOLR_URL}/solr/${name}/select?q=*:*&rows=0&wt=json" \
    | awk -F'"numFound":' '{print $2}' | awk -F',' '{print $1}')"
  log "Core '${name}' now has ${count:-?} documents."
}

for entry in "${TENANTS[@]}"; do
  name="${entry%%|*}"
  extra="${entry#*|}"

  create_core "$name" "$extra"

  # A transient core created with loadOnStartup=false may still be
  # immediately loadable on first request (Solr lazy-loads it) - ping
  # will trigger that load, so the wait below covers both cases.
  wait_for_core_active "$name"
  index_techproducts "$name"
  echo
done

log "All 10 tenant cores created and populated successfully."