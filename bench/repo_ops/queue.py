"""Helpers for manipulating the Human Feedback Interface queue."""

from __future__ import annotations

from typing import Dict, List, Optional

QueueEntry = Dict[str, object]


def next_pending(queue: List[QueueEntry]) -> Optional[QueueEntry]:
    """Return the pending request with the oldest ``created_at`` timestamp."""

    for entry in queue:
        if entry.get("status") != "completed":
            return entry
    return None


def record_completion(queue: List[QueueEntry], request_id: str, run_dir: str) -> bool:
    """Mark the given request as completed and attach its run directory."""

    for entry in queue:
        if entry.get("id") == request_id:
            entry = dict(entry)
            entry["status"] = "completed"
            entry["run_dir"] = run_dir
            return True
    return False
