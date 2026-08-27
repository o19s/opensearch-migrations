#!/usr/bin/env python3

import json
import sys
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

FILE = sys.argv[1] if len(sys.argv) > 1 else "test.log"

# Maximum tolerated percentage difference.
# 0.01 means 0.01%.
THRESHOLD_PERCENT = 0.01

# Maximum tolerated absolute difference.
THRESHOLD_VALUE = 0


# ============================================================================
# Helpers
# ============================================================================

def format_value(value):
    """Format aggregation values for display."""

    if value is None:
        return "-"

    if isinstance(value, float):
        return f"{value:,.6f}".rstrip("0").rstrip(".")

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def calculate_variance(source, target):
    """
    Calculate percentage variance as:

        (target - source) / source * 100

    Returns None when source is zero and target is non-zero.
    """

    if source == 0:
        if target == 0:
            return 0.0
        return None

    return ((target - source) / source) * 100.0


def get_status(source, target, variance):
    """Determine comparison status."""

    difference = abs(target - source)

    if difference == 0:
        return "✅ Identical"

    # If source is zero, percentage variance is undefined.
    if variance is None:
        if difference <= THRESHOLD_VALUE:
            return "⚠️ Within Tolerance"
        return "❌ Discrepancy Found"

    if (
            difference <= THRESHOLD_VALUE
            or abs(variance) <= THRESHOLD_PERCENT
    ):
        return "⚠️ Within Tolerance"

    return "❌ Discrepancy Found"


def extract_aggregation_values(aggregations):
    """
    Convert Elasticsearch/OpenSearch aggregations into comparable values.

    Supports:
      - metric aggregations with a 'value'
      - bucket aggregations with 'buckets'
      - keyed buckets
      - nested aggregations
    """

    result = {}

    if not aggregations:
        return result

    def walk(node, path=""):
        if not isinstance(node, dict):
            return

        # Metric aggregation, e.g.
        #
        # "avg_price": {
        #   "value": 123.45
        # }
        if "value" in node and isinstance(node["value"], (int, float)):
            result[path] = node["value"]

        # Bucket aggregation, e.g.
        #
        # "by_date": {
        #   "buckets": [
        #     {
        #       "key_as_string": "2024-08",
        #       "doc_count": 1
        #     }
        #   ]
        # }
        if "buckets" in node and isinstance(node["buckets"], list):
            for bucket in node["buckets"]:
                if not isinstance(bucket, dict):
                    continue

                bucket_key = bucket.get(
                    "key_as_string",
                    bucket.get("key", "?")
                )

                bucket_path = (
                    f"{path}[{bucket_key}]"
                    if path
                    else str(bucket_key)
                )

                if "doc_count" in bucket:
                    result[bucket_path] = bucket["doc_count"]

                # Look for nested aggregations inside the bucket.
                for key, value in bucket.items():
                    if key in {
                        "key",
                        "key_as_string",
                        "doc_count",
                        "from",
                        "to",
                        "from_as_string",
                        "to_as_string",
                    }:
                        continue

                    if isinstance(value, dict):
                        walk(value, f"{bucket_path}.{key}")

        # Continue walking nested aggregation objects.
        for key, value in node.items():
            if key in {
                "buckets",
                "value",
                "doc_count",
                "key",
                "key_as_string",
            }:
                continue

            if isinstance(value, dict):
                child_path = f"{path}.{key}" if path else key
                walk(value, child_path)

    for name, aggregation in aggregations.items():
        walk(aggregation, name)

    return result


# ============================================================================
# Read log
# ============================================================================

path = Path(FILE)

if not path.exists():
    print(f"ERROR: File not found: {FILE}", file=sys.stderr)
    sys.exit(1)

rows = []

with path.open("r", encoding="utf-8") as f:
    for line_number, line in enumerate(f, 1):

        line = line.strip()

        if not line:
            continue

        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            print(
                f"WARNING: Could not parse line {line_number}: {e}",
                file=sys.stderr,
            )
            continue

        # --------------------------------------------------------------------
        # Only process _search requests that contain aggregations
        # --------------------------------------------------------------------

        request_uri = entry.get(
            "sourceRequest", {}
        ).get("Request-URI", "")

        request_payload = entry.get(
            "sourceRequest", {}
        ).get("payload", {})
        request_body = request_payload.get("inlinedJsonBody", {})

        if not request_uri.endswith("/_search"):
            continue

        if not request_body.get("aggs") and not request_body.get("aggregations"):
            continue

        # --------------------------------------------------------------------
        # Source
        # --------------------------------------------------------------------

        source_response = entry.get("sourceResponse", {})
        source_payload = source_response.get("payload", {})
        source_body = source_payload.get("inlinedJsonBody", {})

        source_aggs = source_body.get(
            "aggregations",
            {}
        )

        # --------------------------------------------------------------------
        # Target - LAST response only
        # --------------------------------------------------------------------

        target_responses = entry.get("targetResponses", [])

        if not target_responses:
            continue

        target_response = target_responses[-1]

        target_payload = target_response.get("payload", {})
        target_body = target_payload.get("inlinedJsonBody", {})

        target_aggs = target_body.get(
            "aggregations",
            {}
        )

        # --------------------------------------------------------------------
        # Flatten aggregations
        # --------------------------------------------------------------------

        source_values = extract_aggregation_values(source_aggs)
        target_values = extract_aggregation_values(target_aggs)

        all_keys = sorted(
            set(source_values.keys()) |
            set(target_values.keys())
        )

        for aggregation_key in all_keys:

            source_value = source_values.get(
                aggregation_key,
                0
            )

            target_value = target_values.get(
                aggregation_key,
                0
            )

            variance = calculate_variance(
                source_value,
                target_value
            )

            status = get_status(
                source_value,
                target_value,
                variance
            )

            # Extract aggregation name from:
            #
            # by_date[2024-08]
            #
            # -> by_date
            if "[" in aggregation_key:
                aggregation_name = aggregation_key.split("[", 1)[0]
                bucket = aggregation_key.split("[", 1)[1].rstrip("]")
                metric = f"{aggregation_name}({bucket})"
            else:
                aggregation_name = aggregation_key
                metric = aggregation_name

            rows.append({
                "query": request_uri,
                "metric": metric,
                "source": source_value,
                "target": target_value,
                "variance": variance,
                "status": status,
            })

# ============================================================================
# Calculate column widths
# ============================================================================

headers = [
    "Query ID / Name",
    "Metric / Aggregation",
    "Source Value",
    "Target Value",
    "Variance",
    "Match Confidence",
]

formatted_rows = []

for row in rows:

    if row["variance"] is None:
        variance = "N/A"
    else:
        variance = f"{row['variance']:+.3f}%"

    formatted_rows.append([
        row["query"],
        row["metric"],
        format_value(row["source"]),
        format_value(row["target"]),
        variance,
        row["status"],
    ])


def visible_length(value):
    return len(
        value.replace("**", "")
    )


widths = []

for i, header in enumerate(headers):

    width = visible_length(header)

    for row in formatted_rows:
        width = max(
            width,
            visible_length(row[i])
        )

    widths.append(width)


# ============================================================================
# Print Markdown table
# ============================================================================

def print_row(row):
    print(
        "| "
        + " | ".join(
            f"{value:<{widths[i]}}"
            for i, value in enumerate(row)
        )
        + " |"
    )


print()

print_row(headers)

print(
    "|-"
    + "-|-".join(
        "-" * width
        for width in widths
    )
    + "-|"
)

for row in formatted_rows:
    print_row(row)

print()
