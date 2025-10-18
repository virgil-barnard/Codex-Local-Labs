from __future__ import annotations

from bench.bugfix.metrics import top_k


def test_top_k_returns_descending_scores() -> None:
    scores = {"model-a": 0.42, "model-b": 0.88, "model-c": 0.74}
    assert top_k(scores, 2) == [("model-b", 0.88), ("model-c", 0.74)]


def test_top_k_handles_limit_edge_cases() -> None:
    scores = {"x": 1.0, "y": 2.0}
    assert top_k(scores, 0) == []
    assert top_k(scores, -1) == []


def test_top_k_truncates_but_preserves_order() -> None:
    scores = {"a": 3.0, "b": 4.0, "c": 5.0}
    assert top_k(scores, 10) == [("c", 5.0), ("b", 4.0), ("a", 3.0)]
