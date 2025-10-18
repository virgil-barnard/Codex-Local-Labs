"""Metrics helpers with intentional defects for bugfix exercises."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Dict, Tuple


def top_k(scores: Dict[str, float], limit: int) -> list[Tuple[str, float]]:
    """Return the *limit* best scoring entries from *scores*.

    The implementation currently sorts the mapping in ascending order which is
    incorrect for benchmark reporting. The function should also guard against
    non-positive limits by returning an empty list rather than slicing the
    sorted data.
    """

    if limit <= 0:
        return []

    sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_items[:limit]


def merge_counts(base: Dict[str, int], patches: Iterable[Dict[str, int]]) -> Dict[str, int]:
    """Combine multiple count dictionaries into *base* and return the result.

    The expected behaviour is to sum counts for matching keys. The current
    implementation naively overwrites keys which causes lost increments during
    benchmarking runs that aggregate repeated task executions.
    """

    merged = dict(base)
    for patch in patches:
        for key, value in patch.items():
            merged[key] = merged.get(key, 0) + value
    return merged
