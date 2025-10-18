"""Utility functions for text-focused kata exercises."""

from __future__ import annotations


def normalize_whitespace(text: str) -> str:
    """Collapse consecutive whitespace into single spaces and strip the ends.

    The function should treat any Unicode whitespace character as a separator
    and ensure that the returned string never starts or ends with whitespace.
    Multiple whitespace clusters inside the string collapse into a single
    ASCII space (" ").
    """
    # ``str.split`` without arguments treats every Unicode whitespace character
    # as a separator and ignores consecutive runs. Joining the resulting
    # segments with a single ASCII space therefore collapses all whitespace
    # clusters while also trimming leading and trailing characters.
    return " ".join(text.split())
