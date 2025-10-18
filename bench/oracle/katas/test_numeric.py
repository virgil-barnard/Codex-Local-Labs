from __future__ import annotations

import pytest

from bench.katas.numeric import pairwise_differences, rolling_average


def test_rolling_average_basic() -> None:
    result = rolling_average([1, 2, 3, 4, 5], window=3)
    assert result == [2.0, 3.0, 4.0]


@pytest.mark.parametrize("window", [0, -1, 6])
def test_rolling_average_rejects_invalid_window(window: int) -> None:
    with pytest.raises(ValueError):
        rolling_average([1, 2, 3], window)


def test_pairwise_differences_handles_iterables() -> None:
    result = pairwise_differences(range(5))
    assert result == [1, 1, 1, 1]


def test_pairwise_differences_handles_floats() -> None:
    values = [0.0, 0.1, 0.4, 1.5]
    diffs = pairwise_differences(values)
    assert diffs == pytest.approx([0.1, 0.3, 1.1])


def test_pairwise_differences_empty_when_single_value() -> None:
    assert pairwise_differences([42.0]) == []
    assert pairwise_differences([]) == []
