#!/usr/bin/env bash

set -euo pipefail

OS_URL="https://localhost:9200"

INDEX="products"
INDEX_FILE_PREFIX=$INDEX

exe() { (curl -fsSk -u 'admin:admin' "$@") }

echo "Create products index"
exe -X PUT "$OS_URL/$INDEX" \
  -H "Content-Type: application/json" \
  --data-binary @sample-data/${INDEX_FILE_PREFIX}_index.json

echo "Populate products index with data"
exe -sSk -X POST "$OS_URL/$INDEX/_bulk" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary @sample-data/${INDEX_FILE_PREFIX}.ndjson
