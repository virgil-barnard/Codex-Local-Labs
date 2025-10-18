#!/usr/bin/env bash
set -euo pipefail

RUN_DIR=${RUN_DIR:-}
if [[ -z "${RUN_DIR}" ]]; then
  latest=$(ls -1dt results/runs/*_hfi_* 2>/dev/null | head -n1 || true)
  RUN_DIR=${latest}
fi

if [[ -z "${RUN_DIR}" ]]; then
  echo "[hfi] No human feedback run found. Set RUN_DIR to publish." >&2
  exit 1
fi

if [[ ! -d "${RUN_DIR}" ]]; then
  echo "[hfi] RUN_DIR '${RUN_DIR}' is not a directory" >&2
  exit 1
fi

metrics_file="${RUN_DIR}/metrics.json"
if [[ ! -f "${metrics_file}" ]]; then
  echo "[hfi] metrics.json not found in ${RUN_DIR}" >&2
  exit 1
fi

sysinfo_file="${RUN_DIR}/sysinfo.json"
if [[ ! -f "${sysinfo_file}" ]]; then
  echo "[hfi] sysinfo.json missing in ${RUN_DIR}; regenerating" >&2
  python scripts/sysinfo.py > "${sysinfo_file}"
fi

ledger="results/ledger.jsonl"
queue_file="bench/hfi/FEEDBACK_QUEUE.yaml"

python - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

run_dir = Path("${RUN_DIR}")
metrics = json.loads(run_dir.joinpath("metrics.json").read_text(encoding="utf-8"))
ledger_path = Path("${ledger}")
ledger_path.parent.mkdir(parents=True, exist_ok=True)
entry = {
    "run_dir": run_dir.as_posix(),
    "published_at": datetime.now(timezone.utc).isoformat(),
    "metrics": metrics,
}
sysinfo_path = run_dir / "sysinfo.json"
if sysinfo_path.exists():
    entry["sysinfo"] = json.loads(sysinfo_path.read_text(encoding="utf-8"))
with ledger_path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry) + "\n")

queue_path = Path("${queue_file}")
if queue_path.exists():
    try:
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        queue = []
    updated = False
    for item in queue:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "completed":
            continue
        if item.get("suite") == metrics.get("suite") and item.get("profile") == metrics.get("profile"):
            item["status"] = "completed"
            item["run_dir"] = run_dir.as_posix()
            item["completed_at"] = entry["published_at"]
            updated = True
            break
    if updated:
        queue_path.write_text(json.dumps(queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

echo "[hfi] Published run ${RUN_DIR} to ${ledger}"
