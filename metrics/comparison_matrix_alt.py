#!/usr/bin/env python3

import hashlib
import json
import sys
from pathlib import Path


# ============================================================================
# Configuration
# ============================================================================

MAX_QUERY_LENGTH = 40
CONNECTION_ID_LENGTH = 12

def shorten(value, max_length=MAX_QUERY_LENGTH):
    """Shorten a string while keeping it readable."""

    value = str(value)

    if len(value) <= max_length:
        return value

    return value[:max_length - 3] + "..."


def short_connection_id(value):
    """Shorten connection ID for display."""

    if not value:
        return "-"

    return str(value)[:CONNECTION_ID_LENGTH]

FILE = sys.argv[1] if len(sys.argv) > 1 else "output.log"

RBO_P = 0.9

# Ranking tolerance
MAX_AVG_RANK_SHIFT = 1.0

# Content comparison
# Exact canonical JSON comparison is used.
# SHA-256 is only used as a compact representation.


# ============================================================================
# Canonical document fingerprint
# ============================================================================

def document_fingerprint(source):
    """
    Generate a stable fingerprint for a document's _source.

    sort_keys=True ensures that JSON field ordering does not matter.

    Example:

        {"a": 1, "b": 2}

    and

        {"b": 2, "a": 1}

    produce the same fingerprint.
    """

    canonical = json.dumps(
        source,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ============================================================================
# Jaccard similarity
# ============================================================================

def jaccard_similarity(source_items, target_items):

    source_set = set(source_items)
    target_set = set(target_items)

    union = source_set | target_set

    if not union:
        return 1.0

    return len(
        source_set & target_set
    ) / len(union)


# ============================================================================
# RBO
# ============================================================================

def rbo_score(source_items, target_items, p=0.9):

    if not source_items or not target_items:
        return (
            1.0
            if source_items == target_items
            else 0.0
        )

    k = max(
        len(source_items),
        len(target_items),
    )

    source_set = set()
    target_set = set()

    agreement_sum = 0.0

    for depth in range(1, k + 1):

        if depth <= len(source_items):
            source_set.add(
                source_items[depth - 1]
            )

        if depth <= len(target_items):
            target_set.add(
                target_items[depth - 1]
            )

        overlap = len(
            source_set & target_set
        )

        agreement = overlap / depth

        agreement_sum += (
                                 p ** (depth - 1)
                         ) * agreement

    score = (
            (1 - p) * agreement_sum
            + (p ** k)
            * (
                    len(source_set & target_set)
                    / k
            )
    )

    return score


# ============================================================================
# Rank shift
# ============================================================================

def calculate_rank_shift(
        source_items,
        target_items,
):

    source_rank = {
        item: rank
        for rank, item
        in enumerate(source_items, start=1)
    }

    target_rank = {
        item: rank
        for rank, item
        in enumerate(target_items, start=1)
    }

    common = (
            set(source_rank)
            & set(target_rank)
    )

    if not common:

        return {
            "average": None,
            "maximum": None,
            "signed_average": None,
            "exact": 0,
        }

    shifts = []

    for item in common:

        shift = (
                target_rank[item]
                - source_rank[item]
        )

        shifts.append(shift)

    absolute = [
        abs(value)
        for value in shifts
    ]

    return {
        "average": sum(absolute) / len(absolute),
        "maximum": max(absolute),
        "signed_average": sum(shifts) / len(shifts),
        "exact": sum(
            1
            for value in shifts
            if value == 0
        ),
    }


# ============================================================================
# Query description
# ============================================================================

def describe_query(entry):

    request = entry.get(
        "sourceRequest",
        {}
    )

    request_uri = request.get(
        "Request-URI",
        ""
    )

    body = (
        request
        .get("payload", {})
        .get("inlinedJsonBody", {})
    )

    query = body.get(
        "query",
        {}
    )

    if not query:
        return request_uri

    if "term" in query:

        terms = query["term"]

        if isinstance(terms, dict):

            return " AND ".join(
                f"{field}={value}"
                for field, value
                in terms.items()
            )

    if "match" in query:

        matches = query["match"]

        if isinstance(matches, dict):

            return " AND ".join(
                f"{field}={value}"
                for field, value
                in matches.items()
            )

    return json.dumps(
        query,
        separators=(",", ":"),
    )


# ============================================================================
# Classification
# ============================================================================

def classify(
        source_ids,
        target_ids,
        source_fingerprints,
        target_fingerprints,
        id_jaccard,
        content_jaccard,
        rbo,
        rank_info,
        source_total,
        target_total,
):

    # ------------------------------------------------------------
    # Exact everything
    # ------------------------------------------------------------

    if (
            source_ids == target_ids
            and source_fingerprints == target_fingerprints
    ):
        return "✅ Identical"


    # ------------------------------------------------------------
    # Content is identical but IDs differ
    # ------------------------------------------------------------

    if (
            content_jaccard == 1.0
            and id_jaccard < 1.0
    ):

        if rbo >= 0.999:

            return "⚠️ ID Difference"

        return "⚠️ ID Difference + Ranking Shift"


    # ------------------------------------------------------------
    # Same content, different order
    # ------------------------------------------------------------

    if (
            content_jaccard == 1.0
            and rbo < 0.999
    ):

        return "⚠️ Ranking Shift"


    # ------------------------------------------------------------
    # Some content matches
    # ------------------------------------------------------------

    if content_jaccard >= 0.90:

        return "⚠️ Minor Content Difference"


    # ------------------------------------------------------------
    # Different hit counts
    # ------------------------------------------------------------

    if source_total != target_total:

        return "❌ Hit Count Discrepancy"


    # ------------------------------------------------------------
    # Actual content discrepancy
    # ------------------------------------------------------------

    return "❌ Content Discrepancy"


# ============================================================================
# Rank drift formatting
# ============================================================================

def format_rank_drift(
        rank_info,
        source_items,
        target_items,
):

    if source_items == target_items:

        return "0 (Exact Rank Match)"

    if rank_info["average"] is None:

        return "No common documents"

    average = rank_info["average"]
    maximum = rank_info["maximum"]

    missing = len(
        set(source_items)
        - set(target_items)
    )

    extra = len(
        set(target_items)
        - set(source_items)
    )

    result = (
        f"Avg {average:.2f}"
        f" positions, max {maximum}"
    )

    if missing:

        result += (
            f", missing {missing}"
        )

    if extra:

        result += (
            f", extra {extra}"
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
        encoding="utf-8",
) as f:

    for line_number, line in enumerate(
            f,
            start=1,
    ):

        line = line.strip()

        if not line:
            continue

        try:

            entry = json.loads(line)

        except json.JSONDecodeError as error:

            print(
                f"WARNING: Could not parse "
                f"line {line_number}: {error}",
                file=sys.stderr,
            )

            continue


        # ================================================================
        # Source request
        # ================================================================

        request = entry.get(
            "sourceRequest",
            {}
        )

        request_uri = request.get(
            "Request-URI",
            ""
        )

        if not request_uri.endswith(
                "/_search"
        ):
            continue


        body = (
            request
            .get("payload", {})
            .get("inlinedJsonBody", {})
        )

        if "query" not in body:
            continue


        top_n = body.get(
            "size",
            10
        )


        # ================================================================
        # Source response
        # ================================================================

        source_body = (
            entry
            .get("sourceResponse", {})
            .get("payload", {})
            .get("inlinedJsonBody", {})
        )

        source_hits_container = source_body.get(
            "hits",
            {}
        )

        source_hits = source_hits_container.get(
            "hits",
            []
        )

        source_total = (
            source_hits_container
            .get("total", {})
            .get("value", len(source_hits))
        )


        # ================================================================
        # Target - LAST response
        # ================================================================

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

        target_hits_container = target_body.get(
            "hits",
            {}
        )

        target_hits = target_hits_container.get(
            "hits",
            []
        )

        target_total = (
            target_hits_container
            .get("total", {})
            .get("value", len(target_hits))
        )


        # ================================================================
        # IDs
        # ================================================================

        source_ids = [
            hit["_id"]
            for hit in source_hits
            if "_id" in hit
        ]

        target_ids = [
            hit["_id"]
            for hit in target_hits
            if "_id" in hit
        ]


        # ================================================================
        # Content fingerprints
        # ================================================================

        source_fingerprints = [
            document_fingerprint(
                hit.get("_source", {})
            )
            for hit in source_hits
        ]

        target_fingerprints = [
            document_fingerprint(
                hit.get("_source", {})
            )
            for hit in target_hits
        ]


        # ================================================================
        # Comparisons
        # ================================================================

        id_jaccard = jaccard_similarity(
            source_ids,
            target_ids,
        )

        content_jaccard = jaccard_similarity(
            source_fingerprints,
            target_fingerprints,
        )

        rbo = rbo_score(
            source_fingerprints,
            target_fingerprints,
            RBO_P,
        )

        rank_info = calculate_rank_shift(
            source_fingerprints,
            target_fingerprints,
        )

        status = classify(
            source_ids,
            target_ids,
            source_fingerprints,
            target_fingerprints,
            id_jaccard,
            content_jaccard,
            rbo,
            rank_info,
            source_total,
            target_total,
        )


        results.append({
            "connection_id": short_connection_id(
                entry.get("connectionId", "")
            ),
            "query": describe_query(entry),
            "top_n": top_n,
            "source_total": source_total,
            "target_total": target_total,
            "id_jaccard": id_jaccard,
            "content_jaccard": content_jaccard,
            "rbo": rbo,
            "rank_drift": format_rank_drift(
                rank_info,
                source_fingerprints,
                target_fingerprints,
            ),
            "status": status,
        })


# ============================================================================
# Table
# ============================================================================

headers = [
    "Connection ID",
    "Search Query",
    "Top-N",
    "Source Hits",
    "Target Hits",
    "ID Jaccard",
    "Content Jaccard",
    "RBO (p=0.9)",
    "Rank Drift",
    "Status",
]


rows = []

for result in results:

    rows.append([
        result["connection_id"],
        shorten(result["query"]),
        f"Top {result['top_n']}",
        f"{result['source_total']:,}",
        f"{result['target_total']:,}",
        f"{result['id_jaccard']:.2f}",
        f"{result['content_jaccard']:.2f}",
        f"{result['rbo']:.2f}",
        result["rank_drift"],
        result["status"],
    ])


# ============================================================================
# Markdown formatting
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

    for row in rows:

        width = max(
            width,
            visible_length(row[i])
        )

    widths.append(width)


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

for row in rows:

    print_row(row)

print()