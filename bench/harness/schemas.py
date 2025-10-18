"""Schema helpers for normalizing benchmark run artifacts."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _parse_timestamp(raw: str) -> datetime:
    """Parse an ISO8601 timestamp string into an aware datetime."""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp '{raw}'") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _coerce_optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected integer value, got {value!r}") from exc


def _coerce_optional_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected float value, got {value!r}") from exc


@dataclass
class RunSummary:
    """Normalized view of a benchmark run for CSV export."""

    run_dir: Path
    run_id: str
    timestamp: datetime
    suite: str
    profile: str
    backend_provider: str
    backend_model: str
    wall_s: float
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    tps: Optional[float] = None
    edits: Optional[int] = None
    files_changed: Optional[int] = None
    loc_delta: Optional[int] = None
    tests_pass: Optional[bool] = None
    gpu_name: Optional[str] = None
    gpu_mem_total: Optional[str] = None
    run_kind: str = "bench"
    exit_code: Optional[int] = None
    commands_total: Optional[int] = None
    commands_succeeded: Optional[int] = None
    commands_failed: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    CSV_FIELDS: Iterable[str] = (
        "timestamp",
        "run_id",
        "suite",
        "profile",
        "run_kind",
        "backend_provider",
        "backend_model",
        "wall_s",
        "tokens_in",
        "tokens_out",
        "tps",
        "edits",
        "files_changed",
        "loc_delta",
        "commands_total",
        "commands_succeeded",
        "commands_failed",
        "tests_pass",
        "gpu_name",
        "gpu_mem_total",
        "exit_code",
        "run_dir",
    )

    @classmethod
    def from_json(cls, payload: Mapping[str, Any], run_dir: Path) -> "RunSummary":
        """Create a :class:`RunSummary` from a JSON payload."""
        timestamp_raw = payload.get("timestamp")
        if not isinstance(timestamp_raw, str):
            raise ValueError("metrics.json is missing a timestamp string")
        timestamp = _parse_timestamp(timestamp_raw)

        run_id = str(payload.get("run_id") or run_dir.name)
        suite = str(payload.get("suite") or "")
        profile = str(payload.get("profile") or "")
        backend_provider = str(payload.get("backend_provider") or "unknown")
        backend_model = str(payload.get("backend_model") or "unknown")
        wall_s = float(payload.get("wall_s") or 0.0)

        tests_pass = payload.get("tests_pass")
        if isinstance(tests_pass, str):
            tests_pass = tests_pass.lower() in {"1", "true", "yes"}
        elif tests_pass is not None:
            tests_pass = bool(tests_pass)

        extra: Dict[str, Any] = {
            key: value
            for key, value in payload.items()
            if key not in {
                "timestamp",
                "run_id",
                "suite",
                "profile",
                "backend_provider",
                "backend_model",
                "wall_s",
                "tests_pass",
                "commands_total",
                "commands_succeeded",
                "commands_failed",
            }
        }

        return cls(
            run_dir=run_dir,
            run_id=run_id,
            timestamp=timestamp,
            suite=suite,
            profile=profile,
            backend_provider=backend_provider,
            backend_model=backend_model,
            wall_s=wall_s,
            tokens_in=_coerce_optional_int(payload.get("tokens_in")),
            tokens_out=_coerce_optional_int(payload.get("tokens_out")),
            tps=_coerce_optional_float(payload.get("tps")),
            edits=_coerce_optional_int(payload.get("edits")),
            files_changed=_coerce_optional_int(payload.get("files_changed")),
            loc_delta=_coerce_optional_int(payload.get("loc_delta")),
            tests_pass=tests_pass,
            gpu_name=(payload.get("gpu_name") or None),
            gpu_mem_total=(payload.get("gpu_mem_total") or None),
            run_kind=str(payload.get("run_kind") or "bench"),
            exit_code=_coerce_optional_int(payload.get("exit_code")),
            commands_total=_coerce_optional_int(payload.get("commands_total")),
            commands_succeeded=_coerce_optional_int(payload.get("commands_succeeded")),
            commands_failed=_coerce_optional_int(payload.get("commands_failed")),
            extra=extra,
        )

    def to_csv_row(self) -> Dict[str, str]:
        """Render the summary as a flat dictionary for CSV writing."""
        def _fmt(value: Any) -> str:
            if value is None:
                return "NA"
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, datetime):
                return value.astimezone(timezone.utc).strftime(ISOFORMAT)
            return str(value)

        row = {
            "timestamp": self.timestamp.astimezone(timezone.utc).strftime(ISOFORMAT),
            "run_id": self.run_id,
            "suite": self.suite,
            "profile": self.profile,
            "run_kind": self.run_kind,
            "backend_provider": self.backend_provider,
            "backend_model": self.backend_model,
            "wall_s": f"{self.wall_s:.3f}",
            "tokens_in": _fmt(self.tokens_in),
            "tokens_out": _fmt(self.tokens_out),
            "tps": _fmt(self.tps),
            "edits": _fmt(self.edits),
            "files_changed": _fmt(self.files_changed),
            "loc_delta": _fmt(self.loc_delta),
            "commands_total": _fmt(self.commands_total),
            "commands_succeeded": _fmt(self.commands_succeeded),
            "commands_failed": _fmt(self.commands_failed),
            "tests_pass": _fmt(self.tests_pass),
            "gpu_name": _fmt(self.gpu_name),
            "gpu_mem_total": _fmt(self.gpu_mem_total),
            "exit_code": _fmt(self.exit_code),
            "run_dir": self.run_dir.as_posix(),
        }
        return row


def load_run_summary(run_dir: Path) -> Optional[RunSummary]:
    """Load a run summary from ``metrics.json`` if it exists."""
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        return None
    data = metrics_path.read_text(encoding="utf-8")
    payload = json.loads(data)
    return RunSummary.from_json(payload, run_dir)
