#!/usr/bin/env python3

import json
import sys
from pathlib import Path


# ============================================================================
# Configuration
# ============================================================================

FILE = sys.argv[1] if len(sys.argv) > 1 else "tuple.log"

# RBO persistence parameter.
# p=0.9 means higher-ranked results receive significantly more weight.
RBO_P = 0.9

# Classification thresholds.
JACCARD_IDENTICAL = 1.0
RBO_IDENTICAL = 0.999

JACCARD_ACCEPTABLE = 0.90
RBO_ACCEPTABLE = 0.90

# Maximum average absolute rank shift considered acceptable.
MAX_AVG_RANK_SHIFT = 1.0


# ============================================================================
# RBO
# ============================================================================

def rbo_score(source_ids, target_ids, p=0.9):
    """
    Calculate finite RBO for two ranked lists.

    RBO gives more importance to the top of the ranking.

    Identical lists return 1.0.
    Completely different lists approach 0.0.
    """

    if not source_ids or not target_ids:
        return 1.0 if source_ids == target_ids else 0.0

    k = max(len(source_ids), len(target_ids))

    source_set = set()
    target_set = set()

    agreement_sum = 0.0

    for depth in range(1, k + 1):

        if depth <= len(source_ids):
            source_set.add(source_ids[depth - 1])

        if depth <= len(target_ids):
            target_set.add(target_ids[depth - 1])

        overlap = len(source_set & target_set)

        # Agreement at this depth.
        agreement = overlap / depth

        agreement_sum += (
                (p ** (depth - 1)) * agreement
        )

    # Finite RBO with residual term.
    score = (
            (1 - p) * agreement_sum
            + (p ** k) * (
                    len(source_set & target_set) / k
            )
    )

    return score


# ============================================================================
# Jaccard
# ============================================================================

def jaccard_similarity(source_ids, target_ids):

    source_set = set(source_ids)
    target_set = set(target_ids)

    union = source_set | target_set

    if not union:
        return 1.0

    return len(source_set & target_set) / len(union)


# ============================================================================
# Rank shift
# ============================================================================

def rank_shift(source_ids, target_ids):

    source_rank = {
        doc_id: rank
        for rank, doc_id in enumerate(source_ids, start=1)
    }

    target_rank = {
        doc_id: rank
        for rank, doc_id in enumerate(target_ids, start=1)
    }

    common_ids = (
            set(source_rank.keys())
            & set(target_rank.keys())
    )

    if not common_ids:
        return {
            "average": None,
            "maximum": None,
            "signed_average": None,
            "exact_matches": 0,
        }

    shifts = []

    for doc_id in common_ids:
        source_position = source_rank[doc_id]
        target_position = target_rank[doc_id]

        shifts.append(
            target_position - source_position
        )

    absolute_shifts = [
        abs(shift)
        for shift in shifts
    ]

    return {
        "average": sum(absolute_shifts) / len(absolute_shifts),
        "maximum": max(absolute_shifts),
        "signed_average": sum(shifts) / len(shifts),
        "exact_matches": sum(
            1 for shift in shifts
            if shift == 0
        ),
    }


# ============================================================================
# Classification
# ============================================================================

def classify(
        source_ids,
        target_ids,
        jaccard,
        rbo,
        rank_info,
):

    if source_ids == target_ids:
        return "✅ Identical Ranking"

    average_shift = rank_info["average"]

    if (
            jaccard >= JACCARD_ACCEPTABLE
            and rbo >= RBO_ACCEPTABLE
            and average_shift is not None
            and average_shift <= MAX_AVG_RANK_SHIFT
    ):
        return "⚠️ Acceptable Shift"

    return "❌ Ranking Regression"


# ============================================================================
# Query description
# ============================================================================

def describe_query(entry):

    request = entry.get("sourceRequest", {})

    uri = request.get("Request-URI", "")

    payload = (
        request
        .get("payload", {})
        .get("inlinedJsonBody", {})
    )

    query = payload.get(
        "query",
        {}
    )

    if not query:
        return uri

    # Try to produce a readable representation.
    #
    # Example:
    #
    # {"term": {"vendor_id": "2"}}
    #
    # becomes:
    #
    # vendor_id = 2
    #

    if "term" in query:

        terms = query["term"]

        if isinstance(terms, dict):

            parts = []

            for field, value in terms.items():
                parts.append(
                    f"{field}={value}"
                )

            return " AND ".join(parts)

    if "match" in query:

        matches = query["match"]

        if isinstance(matches, dict):

            parts = []

            for field, value in matches.items():
                parts.append(
                    f"{field}={value}"
                )

            return " AND ".join(parts)

    if "bool" in query:
        return "bool query"

    return json.dumps(
        query,
        separators=(",", ":")
    )


# ============================================================================
# Formatting
# ============================================================================

