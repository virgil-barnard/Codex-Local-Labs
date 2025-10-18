from __future__ import annotations

from datetime import datetime

from bench.repo_ops.queue import next_pending, record_completion


def _ts(value: str) -> str:
    # Normalise to ensure lexicographic ordering matches chronological ordering
    return datetime.fromisoformat(value).isoformat()


def test_next_pending_returns_oldest_pending_request() -> None:
    queue = [
        {"id": "req-002", "created_at": _ts("2024-03-02T10:00:00"), "status": "pending"},
        {"id": "req-001", "created_at": _ts("2024-03-01T09:00:00"), "status": "pending"},
        {"id": "req-003", "created_at": _ts("2024-03-03T12:00:00"), "status": "completed"},
    ]
    pending = next_pending(queue)
    assert pending is not None
    assert pending["id"] == "req-001"


def test_next_pending_skips_completed_requests() -> None:
    queue = [
        {"id": "req-100", "created_at": _ts("2024-01-01T00:00:00"), "status": "completed"}
    ]
    assert next_pending(queue) is None


def test_record_completion_updates_entry_in_place() -> None:
    queue = [
        {"id": "req-01", "created_at": _ts("2024-04-01T00:00:00"), "status": "pending"}
    ]
    updated = record_completion(queue, "req-01", "results/runs/20240401")
    assert updated is True
    assert queue[0]["status"] == "completed"
    assert queue[0]["run_dir"] == "results/runs/20240401"


def test_record_completion_returns_false_for_unknown_id() -> None:
    queue = [
        {"id": "req-01", "created_at": _ts("2024-04-01T00:00:00"), "status": "pending"}
    ]
    assert record_completion(queue, "req-02", "results/runs/unknown") is False
