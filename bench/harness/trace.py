"""Helpers for parsing Codex JSON event traces into aggregate metrics."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Set, Tuple

_PROMPT_TOKEN_KEYS = (
    "prompt_tokens",
    "input_tokens",
    "tokens_in",
    "prompt",
    "input",
)
_COMPLETION_TOKEN_KEYS = (
    "completion_tokens",
    "output_tokens",
    "tokens_out",
    "completion",
    "generated",
)
_PATH_KEYS = ("path", "filepath", "file", "filename", "relative_path")
_STATUS_SUCCESS = {"success", "succeeded", "ok", "completed", "done"}
_STATUS_FAILURE = {"failure", "failed", "error", "timeout", "cancelled", "canceled"}


def _maybe_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def _iter_mappings(obj: Any) -> Iterator[Dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for item in obj.values():
            yield from _iter_mappings(item)
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_mappings(item)


def _first_token_value(mapping: Dict[str, Any], keys: Iterable[str]) -> Optional[int]:
    for key in keys:
        if key in mapping:
            value = _maybe_int(mapping.get(key))
            if value is not None:
                return value
    return None


def _extract_usage(event: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    sources = [event]

    usage = event.get("usage")
    if isinstance(usage, dict):
        sources.append(usage)
    metrics = event.get("metrics")
    if isinstance(metrics, dict):
        sources.append(metrics)
        metrics_usage = metrics.get("usage")
        if isinstance(metrics_usage, dict):
            sources.append(metrics_usage)

    for mapping in sources:
        if tokens_in is None:
            tokens_in = _first_token_value(mapping, _PROMPT_TOKEN_KEYS)
        if tokens_out is None:
            tokens_out = _first_token_value(mapping, _COMPLETION_TOKEN_KEYS)
        if tokens_in is not None and tokens_out is not None:
            break
    return tokens_in, tokens_out


def _is_edit_event(event: Dict[str, Any], label: str) -> bool:
    if "edit" in label or "diff" in label:
        return True
    if any(key in event for key in ("diff", "patch", "edit", "edits")):
        return True
    return False


def _collect_changed_files(event: Dict[str, Any]) -> Set[str]:
    paths: Set[str] = set()
    for mapping in _iter_mappings(event):
        for key in _PATH_KEYS:
            value = mapping.get(key)
            if isinstance(value, str) and value.strip():
                paths.add(value.strip())
        files = mapping.get("files")
        if isinstance(files, list):
            for entry in files:
                if isinstance(entry, str) and entry.strip():
                    paths.add(entry.strip())
                elif isinstance(entry, dict):
                    for key in _PATH_KEYS:
                        val = entry.get(key)
                        if isinstance(val, str) and val.strip():
                            paths.add(val.strip())
    return paths


def _extract_loc_delta(event: Dict[str, Any]) -> Optional[int]:
    loc_value: Optional[int] = None
    for mapping in _iter_mappings(event):
        if loc_value is None and "loc_delta" in mapping:
            loc = _maybe_int(mapping.get("loc_delta"))
            if loc is not None:
                loc_value = loc
                continue
        inserted = _maybe_int(mapping.get("lines_added") or mapping.get("inserted") or mapping.get("additions"))
        removed = _maybe_int(mapping.get("lines_removed") or mapping.get("deleted") or mapping.get("deletions"))
        if inserted is not None or removed is not None:
            loc_value = (inserted or 0) - (removed or 0)
    return loc_value


def _command_success(event: Dict[str, Any], label: str) -> Optional[bool]:
    lower_label = label.lower()
    looks_like_command = "command" in lower_label or "shell" in lower_label
    exit_code: Optional[int] = None
    status: Optional[str] = None

    for mapping in _iter_mappings(event):
        if not looks_like_command and any(key in mapping for key in ("command", "shell", "cmd")):
            looks_like_command = True
        if exit_code is None and "exit_code" in mapping:
            exit_code = _maybe_int(mapping.get("exit_code"))
        if status is None and "status" in mapping:
            raw = mapping.get("status")
            if isinstance(raw, str):
                status = raw.lower().strip()

    if not looks_like_command and exit_code is None and status is None:
        return None

    if exit_code is not None:
        return exit_code == 0
    if status is not None:
        if status in _STATUS_SUCCESS:
            return True
        if status in _STATUS_FAILURE:
            return False
    return None


@dataclass
class TraceMetrics:
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    edits: Optional[int] = None
    files_changed: Optional[int] = None
    loc_delta: Optional[int] = None
    commands_total: Optional[int] = None
    commands_succeeded: Optional[int] = None
    commands_failed: Optional[int] = None

    def to_dict(self) -> Dict[str, Optional[int]]:
        return {
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "edits": self.edits,
            "files_changed": self.files_changed,
            "loc_delta": self.loc_delta,
            "commands_total": self.commands_total,
            "commands_succeeded": self.commands_succeeded,
            "commands_failed": self.commands_failed,
        }


def extract_codex_metrics(events_path: Path) -> TraceMetrics:
    tokens_in_total = 0
    tokens_out_total = 0
    has_tokens_in = False
    has_tokens_out = False
    edits = 0
    changed_files: Set[str] = set()
    loc_delta_total = 0
    has_loc_delta = False
    command_total = 0
    command_success = 0
    command_failure = 0

    if not events_path.exists():
        return TraceMetrics()

    with events_path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            label = str(event.get("event") or event.get("type") or "").lower()

            tokens_in, tokens_out = _extract_usage(event)
            if tokens_in is not None:
                tokens_in_total += tokens_in
                has_tokens_in = True
            if tokens_out is not None:
                tokens_out_total += tokens_out
                has_tokens_out = True

            is_edit = _is_edit_event(event, label)
            if is_edit:
                edits += 1
                changed_files.update(_collect_changed_files(event))
                loc_delta = _extract_loc_delta(event)
                if loc_delta is not None:
                    loc_delta_total += loc_delta
                    has_loc_delta = True

            command_result = _command_success(event, label)
            if command_result is not None:
                command_total += 1
                if command_result:
                    command_success += 1
                else:
                    command_failure += 1

    return TraceMetrics(
        tokens_in=tokens_in_total if has_tokens_in else None,
        tokens_out=tokens_out_total if has_tokens_out else None,
        edits=edits if edits else None,
        files_changed=len(changed_files) if changed_files else None,
        loc_delta=loc_delta_total if has_loc_delta else None,
        commands_total=command_total if command_total else None,
        commands_succeeded=command_success if command_total else None,
        commands_failed=command_failure if command_total else None,
    )


def merge_trace_metrics(
    metrics: Dict[str, Any], events_path: Path, *, wall_time: Optional[float] = None
) -> Dict[str, Any]:
    """Merge extracted trace metrics into an existing metrics payload."""

    merged = dict(metrics)
    trace = extract_codex_metrics(events_path)
    updates = trace.to_dict()

    for key, value in updates.items():
        if value is None:
            continue
        current = merged.get(key)
        if current in (None, "", "NA"):
            merged[key] = value
        else:
            try:
                current_int = int(current)
            except (TypeError, ValueError):
                merged[key] = value
            else:
                if current_int == 0 and value != 0:
                    merged[key] = value
    if trace.tokens_out is not None:
        wall = wall_time if wall_time is not None else _maybe_int(merged.get("wall_s"))
        if wall and wall > 0:
            merged["tps"] = round(trace.tokens_out / float(wall), 3)
    return merged
