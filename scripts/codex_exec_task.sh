#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <TASK> [PROFILE]" >&2
  exit 1
fi

TASK=$1
PROFILE=${2:-ollama}

ts=$(date -u +%Y%m%dT%H%M%SZ)
task_name=$(basename "${TASK}")
run_dir="results/runs/${ts}_${PROFILE}"
trace_dir="${run_dir}/trace"
run_log="${run_dir}/run.log"

mkdir -p "${trace_dir}"

config_template=${CODEX_CONFIG_TEMPLATE:-codex/config.template.toml}
config_target=${CODEX_CONFIG_PATH:-$HOME/.codex/config.toml}
if [[ -f "${config_template}" ]]; then
  mkdir -p "$(dirname "${config_target}")"
  cp "${config_template}" "${config_target}"
fi

export CODEX_PROFILE="${PROFILE}"
export CODEX_TRACE_DIR="${trace_dir}"
export CODEX_LOG_LEVEL=${CODEX_LOG_LEVEL:-trace}

echo "[codex] Executing ${task_name} with profile ${PROFILE}" >&2
set -o pipefail
if command -v codex >/dev/null 2>&1; then
  codex exec --task "${TASK}" --yes --verbose | tee "${run_log}"
else
  echo "[codex] Codex CLI is not installed in the current environment" >&2
  exit 127
fi
