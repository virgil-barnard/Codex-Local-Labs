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

    length = len(values)
    if window <= 0 or window > length:
        raise ValueError("window must be between 1 and the length of values")

    if window == 0:  # defensive; handled above but keeps type-checkers happy
        return []

    averages: List[float] = []
    window_sum = sum(values[:window])
    averages.append(window_sum / window)

    for idx in range(window, length):
        window_sum += values[idx] - values[idx - window]
        averages.append(window_sum / window)

    return averages


def pairwise_differences(values: Iterable[float]) -> List[float]:
    """Compute successive differences between items in *values*.

    The return value should have ``len(values) - 1`` items when at least two
    values are provided. For shorter iterables an empty list is expected.
    """

    iterator = iter(values)
    try:
        previous = next(iterator)
    except StopIteration:
        return []

    differences: List[float] = []
    for current in iterator:
        differences.append(float(current) - float(previous))
        previous = current

    return differences
