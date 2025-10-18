"""Numeric helpers that form the basis for kata-style tasks."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import List


def rolling_average(values: Sequence[float], window: int) -> List[float]:
    """Return the simple moving average for the given sequence.

    The window is the number of consecutive values to include in each
    average. The caller is responsible for providing a positive window that is
    no larger than the input sequence.
    """

    raise NotImplementedError("rolling_average has not been implemented yet")


def pairwise_differences(values: Iterable[float]) -> List[float]:
    """Compute successive differences between items in *values*.

    The return value should have ``len(values) - 1`` items when at least two
    values are provided. For shorter iterables an empty list is expected.
    """

    raise NotImplementedError("pairwise_differences has not been implemented yet")
