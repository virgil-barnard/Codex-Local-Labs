#!/usr/bin/env bash
set -euo pipefail

SUITE=${SUITE:-}
PROFILE=${PROFILE:-}

if [[ -z "${SUITE}" ]]; then
  echo "[bench] SUITE environment variable is required" >&2
  exit 1
fi

if [[ -z "${PROFILE}" ]]; then
  echo "[bench] PROFILE environment variable is required" >&2
  exit 1
fi

TASK_FILE="codex/tasks/${SUITE}.yaml"
if [[ ! -f "${TASK_FILE}" ]]; then
  echo "[bench] Task file '${TASK_FILE}' not found" >&2
  exit 1
fi

run_kind=${BENCH_RUN_KIND:-bench}
ts=$(date -u +%Y%m%dT%H%M%SZ)
run_id="${ts}_${run_kind}_${PROFILE}_${SUITE}"
run_dir="results/runs/${run_id}"
trace_dir="${run_dir}/trace"
run_log="${run_dir}/run.log"
metrics_file="${run_dir}/metrics.json"

mkdir -p "${trace_dir}"

config_template=${CODEX_CONFIG_TEMPLATE:-codex/config.template.toml}
config_target=${CODEX_CONFIG_PATH:-$HOME/.codex/config.toml}
if [[ -f "${config_template}" ]]; then
  mkdir -p "$(dirname "${config_target}")"
  cp "${config_template}" "${config_target}"
fi

backend_provider=${BENCH_BACKEND_PROVIDER:-${PROFILE}}
backend_model=${BENCH_BACKEND_MODEL:-${MODEL:-unknown}}

start_epoch=$(date +%s)
exit_code=0
if command -v codex >/dev/null 2>&1; then
  echo "[bench] Running suite '${SUITE}' with profile '${PROFILE}'" >&2
  set +e
  CODEX_PROFILE="${PROFILE}" \
    CODEX_TRACE_DIR="${trace_dir}" \
    CODEX_LOG_LEVEL=${CODEX_LOG_LEVEL:-trace} \
    codex exec --task "${TASK_FILE}" --yes --verbose | tee "${run_log}"
  exit_code=${PIPESTATUS[0]}
  set -e
else
  echo "[bench] Codex CLI not found; generating placeholder metrics" | tee "${run_log}"
  exit_code=127
fi
end_epoch=$(date +%s)
wall_s=$((end_epoch - start_epoch))
if [[ ${wall_s} -lt 0 ]]; then
  wall_s=0
fi

timestamp_iso=$(python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
PY
)

task_count=$(python - <<PY
from pathlib import Path
count = 0
for line in Path("${TASK_FILE}").read_text(encoding="utf-8").splitlines():
    if line.strip().startswith("- id:"):
        count += 1
print(count)
PY
)

python - <<PY
import json
from pathlib import Path

metrics = {
    "run_id": "${run_id}",
    "timestamp": "${timestamp_iso}",
    "suite": "${SUITE}",
    "profile": "${PROFILE}",
    "run_kind": "${run_kind}",
    "task_file": "${TASK_FILE}",
    "task_count": int(${task_count}),
    "backend_provider": "${backend_provider}",
    "backend_model": "${backend_model}",
    "wall_s": ${wall_s},
    "exit_code": ${exit_code},
    "tests_pass": ${exit_code} == 0,
    "tokens_in": None,
    "tokens_out": None,
    "tps": None,
    "edits": None,
    "files_changed": None,
    "loc_delta": None,
    "gpu_name": None,
    "gpu_mem_total": None,
}

metrics_path = Path("${metrics_file}")
metrics_path.parent.mkdir(parents=True, exist_ok=True)
metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

HARVEST_HINT="Run metrics captured in ${metrics_file}"
echo "${HARVEST_HINT}" >&2
echo "RUN_DIR=${run_dir}"

exit ${exit_code}
