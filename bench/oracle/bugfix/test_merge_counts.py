from __future__ import annotations

from bench.bugfix.metrics import merge_counts


def test_merge_counts_accumulates_values() -> None:
    base = {"passes": 3, "failures": 1}
    patches = [
        {"passes": 1, "skips": 2},
        {"passes": 2, "failures": 1},
    ]
    assert merge_counts(base, patches) == {"passes": 6, "failures": 2, "skips": 2}


def test_merge_counts_does_not_mutate_inputs() -> None:
    base = {"passes": 3}
    patches = [{"passes": 1}, {"passes": 5}]
    merge_counts(base, patches)
    assert base == {"passes": 3}
    assert patches == [{"passes": 1}, {"passes": 5}]
