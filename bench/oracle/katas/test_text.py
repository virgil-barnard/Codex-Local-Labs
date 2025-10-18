from __future__ import annotations

import pytest

from bench.katas.text import normalize_whitespace


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("hello", "hello"),
        ("  leading and trailing   ", "leading and trailing"),
        ("line1\nline2\tline3", "line1 line2 line3"),
        ("mix\u2003of\tunicode\nspaces", "mix of unicode spaces"),
        ("   multiple\n\n\tseparators   here   ", "multiple separators here"),
    ],
)
def test_normalize_whitespace_collapses_gaps(raw: str, expected: str) -> None:
    assert normalize_whitespace(raw) == expected


def test_normalize_whitespace_handles_all_whitespace() -> None:
    messy = "\n\t spaced\u2009out\u00a0text\t"
    assert normalize_whitespace(messy) == "spaced out text"
