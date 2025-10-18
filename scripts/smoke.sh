#!/usr/bin/env bash
set -euo pipefail

COMPOSE=${COMPOSE:-docker compose}
COMPOSE_FILE=${COMPOSE_FILE:-docker/compose.yml}
ENABLE_VLLM=${ENABLE_VLLM:-0}
SMOKE_PROFILE=${SMOKE_PROFILE:-${PROFILE:-ollama}}

PROFILE_ARGS=()
if [[ "${ENABLE_VLLM}" == "1" ]]; then
  PROFILE_ARGS+=(--profile vllm)
fi

run_compose() {
  ${COMPOSE} -f "${COMPOSE_FILE}" "${PROFILE_ARGS[@]}" "$@"
}

ensure_service_running() {
  local service=$1
  if ! run_compose ps --status=running "${service}" >/dev/null 2>&1; then
    echo "[smoke] ${service} is not running" >&2
    exit 1
  fi
}

check_models() {
  local name=$1
  local url=$2
  echo "[smoke] Checking ${name} models endpoint at ${url}" >&2
  run_compose exec runner curl -fsS "${url}/models" >/dev/null
}

ensure_service_running runner
ensure_service_running ollama

OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://ollama:11434/v1}
check_models "ollama" "${OLLAMA_BASE_URL}"

if run_compose ps vllm >/dev/null 2>&1; then
  if run_compose ps --status=running vllm >/dev/null 2>&1; then
    VLLM_BASE_URL=${VLLM_BASE_URL:-http://vllm:8000/v1}
    check_models "vllm" "${VLLM_BASE_URL}"
  fi
fi

echo "[smoke] Checking Codex CLI availability" >&2
if run_compose exec runner command -v codex >/dev/null 2>&1; then
  run_compose exec runner codex --version
  echo "[smoke] Verifying codex --profile ${SMOKE_PROFILE} --version" >&2
  run_compose exec runner env CODEX_PROFILE="${SMOKE_PROFILE}" codex --profile "${SMOKE_PROFILE}" --version
else
  echo "[smoke] Codex CLI not installed in runner container" >&2
fi

echo "[smoke] All checks completed." >&2
