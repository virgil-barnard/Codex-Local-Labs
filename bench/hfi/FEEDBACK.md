# Human Feedback Interface

This folder contains the queue and documentation for running manual benchmark
sessions. Human operators follow the workflow outlined below when Codex requests
feedback.

## Quickstart

1. Inspect `FEEDBACK_QUEUE.yaml` for pending requests (`status: "pending"`).
2. For each item, run `make hfi-run SUITE=<suite> PROFILE=<profile>` inside the
   repository root. This captures the Codex run and collects system metadata.
3. Review the artifacts saved under `results/runs/<timestamp>_hfi_<profile>_<suite>/`.
4. When satisfied, publish the run with `RUN_DIR=<path> make hfi-publish`.
5. Commit and push the updated queue, ledger, and artifacts.

## Artifact Layout

Each human-feedback run saves the following files under `results/runs/...`:

- `run.log` – stdout/stderr from the Codex CLI (or placeholder output if absent).
- `trace/` – raw traces emitted by the Codex CLI when available.
- `metrics.json` – normalized metrics consumed by the aggregator.
- `sysinfo.json` – hardware and environment metadata captured locally.

## Publishing Rules

- Never edit `results/ledger.jsonl` manually. Always use `make hfi-publish`.
- The ledger is append-only; one JSON document per run.
- `FEEDBACK_QUEUE.yaml` is maintained as JSON-compatible YAML for ease of use.
- When publishing, ensure the corresponding queue entry is marked `status: "completed"`.
- Keep large artifacts (logs, traces) under version control so Codex can review them.

## Troubleshooting

- If the Codex CLI is not available locally, the harness records placeholder
  metrics so the maintainer can still log the manual review.
- Missing GPU metrics simply result in `gpu: []` within `sysinfo.json`.
- To re-run a failed request, leave the queue entry as `status: "pending"` and
  rerun `make hfi-run` at your convenience.
