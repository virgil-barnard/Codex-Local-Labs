"""Helpers for manipulating the Human Feedback Interface queue."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

QueueEntry = Dict[str, object]
LedgerEntry = Dict[str, object]

DEFAULT_QUEUE_PATH = Path("bench/hfi/FEEDBACK_QUEUE.yaml")
DEFAULT_LEDGER_PATH = Path("results/ledger.jsonl")

_ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime(_ISO_FORMAT)


def _parse_timestamp(raw: object) -> Optional[datetime]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _sanitize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _ensure_queue(entry: object) -> QueueEntry:
    if not isinstance(entry, dict):
        raise ValueError("Queue entries must be JSON objects")
    return entry


def load_queue(queue_path: Path = DEFAULT_QUEUE_PATH) -> List[QueueEntry]:
    """Load queue entries from ``queue_path``.

    The queue file stores JSON-compatible YAML; we treat it as JSON.
    """

    if not queue_path.exists():
        return []
    text = queue_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    payload = json.loads(text)
    if not isinstance(payload, list):
        raise ValueError("Queue file must contain a JSON array")
    return [_ensure_queue(entry) for entry in payload]


def save_queue(queue: Iterable[QueueEntry], queue_path: Path = DEFAULT_QUEUE_PATH) -> None:
    """Persist ``queue`` back to ``queue_path``."""

    entries = list(queue)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def add_request(
    suite: str,
    profile: str,
    *,
    notes: Optional[str] = None,
    request_id: Optional[str] = None,
    priority: Optional[int] = None,
    queue_path: Path = DEFAULT_QUEUE_PATH,
) -> QueueEntry:
    """Append a new request to the feedback queue and return it."""

    queue = load_queue(queue_path)
    normalized_suite = _sanitize_token(suite)
    normalized_profile = _sanitize_token(profile)
    if request_id is None:
        timestamp = _format_timestamp(_now_utc())
        request_id = f"{normalized_suite or 'suite'}-{normalized_profile or 'profile'}-{timestamp}"
    if any(entry.get("id") == request_id for entry in queue):
        raise ValueError(f"Queue already contains an entry with id '{request_id}'")

    created_at = _format_timestamp(_now_utc())
    entry: QueueEntry = {
        "id": request_id,
        "suite": suite,
        "profile": profile,
        "status": "pending",
        "created_at": created_at,
    }
    if notes:
        entry["notes"] = notes
    if priority is not None:
        entry["priority"] = priority

    queue.append(entry)
    save_queue(queue, queue_path)
    return entry


def load_ledger(ledger_path: Path = DEFAULT_LEDGER_PATH) -> List[LedgerEntry]:
    """Load JSON objects from the append-only ledger file."""

    if not ledger_path.exists():
        return []
    entries: List[LedgerEntry] = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                entries.append(payload)
    return entries


def reconcile_queue(
    queue_path: Path = DEFAULT_QUEUE_PATH,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
) -> int:
    """Reconcile queue entries with ledger runs.

    Returns the number of queue entries transitioned to ``completed``.
    """

    queue = load_queue(queue_path)
    ledger = load_ledger(ledger_path)

    pending_indices = [index for index, entry in enumerate(queue) if entry.get("status") != "completed"]
    if not pending_indices:
        return 0

    ledger_matches: List[Tuple[int, LedgerEntry, Optional[datetime]]] = []
    for idx, record in enumerate(ledger):
        metrics = record.get("metrics")
        if not isinstance(metrics, dict):
            continue
        if metrics.get("run_kind") != "hfi":
            continue
        timestamp = _parse_timestamp(metrics.get("timestamp")) or _parse_timestamp(record.get("published_at"))
        ledger_matches.append((idx, record, timestamp))

    used_ledgers: set[int] = set()
    updates = 0

    for queue_index in pending_indices:
        entry = queue[queue_index]
        suite = entry.get("suite")
        profile = entry.get("profile")
        created_at = _parse_timestamp(entry.get("created_at"))

        best_match: Optional[Tuple[int, LedgerEntry, Optional[datetime]]] = None
        for idx, record, ts in ledger_matches:
            if idx in used_ledgers:
                continue
            metrics = record.get("metrics", {})
            if metrics.get("suite") != suite or metrics.get("profile") != profile:
                continue
            if created_at is not None and ts is not None and ts < created_at:
                continue
            if best_match is None:
                best_match = (idx, record, ts)
                continue
            _, _, current_ts = best_match
            if current_ts is None:
                best_match = (idx, record, ts)
            elif ts is not None and ts < current_ts:
                best_match = (idx, record, ts)

        if best_match is None:
            continue

        idx, record, ts = best_match
        used_ledgers.add(idx)
        entry["status"] = "completed"
        run_dir = record.get("run_dir")
        if isinstance(run_dir, str):
            entry["run_dir"] = run_dir
        published_at = _parse_timestamp(record.get("published_at"))
        completed_at = published_at or ts
        if completed_at is not None:
            entry["completed_at"] = _format_timestamp(completed_at)
        updates += 1

    if updates:
        save_queue(queue, queue_path)
    return updates


def next_pending(queue: List[QueueEntry]) -> Optional[QueueEntry]:
    """Return the pending request with the oldest ``created_at`` timestamp."""
    candidates: List[Tuple[str, int, QueueEntry]] = []
    for index, entry in enumerate(queue):
        if entry.get("status") == "completed":
            continue
        created = entry.get("created_at")
        # Normalise missing timestamps to a sentinel that sorts after valid
        # ISO-formatted datetimes. Include the original index to provide a
        # deterministic tie-breaker when timestamps match.
        key = created if isinstance(created, str) else "\uffff"
        candidates.append((key, index, entry))

    if not candidates:
        return None

    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def record_completion(queue: List[QueueEntry], request_id: str, run_dir: str) -> bool:
    """Mark the given request as completed and attach its run directory."""
    for entry in queue:
        if entry.get("id") == request_id:
            entry["status"] = "completed"
            entry["run_dir"] = run_dir
            entry["completed_at"] = _format_timestamp(_now_utc())
            return True
    return False
