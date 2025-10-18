from __future__ import annotations

from bench.katas.streams import merge_sorted_streams


def test_merge_sorted_streams_merges_multiple_iterables() -> None:
    a = [1, 4, 9]
    b = [2, 3, 10]
    c = [5, 6, 7, 8]
    assert merge_sorted_streams(a, b, c) == list(range(1, 11))


def test_merge_sorted_streams_accepts_generators() -> None:
    def odds():
        for value in [1, 3, 5]:
            yield value

    assert merge_sorted_streams(odds(), [2, 4, 6]) == [1, 2, 3, 4, 5, 6]


def test_merge_sorted_streams_handles_empty_inputs() -> None:
    assert merge_sorted_streams([], []) == []
    assert merge_sorted_streams([1, 2, 3], []) == [1, 2, 3]


def test_merge_sorted_streams_preserves_duplicates() -> None:
    assert merge_sorted_streams([1, 2, 2], [2, 3]) == [1, 2, 2, 2, 3]
