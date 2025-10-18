from __future__ import annotations

from datetime import datetime

import json
from typing import List

from bench.repo_ops.queue import (
    add_request,
    load_queue,
    reconcile_queue,
    save_queue,
)
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


def test_add_request_appends_entry_with_defaults(tmp_path) -> None:
    queue_path = tmp_path / "FEEDBACK_QUEUE.yaml"
    entry = add_request(
        suite="python_katas",
        profile="ollama",
        notes="baseline",
        queue_path=queue_path,
    )

    assert entry["status"] == "pending"
    assert entry["suite"] == "python_katas"
    assert entry["profile"] == "ollama"
    assert "created_at" in entry
    assert entry["id"].startswith("python-katas-ollama-")

    loaded = load_queue(queue_path)
    assert loaded == [entry]


def test_reconcile_queue_matches_suite_and_profile(tmp_path) -> None:
    queue_path = tmp_path / "FEEDBACK_QUEUE.yaml"
    ledger_path = tmp_path / "ledger.jsonl"

    queue_entries: List[dict] = [
        {
            "id": "req-123",
            "suite": "python_katas",
            "profile": "ollama",
            "status": "pending",
            "created_at": "2024-04-01T00:00:00Z",
        }
    ]
    save_queue(queue_entries, queue_path)

    ledger_record = {
        "run_dir": "results/runs/20240401T010000Z_hfi_ollama_python_katas",
        "published_at": "2024-04-01T01:05:00+00:00",
        "metrics": {
            "suite": "python_katas",
            "profile": "ollama",
            "run_kind": "hfi",
            "timestamp": "2024-04-01T01:00:00Z",
        },
    }

    with ledger_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(ledger_record) + "\n")

    updated = reconcile_queue(queue_path=queue_path, ledger_path=ledger_path)
    assert updated == 1

    queue_after = load_queue(queue_path)
    assert queue_after[0]["status"] == "completed"
    assert queue_after[0]["run_dir"] == ledger_record["run_dir"]
    assert queue_after[0]["completed_at"].startswith("2024-04-01T01:05:00")
