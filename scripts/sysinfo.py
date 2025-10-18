"""Collect lightweight system information for human feedback runs."""
from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _safe_run(command: List[str]) -> Optional[str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _memory_info() -> Dict[str, Any]:
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        return {
            "total_bytes": vm.total,
            "available_bytes": vm.available,
        }
    except Exception:
        # Fall back to /proc/meminfo where available.
        meminfo_path = "/proc/meminfo"
        info: Dict[str, Any] = {}
        if os.path.exists(meminfo_path):
            with open(meminfo_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("MemTotal:"):
                        info["total_kib"] = int(line.split()[1])
                    if line.startswith("MemAvailable:"):
                        info["available_kib"] = int(line.split()[1])
        return info


def _gpu_info() -> List[Dict[str, Any]]:
    query = [
        "nvidia-smi",
        "--query-gpu=name,memory.total",
        "--format=csv,noheader",
    ]
    output = _safe_run(query)
    if not output:
        return []
    gpus = []
    for line in output.splitlines():
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if not parts:
            continue
        entry: Dict[str, Any] = {"name": parts[0]}
        if len(parts) > 1:
            entry["memory_total"] = parts[1]
        gpus.append(entry)
    return gpus


def collect() -> Dict[str, Any]:
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "memory": _memory_info(),
        "gpu": _gpu_info(),
    }


def main() -> None:
    payload = collect()
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
