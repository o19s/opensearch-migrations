"""Pure, side-effect-free comparison primitives.

These are unchanged in behavior from the original comparison_matrix*.py
scripts, just typed and unit-testable in isolation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Sequence


def jaccard_similarity(source_items: Sequence[Any], target_items: Sequence[Any]) -> float:
    """Set-overlap similarity, order-independent. 1.0 for two empty sets."""

    source_set = set(source_items)
    target_set = set(target_items)

    union = source_set | target_set
    if not union:
        return 1.0

    return len(source_set & target_set) / len(union)


def rbo_score(source_items: Sequence[Any], target_items: Sequence[Any], p: float = 0.9) -> float:
    """Rank-Biased Overlap: order-sensitive similarity weighted toward the top.

    p closer to 1.0 spreads weight deeper into the ranking; p closer to 0.0
    concentrates weight at rank 1.
    """

    if not source_items or not target_items:
        return 1.0 if source_items == target_items else 0.0

    k = max(len(source_items), len(target_items))

    source_set: set[Any] = set()
    target_set: set[Any] = set()
    agreement_sum = 0.0

    for depth in range(1, k + 1):
        if depth <= len(source_items):
            source_set.add(source_items[depth - 1])
        if depth <= len(target_items):
            target_set.add(target_items[depth - 1])

        overlap = len(source_set & target_set)
        agreement_sum += (p ** (depth - 1)) * (overlap / depth)

    residual = (p**k) * (len(source_set & target_set) / k)
    return (1 - p) * agreement_sum + residual


@dataclass(slots=True)
class RankShift:
    average: float | None
    maximum: int | None
    signed_average: float | None
    exact_matches: int

    @property
    def has_common_items(self) -> bool:
        return self.average is not None

    def format(self, source_items: Sequence[Any], target_items: Sequence[Any]) -> str:
        if list(source_items) == list(target_items):
            return "0 (exact match)"

        if self.average is None:
            return "no common items"

        missing = len(set(source_items) - set(target_items))
        extra = len(set(target_items) - set(source_items))

        text = f"avg {self.average:.2f}, max {self.maximum}"
        if missing:
            text += f", missing {missing}"
        if extra:
            text += f", extra {extra}"
        return text


def rank_shift(source_items: Sequence[Any], target_items: Sequence[Any]) -> RankShift:
    """Positional drift of items common to both lists."""

    source_rank = {item: rank for rank, item in enumerate(source_items, start=1)}
    target_rank = {item: rank for rank, item in enumerate(target_items, start=1)}

    common = set(source_rank) & set(target_rank)
    if not common:
        return RankShift(average=None, maximum=None, signed_average=None, exact_matches=0)

    shifts = [target_rank[item] - source_rank[item] for item in common]
    absolute = [abs(s) for s in shifts]

    return RankShift(
        average=sum(absolute) / len(absolute),
        maximum=max(absolute),
        signed_average=sum(shifts) / len(shifts),
        exact_matches=sum(1 for s in shifts if s == 0),
    )


def document_fingerprint(source: dict) -> str:
    """Stable content fingerprint for a document's `_source`, order-independent."""

    canonical = json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
