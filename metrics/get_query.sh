#!/usr/bin/env bash

set -euo pipefail

FILE="${1:-output.log}"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Maximum tolerated percentage difference.
# 0.01 means 0.01%
THRESHOLD_PERCENT="${THRESHOLD_PERCENT:-0.01}"

# Maximum tolerated absolute document difference.
THRESHOLD_COUNT="${THRESHOLD_COUNT:-100}"

# ---------------------------------------------------------------------------
# Collect and format data
# ---------------------------------------------------------------------------

jq -r '
  select(.sourceRequest["Request-URI"] == "/_cat/indices?format=json")
  |
  (
    .sourceResponse.payload.inlinedJsonBody
    | map({
        key: .index,
        value: (."docs.count" | tonumber)
      })
    | from_entries
  ) as $source
  |
  (
    .targetResponses[-1].payload.inlinedJsonBody
    | map({
        key: .index,
        value: (."docs.count" | tonumber)
      })
    | from_entries
  ) as $target
  |
  (($source | keys) + ($target | keys) | unique)[] as $index
  |
  [
    $index,
    ($source[$index] // 0),
    ($target[$index] // 0)
  ]
  | @tsv
' "$FILE" |
python3 -c '
import sys

threshold_percent = float("'"$THRESHOLD_PERCENT"'")
threshold_count = int("'"$THRESHOLD_COUNT"'")

rows = []

total_source = 0
total_target = 0

for line in sys.stdin:
    index, source, target = line.rstrip("\n").split("\t")

    source = int(source)
    target = int(target)

    delta = target - source

    if source == 0:
        delta_percent = 0.0 if target == 0 else 100.0
    else:
        delta_percent = (delta / source) * 100.0

    abs_delta = abs(delta)
    abs_percent = abs(delta_percent)

    if delta == 0:
        status = "✅ Match"
    elif (
        abs_delta <= threshold_count
        and abs_percent <= threshold_percent
    ):
        status = "⚠️ Minor Lag (In-Sync Tolerance)"
    else:
        status = f"❌ Action Required: Review {abs_delta:,} records"

    rows.append((
        index,
        source,
        target,
        delta,
        delta_percent,
        status
    ))

    total_source += source
    total_target += target

# ---------------------------------------------------------------------------
# Total
# ---------------------------------------------------------------------------

total_delta = total_target - total_source

if total_source == 0:
    total_percent = 0.0 if total_target == 0 else 100.0
else:
    total_percent = (total_delta / total_source) * 100.0

if total_delta == 0:
    total_status = "✅ Match"
elif (
    abs(total_delta) <= threshold_count
    and abs(total_percent) <= threshold_percent
):
    total_status = "⚠️ Minor Lag (In-Sync Tolerance)"
else:
    total_status = f"❌ Action Required: Review {abs(total_delta):,} records"

# ---------------------------------------------------------------------------
# Determine column widths
# ---------------------------------------------------------------------------

headers = [
    "Index",
    "Source Count",
    "Target Count",
    "Delta Count",
    "Delta (%)",
    "Status / Confidence"
]

formatted_rows = []

for index, source, target, delta, percent, status in rows:
    formatted_rows.append([
        f"**{index}**",
        f"{source:,}",
        f"{target:,}",
        f"{delta:,}",
        f"{percent:.3f}%",
        status
    ])

formatted_rows.append([
    "**Total**",
    f"**{total_source:,}**",
    f"**{total_target:,}**",
    f"**{total_delta:,}**",
    f"**{total_percent:.3f}%**",
    f"**{total_status}**"
])

# Remove Markdown formatting when calculating widths.
def visible_length(value):
    return len(
        value
        .replace("**", "")
    )

widths = []

for i, header in enumerate(headers):
    width = visible_length(header)

    for row in formatted_rows:
        width = max(width, visible_length(row[i]))

    widths.append(width)

# ---------------------------------------------------------------------------
# Print table
# ---------------------------------------------------------------------------

def print_row(row):
    print(
        "| "
        + " | ".join(
            f"{value:<{widths[i]}}"
            for i, value in enumerate(row)
        )
        + " |"
    )

print_row(headers)

print(
    "|-"
    + "-|-".join("-" * width for width in widths)
    + "-|"
)

for row in formatted_rows:
    print_row(row)
'