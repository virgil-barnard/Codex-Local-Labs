"""Stream helpers for kata exercises."""

from __future__ import annotations

from collections.abc import Iterable
from heapq import merge
from typing import Any, List


def merge_sorted_streams(*streams: Iterable[Any]) -> List[Any]:
    """Merge multiple individually sorted iterables into a single sorted list."""
    if not streams:
        return []

    # ``heapq.merge`` lazily merges any number of already sorted iterables,
    # yielding values in non-decreasing order while preserving duplicates.
    # Materialise the merged iterator into a list so callers receive an eagerly
    # evaluated result that can be reused without exhausting generators.
    return list(merge(*streams))
