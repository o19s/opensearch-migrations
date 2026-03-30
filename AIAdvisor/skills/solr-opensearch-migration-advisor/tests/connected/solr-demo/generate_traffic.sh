#!/usr/bin/env bash
# ============================================================================
# Generate realistic search traffic against the Solr demo for ~15 minutes.
#
# Produces a mix of query types across multiple handlers to create
# interesting MBeans stats for migration advisor inspection:
#   - /product-search (eDisMax, 60% of traffic)
#   - /select (standard, 20%)
#   - /suggest (autocomplete, 10%)
#   - /nearby (geo-spatial, 5%)
#   - /admin/ping (health checks, 5%)
#
# Traffic follows a rough zipf distribution: a few popular queries
# repeat often while most queries are unique.
#
# Usage:
#   bash generate_traffic.sh [SOLR_URL] [DURATION_MINUTES]
#   bash generate_traffic.sh                            # defaults: localhost:38983, 15
#   bash generate_traffic.sh http://localhost:8983 5     # 5 minutes
# ============================================================================

set -euo pipefail

SOLR_URL="${1:-http://localhost:38983}"
DURATION_MINUTES="${2:-15}"
COLLECTION="ecommerce"
END_TIME=$(( $(date +%s) + DURATION_MINUTES * 60 ))

echo "=== Generating traffic for ${DURATION_MINUTES} minutes ==="
echo "    Target: ${SOLR_URL}/solr/${COLLECTION}"
echo "    Stop time: $(date -d @${END_TIME} 2>/dev/null || date -r ${END_TIME} 2>/dev/null || echo "${END_TIME}")"
echo ""

# --- Query pools ---

# Popular queries (repeat frequently — zipf head)
POPULAR_QUERIES=(
  "laptop" "phone" "headphones" "wireless speaker" "4k monitor"
  "gaming mouse" "usb charger" "samsung" "apple" "bluetooth"
)

# Long-tail queries (used once or twice)
LONGTAIL_QUERIES=(
  "ergonomic keyboard mechanical" "portable ssd 1tb rugged"
  "noise cancelling headphones under 200" "4k webcam for streaming"
  "wifi 6 mesh router whole home" "dslr camera beginner"
  "smart watch fitness tracker heart rate" "usb-c hub thunderbolt"
  "laser printer color duplex" "gaming controller wireless pc"
  "studio microphone condenser usb" "portable battery 20000mah"
  "monitor arm dual mount" "cable management desk kit"
  "smart home hub zigbee" "outdoor security camera wireless"
  "mechanical keyboard cherry mx" "ultrawide monitor 34 inch"
  "e-reader backlight waterproof" "drone camera 4k gps"
)

# Filter queries for faceted search
FILTER_BRANDS=("Samsung" "Apple" "Sony" "Dell" "Bose" "Logitech")
FILTER_CATEGORIES=("Laptops" "Phones" "Audio" "Cameras" "Peripherals")

# Autocomplete prefixes
SUGGEST_PREFIXES=("lap" "pho" "head" "wire" "sam" "app" "mon" "key"
                  "gam" "cha" "spe" "cam" "tab" "rou" "pri")

# Geo-spatial locations
GEO_POINTS=(
  "40.7,-74.0"   "34.0,-118.2"  "41.8,-87.6"
  "29.7,-95.3"   "47.6,-122.3"  "25.7,-80.1"
)

pick_random() {
  local -n arr=$1
  echo "${arr[$((RANDOM % ${#arr[@]}))]}"
}

encode_query() {
  # Minimal URL encoding for spaces and special chars
  echo "$1" | sed 's/ /%20/g; s/&/%26/g'
}

requests=0
errors=0

send_query() {
  local url="$1"
  if curl -sf -o /dev/null --max-time 5 "$url"; then
    requests=$((requests + 1))
  else
    errors=$((errors + 1))
  fi
}

echo "Starting traffic generation..."

while [ $(date +%s) -lt $END_TIME ]; do
  # Weighted random: pick a handler type
  roll=$(( RANDOM % 100 ))

  if [ $roll -lt 60 ]; then
    # 60%: eDisMax product search
    if [ $(( RANDOM % 3 )) -eq 0 ]; then
      q=$(pick_random LONGTAIL_QUERIES)
    else
      q=$(pick_random POPULAR_QUERIES)
    fi
    encoded_q=$(encode_query "$q")
    url="${SOLR_URL}/solr/${COLLECTION}/product-search?q=${encoded_q}"

    # Sometimes add filters
    if [ $(( RANDOM % 3 )) -eq 0 ]; then
      brand=$(pick_random FILTER_BRANDS)
      url="${url}&fq=brand:${brand}"
    fi
    if [ $(( RANDOM % 4 )) -eq 0 ]; then
      min_price=$(( RANDOM % 50 * 10 ))
      max_price=$(( min_price + 100 + RANDOM % 500 ))
      url="${url}&fq=price:[${min_price}%20TO%20${max_price}]"
    fi

    send_query "$url"

  elif [ $roll -lt 80 ]; then
    # 20%: standard /select
    q=$(pick_random POPULAR_QUERIES)
    encoded_q=$(encode_query "$q")
    sort_options=("price asc" "price desc" "popularity desc" "rating desc" "")
    sort=$(pick_random sort_options)
    url="${SOLR_URL}/solr/${COLLECTION}/select?q=${encoded_q}&rows=10"
    if [ -n "$sort" ]; then
      encoded_sort=$(encode_query "$sort")
      url="${url}&sort=${encoded_sort}"
    fi
    send_query "$url"

  elif [ $roll -lt 90 ]; then
    # 10%: autocomplete /suggest
    prefix=$(pick_random SUGGEST_PREFIXES)
    send_query "${SOLR_URL}/solr/${COLLECTION}/suggest?q=${prefix}"

  elif [ $roll -lt 95 ]; then
    # 5%: geo-spatial /nearby
    pt=$(pick_random GEO_POINTS)
    dist=$(( RANDOM % 200 + 10 ))
    send_query "${SOLR_URL}/solr/${COLLECTION}/nearby?q=*:*&fq={!geofilt}&pt=${pt}&d=${dist}"

  else
    # 5%: health check ping
    send_query "${SOLR_URL}/solr/${COLLECTION}/admin/ping"
  fi

  # Vary request rate: 5-20 requests/sec with occasional bursts
  if [ $(( RANDOM % 20 )) -eq 0 ]; then
    # Burst: no sleep
    :
  else
    # Normal: small random delay (50-200ms)
    sleep 0.$(( RANDOM % 150 + 50 ))
  fi

  # Progress every 60 seconds
  if [ $(( requests % 500 )) -eq 0 ] && [ $requests -gt 0 ]; then
    elapsed=$(( $(date +%s) - (END_TIME - DURATION_MINUTES * 60) ))
    remaining=$(( END_TIME - $(date +%s) ))
    echo "  ... ${requests} requests sent (${errors} errors), ${remaining}s remaining"
  fi
done

echo ""
echo "=== Traffic generation complete ==="
echo "  Total requests: ${requests}"
echo "  Errors: ${errors}"
echo "  Duration: ${DURATION_MINUTES} minutes"
echo ""
echo "  Inspect stats:"
echo "    curl '${SOLR_URL}/solr/${COLLECTION}/admin/mbeans?stats=true&cat=QUERYHANDLER&wt=json' | jq '.\"solr-mbeans\"'"
