#!/usr/bin/env bash
set -euo pipefail

SUITE=${SUITE:-}
PROFILE=${PROFILE:-}

if [[ -z "${SUITE}" ]]; then
  echo "[hfi] SUITE environment variable is required" >&2
  exit 1
fi

if [[ -z "${PROFILE}" ]]; then
  echo "[hfi] PROFILE environment variable is required" >&2
  exit 1
fi

echo "[hfi] Starting human feedback run for suite '${SUITE}' (profile=${PROFILE})" >&2

set +e
output=$(BENCH_RUN_KIND=hfi SUITE="${SUITE}" PROFILE="${PROFILE}" ./bench/harness/run_suite.sh)
status=$?
set -e

echo "${output}"

run_dir=$(echo "${output}" | awk -F= '/^RUN_DIR=/{print $2}' | tail -n1)
if [[ -z "${run_dir}" ]]; then
  echo "[hfi] Unable to determine run directory from harness output" >&2
  exit 1
fi

python scripts/sysinfo.py > "${run_dir}/sysinfo.json"
echo "[hfi] System information captured at ${run_dir}/sysinfo.json" >&2

if [[ ${status} -ne 0 ]]; then
  if [[ ${status} -eq 127 ]]; then
    echo "[hfi] Codex CLI unavailable; placeholder metrics recorded" >&2
  else
    echo "[hfi] Benchmark run exited with status ${status}" >&2
    exit ${status}
  fi
fi

echo "[hfi] Human feedback run artifacts located at ${run_dir}"