def format_percentage(value):

    return f"{value * 100:.2f}%"


def format_rank_shift(
        source_ids,
        target_ids,
        rank_info,
):

    if source_ids == target_ids:
        return "0 (Exact Rank Match)"

    common = (
        len(
            set(source_ids)
            & set(target_ids)
        )
    )

    missing = len(
        set(source_ids)
        - set(target_ids)
    )

    extra = len(
        set(target_ids)
        - set(source_ids)
    )

    average = rank_info["average"]
    maximum = rank_info["maximum"]

    if average is None:
        return (
            f"No common documents "
            f"(Missing {missing}, Extra {extra})"
        )

    if (
            average == 0
            and missing == 0
            and extra == 0
    ):
        return "0 (Exact Rank Match)"

    result = (
        f"Avg {average:.2f} positions"
    )

    if maximum is not None:
        result += (
            f", max {maximum}"
        )

    if missing or extra:
        result += (
            f" (Missing {missing}, Extra {extra})"
        )

    return result


# ============================================================================
# Read input
# ============================================================================

path = Path(FILE)

if not path.exists():
    print(
        f"ERROR: File not found: {FILE}",
        file=sys.stderr,
    )
    sys.exit(1)


results = []


with path.open(
        "r",
        encoding="utf-8"
) as f:

    for line_number, line in enumerate(
            f,
            start=1
    ):

        line = line.strip()

        if not line:
            continue

        try:
            entry = json.loads(line)

        except json.JSONDecodeError as e:

            print(
                f"WARNING: Could not parse line "
                f"{line_number}: {e}",
                file=sys.stderr,
            )

            continue

        # --------------------------------------------------------------------
        # Source request
        # --------------------------------------------------------------------

        request = entry.get(
            "sourceRequest",
            {}
        )

        request_uri = request.get(
            "Request-URI",
            ""
        )

        # Only process _search requests.
        if not request_uri.endswith(
                "/_search"
        ):
            continue

        request_body = (
            request
            .get("payload", {})
            .get("inlinedJsonBody", {})
        )

        # We only care about actual searches.
        if "query" not in request_body:
            continue

        top_n = request_body.get(
            "size",
            10
        )

        # --------------------------------------------------------------------
        # Source hits
        # --------------------------------------------------------------------

        source_body = (
            entry
            .get("sourceResponse", {})
            .get("payload", {})
            .get("inlinedJsonBody", {})
        )

        source_hits = (
            source_body
            .get("hits", {})
            .get("hits", [])
        )

        source_ids = [
            hit["_id"]
            for hit in source_hits
            if "_id" in hit
        ]

        # --------------------------------------------------------------------
        # Target - LAST response
        # --------------------------------------------------------------------

        target_responses = entry.get(
            "targetResponses",
            []
        )

        if not target_responses:
            continue

        target_body = (
            target_responses[-1]
            .get("payload", {})
            .get("inlinedJsonBody", {})
        )

        target_hits = (
            target_body
            .get("hits", {})
            .get("hits", [])
        )

        target_ids = [
            hit["_id"]
            for hit in target_hits
            if "_id" in hit
        ]

        # --------------------------------------------------------------------
        # Comparisons
        # --------------------------------------------------------------------

        jaccard = jaccard_similarity(
            source_ids,
            target_ids,
        )

        rbo = rbo_score(
            source_ids,
            target_ids,
            RBO_P,
        )

        rank_info = rank_shift(
            source_ids,
            target_ids,
        )

        status = classify(
            source_ids,
            target_ids,
            jaccard,
            rbo,
            rank_info,
        )

        results.append({
            "query": describe_query(entry),
            "top_n": top_n,
            "jaccard": jaccard,
            "rbo": rbo,
            "rank_shift": format_rank_shift(
                source_ids,
                target_ids,
                rank_info,
            ),
            "status": status,
        })


# ============================================================================
# Build table
# ============================================================================

headers = [
    "Search Query",
    "Top-N Depth",
    "Jaccard Similarity",
    "RBO Score (p=0.9)",
    "Rank Shift / Drift Behavior",
    "Match Confidence",
]


table_rows = []

for result in results:

    overlap = (
        f"{result['jaccard']:.2f}"
        f" ({result['jaccard'] * 100:.0f}% overlap)"
    )

    table_rows.append([
        f"**{result['query']}**",
        f"Top {result['top_n']}",
        overlap,
        f"{result['rbo']:.2f}",
        result["rank_shift"],
        result["status"],
    ])


# ============================================================================
# Calculate widths
# ============================================================================

def visible_length(value):

    return len(
        value.replace(
            "**",
            ""
        )
    )


widths = []

for i, header in enumerate(headers):

    width = visible_length(header)

    for row in table_rows:

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

for row in table_rows:
    print_row(row)

print()
