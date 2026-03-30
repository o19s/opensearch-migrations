#!/usr/bin/env bash
# ============================================================================
# Generate and index ~200K e-commerce product documents into Solr.
#
# Usage:
#   bash generate_data.sh [SOLR_URL] [NUM_DOCS]
#   bash generate_data.sh                          # defaults: localhost:38983, 200000
#   bash generate_data.sh http://localhost:8983 50000
# ============================================================================

set -euo pipefail

SOLR_URL="${1:-http://localhost:38983}"
NUM_DOCS="${2:-200000}"
COLLECTION="ecommerce"
BATCH_SIZE=500

echo "=== Generating ${NUM_DOCS} products for ${SOLR_URL}/solr/${COLLECTION} ==="

# --- Data pools for random selection ---
BRANDS=("Samsung" "Apple" "Sony" "LG" "Dell" "HP" "Lenovo" "Asus" "Acer"
        "Microsoft" "Google" "Bose" "JBL" "Canon" "Nikon" "Logitech"
        "Corsair" "Razer" "Anker" "Belkin")

CATEGORIES=(
  "Electronics/Laptops" "Electronics/Phones" "Electronics/Tablets"
  "Electronics/TVs" "Electronics/Audio" "Electronics/Cameras"
  "Accessories/Cases" "Accessories/Chargers" "Accessories/Cables"
  "Computing/Storage" "Computing/Memory" "Computing/Peripherals"
  "Gaming/Consoles" "Gaming/Controllers" "Gaming/Headsets"
  "Home/Smart Home" "Home/Networking" "Home/Printers"
  "Wearables/Watches" "Wearables/Fitness"
)

ADJECTIVES=("Premium" "Ultra" "Pro" "Elite" "Essential" "Advanced" "Compact"
            "Wireless" "Portable" "Smart" "HD" "4K" "Ergonomic" "Rugged"
            "Slim" "Fast" "Quiet" "Eco" "Mini" "Max")

NOUNS=("Laptop" "Phone" "Tablet" "Monitor" "Headphones" "Speaker" "Camera"
       "Charger" "Mouse" "Keyboard" "Router" "SSD" "Hard Drive" "RAM"
       "GPU" "Webcam" "Microphone" "Printer" "Watch" "Tracker"
       "Controller" "Dock" "Hub" "Adapter" "Cable" "Stand" "Case"
       "Battery" "Stylus" "Scanner")

TAGS_POOL=("bestseller" "new-arrival" "sale" "clearance" "refurbished"
           "eco-friendly" "bundle" "limited-edition" "exclusive" "top-rated"
           "staff-pick" "gift-idea" "back-to-school" "prime-day" "holiday")

# US warehouse locations (lat,lon)
LOCATIONS=(
  "40.7128,-74.0060"   # NYC
  "34.0522,-118.2437"  # LA
  "41.8781,-87.6298"   # Chicago
  "29.7604,-95.3698"   # Houston
  "33.4484,-112.0740"  # Phoenix
  "47.6062,-122.3321"  # Seattle
  "25.7617,-80.1918"   # Miami
  "39.7392,-104.9903"  # Denver
  "33.7490,-84.3880"   # Atlanta
  "42.3601,-71.0589"   # Boston
)

pick_random() {
  local -n arr=$1
  echo "${arr[$((RANDOM % ${#arr[@]}))]}"
}

# --- Generate and index in batches via temp file ---
docs_sent=0
batch_file=$(mktemp)
trap "rm -f ${batch_file}" EXIT

send_batch() {
  echo "]" >> "$batch_file"
  curl -sf -X POST "${SOLR_URL}/solr/${COLLECTION}/update?commit=false" \
    -H 'Content-Type: application/json' \
    -d @"${batch_file}" > /dev/null
  : > "$batch_file"
}

for ((i=1; i<=NUM_DOCS; i++)); do
  brand=$(pick_random BRANDS)
  adj=$(pick_random ADJECTIVES)
  noun=$(pick_random NOUNS)
  cat=$(pick_random CATEGORIES)
  loc=$(pick_random LOCATIONS)

  cat_parent="${cat%%/*}"
  cat_child="${cat##*/}"

  name="${brand} ${adj} ${noun} ${i}"
  price=$(( RANDOM % 99000 + 999 ))
  price_dec=$(awk "BEGIN{printf \"%.2f\", $price / 100}")
  sale_pct=$(( RANDOM % 40 ))
  sale_price=$(awk "BEGIN{printf \"%.2f\", $price_dec * (100 - $sale_pct) / 100}")
  popularity=$(( RANDOM % 1000 ))
  rating=$(awk "BEGIN{printf \"%.1f\", ($RANDOM % 40 + 10) / 10.0}")
  review_count=$(( RANDOM % 5000 ))
  weight=$(( RANDOM % 10000 + 50 ))
  in_stock=$(( RANDOM % 10 > 1 ? 1 : 0 ))

  days_ago=$(( RANDOM % 730 ))
  created=$(date -u -d "-${days_ago} days" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
            echo "2025-06-15T12:00:00Z")
  updated=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "2026-03-30T12:00:00Z")

  num_tags=$(( RANDOM % 3 + 1 ))
  tags_json=""
  for ((t=0; t<num_tags; t++)); do
    tag=$(pick_random TAGS_POOL)
    [ -z "$tags_json" ] && tags_json="\"${tag}\"" || tags_json="${tags_json},\"${tag}\""
  done

  [ "$in_stock" -eq 0 ] && in_stock_str="false" || in_stock_str="true"

  doc="{\"id\":\"prod-${i}\",\"name\":\"${name}\",\"description\":\"The ${brand} ${adj} ${noun} delivers exceptional performance and value.\",\"brand\":\"${brand}\",\"category\":[\"${cat_parent}\",\"${cat_child}\"],\"price\":${price_dec},\"sale_price\":${sale_price},\"in_stock\":${in_stock_str},\"sku\":\"SKU-${brand:0:3}-${i}\",\"popularity\":${popularity},\"rating\":${rating},\"review_count\":${review_count},\"weight_grams\":${weight},\"created_at\":\"${created}\",\"updated_at\":\"${updated}\",\"warehouse_location\":\"${loc}\",\"tags\":[${tags_json}]}"

  batch_pos=$(( (docs_sent) % BATCH_SIZE ))
  if [ $batch_pos -eq 0 ]; then
    # Send previous batch if file has content
    [ -s "$batch_file" ] && send_batch
    echo "[" > "$batch_file"
    echo "$doc" >> "$batch_file"
  else
    echo ",$doc" >> "$batch_file"
  fi

  docs_sent=$((docs_sent + 1))

  if [ $(( docs_sent % 10000 )) -eq 0 ]; then
    echo "  ... indexed ${docs_sent}/${NUM_DOCS} documents"
  fi
done

# Send final batch
[ -s "$batch_file" ] && send_batch

# Hard commit
echo "  ... committing..."
curl -sf -X POST "${SOLR_URL}/solr/${COLLECTION}/update?commit=true" \
  -H 'Content-Type: application/json' \
  -d '[]' > /dev/null

echo "=== Done: ${docs_sent} documents indexed ==="
echo "  Verify: curl '${SOLR_URL}/solr/${COLLECTION}/select?q=*:*&rows=0'"
