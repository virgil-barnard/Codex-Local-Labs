AGENTS.md — Codex‑Local Labs (for GPT‑5 Codex)

You are the primary coding agent for bootstrapping a Dockerized lab that runs OpenAI’s Codex CLI against local LLM backends and benchmarks them on small, repeatable coding tasks. The maintainer will approve PRs, pull locally, run GPU benchmarks, and push results back as human feedback artifacts. Default target platform: Linux container runtime; NVIDIA GPU is optional (used when available).

⸻

Goals (in order)
	1.	Stand up a reproducible Docker stack (Codex runner + local providers).
	2.	Generate a minimal yet rigorous benchmark harness (katas, bugfix minis, repo ops) with unit tests.
	3.	Automate non‑interactive codex exec runs and emit machine‑readable metrics (CSV/JSON + logs).
	4.	Implement a Human‑Feedback Loop (HFL) so the maintainer can run GPU tests locally and publish results Codex will ingest next run.
	5.	Keep tests green; commits small, auditable, and reversible.

⸻

Operating constraints & conventions
	•	Language/stack: Python 3.11+, Bash, Docker, Docker Compose, Makefile.
	•	Providers (OpenAI‑compatible endpoints):
	•	Ollama (CPU/GPU) — default profile.
	•	vLLM (GPU‑oriented) — optional, guarded by a Compose profile.
	•	(LM Studio may be used by maintainer; don’t require it in Compose.)
	•	Codex CLI: Use non‑interactive mode for repeatability; approvals/sandbox enabled.
	•	Determinism: Default temperature ≤ 0.2 for benchmarks unless exploration is required.
	•	Secrets: No plaintext secrets in repo; read base URLs/keys from env files or .env.
	•	DX: One‑command operations via make for each phase.

⸻

Directory layout to create

codex-local-labs/
├─ AGENTS.md                       # this file
├─ docker/
│  ├─ Dockerfile.runner            # codex + tooling
│  ├─ Dockerfile.vllm              # optional, GPU-enabled
│  ├─ compose.yml
│  └─ profiles/                    # per-provider env files
│     ├─ ollama.env
│     └─ vllm.env
├─ codex/
│  ├─ config.template.toml         # copied to ~/.codex/config.toml in runner
│  └─ tasks/                       # benchmark task specs (text/yaml)
│     ├─ python_katas.yaml
│     ├─ bugfix_mini.yaml
│     └─ repo_ops.yaml
├─ bench/
│  ├─ oracle/                      # expected outputs / unit tests
│  │  ├─ katas/                    # tests for katas
│  │  └─ bugfix/                   # failing tests to be fixed
│  └─ harness/
│     ├─ run_suite.sh
│     ├─ harvest_metrics.py
│     └─ schemas.py
├─ bench/hfi/                      # Human‑Feedback Interface (HFL)
│  ├─ FEEDBACK.md
│  └─ FEEDBACK_QUEUE.yaml          # Codex appends requests; human runs
├─ scripts/
│  ├─ bootstrap.sh                 # one‑shot local bootstrap (optional)
│  ├─ smoke.sh                     # fast health checks
│  ├─ codex_exec_task.sh           # thin wrapper over codex exec
│  ├─ hfi_run.sh                   # human runs requested jobs locally
│  ├─ hfi_publish.sh               # validate, sign, append, commit
│  └─ sysinfo.py                   # provenance for HFL runs
├─ results/
│  ├─ runs/                        # timestamped run folders with logs, metrics
│  ├─ dashboards/                  # CSV/JSON aggregates; optional HTML
│  └─ ledger.jsonl                 # append‑only HFL ledger
├─ .github/
│  └─ workflows/
│     └─ bench.yml                 # optional CI matrix (default-off)
├─ pyproject.toml                  # ruff/pytest/coverage config
├─ Makefile
└─ README.md


⸻

Commit protocol
	•	Small, vertical slices; one logical change per commit.
	•	Conventional messages: feat|fix|chore(scope): summary.
	•	After each milestone, append the commit hash into the milestone box.
	•	Keep PRs ≲ 300 LOC net diff (except vendor/config blobs).

⸻

Milestones (implement in order)

M0 — Repo & Tooling Scaffolding
	•	Create repo tree exactly as above. COMMIT: 0bde9cd70809f502efb22e4f41f398124478dafe
	•	Add pyproject.toml with ruff, pytest, coverage config. COMMIT: 16a04c9cb9a4871080370b7b42ba6f3ef9f52053
	•	Add Makefile with targets:
	•	make build (build runner + vllm images)
	•	make up (compose up -d)
	•	make down (compose down -v)
	•	make smoke (provider health + codex version)
	•	make bench SUITE=python_katas PROFILE=ollama
	•	make harvest (aggregate results → CSV)
	•	make hfi-run SUITE=... PROFILE=... (human loop)
	•	make hfi-publish (append to ledger, stage artifacts)
COMMIT: e678bc7b8176525592efc4d65eeae8ff66f58557
	•	README.md quickstart. COMMIT: 1d5ba02f16b9b6150f145ee8d2633a2ad77bbc58

M1 — Dockerized Providers & Runner
	•	compose.yml services:
	•	runner: Codex CLI + Python tooling; mounts repo; depends_on providers.
	•	ollama: official image; persistent model cache volume.
	•	vllm: optional GPU service (compose profile vllm), port 8000.
COMMIT: f041fe55b72d0746ef9cd520e8f88085e97a6b11
	•	Dockerfile.runner: install Codex CLI + pytest, ruff, psutil, pandas. COMMIT: 4c1f7ac9fa59e6a4963949d2c81316f4c8c9f03c
	•	Dockerfile.vllm: CUDA base, vLLM install; model/HF cache volumes. COMMIT: 07959534a3cf41098bd7b18ca2efe912e7828299
	•	docker/profiles/*.env (base URLs, API key placeholders). COMMIT: 1a535d263450d17f654a06c22cd11173b4bd97b0
	•	scripts/smoke.sh curls provider /v1/models and runs codex --version. COMMIT: dcd5423ff9616e7fabd4c1f48c4ecc1c07d51e65

M2 — Codex Config & Exec Wrapper
	•	codex/config.template.toml with:
	•	[defaults] workspace = "."
	•	Profiles: [profiles.ollama], [profiles.vllm] pointing to env‑driven base URLs.
COMMIT: 76103235c77c5977162799aa8a8a7df62172a4c3
	•	scripts/codex_exec_task.sh:
	•	Args: TASK, PROFILE (default ollama).
	•	Sets CODEX_PROFILE, CODEX_TRACE_DIR, CODEX_LOG_LEVEL=trace.
	•	Runs codex exec --task "$TASK" --yes --verbose | tee .../run.log.
COMMIT: 72d71f9ca39ef020101d53d6ed2da070c296ba8d

M3 — Bench Suites & Oracles
	•	codex/tasks/python_katas.yaml:
	•	5–10 tiny functions with docstrings; tests in bench/oracle/katas/test_*.py.
	•	Success = pytest green after Codex edits.
COMMIT: fcdb08fcc8724eef744989465117318227c913b1
COMMIT: fcfb4bc3bf1f5d46fb540e393f27303d02029f8a
	•	codex/tasks/bugfix_mini.yaml:
	•	Minimal seeded bug(s) + failing tests in bench/oracle/bugfix/.
	•	Success = tests pass; record diff size & time‑to‑green.
COMMIT: fcdb08fcc8724eef744989465117318227c913b1
COMMIT: fcfb4bc3bf1f5d46fb540e393f27303d02029f8a
	•	codex/tasks/repo_ops.yaml:
	•	Tasks such as adding pre-commit, Ruff hooks, minimal CI workflow.
	•	Success = lint/test pass; files correctly added.
COMMIT: fcdb08fcc8724eef744989465117318227c913b1
COMMIT: fcfb4bc3bf1f5d46fb540e393f27303d02029f8a

M4 — Harness, Metrics, Dashboards
	•	bench/harness/run_suite.sh:
	•	Selects provider profile.
	•	Invokes scripts/codex_exec_task.sh with suite path.
	•	Runs pytest -q post‑apply; non‑zero exit on failure.
COMMIT: ______
	•	bench/harness/harvest_metrics.py:
	•	Parse results/runs/*/run.log + pytest.txt.
	•	Emit results/dashboards/metrics.csv with columns:
timestamp, profile, suite, task_id, wall_s, edits, files_changed, loc_delta, pass, tokens_in, tokens_out, tps, gpu_util_avg (NA if missing).
COMMIT: ______
	•	Optional HTML/Markdown summary from CSV. COMMIT: ______

M5 — CI (optional, default‑off)
	•	.github/workflows/bench.yml matrix over PROFILE × SUITE.
	•	Jobs: docker compose up then run harness in runner.
	•	Trigger via workflow_dispatch to avoid long runs by default.
COMMIT: ______

⸻

Human‑Feedback Loop (HFL)

This enables Codex (no GPU) to queue GPU experiments; the maintainer runs them locally; results are published back for Codex to ingest.

Files to implement
	1.	bench/hfi/FEEDBACK.md — human instructions (see below content).
	2.	bench/hfi/FEEDBACK_QUEUE.yaml — owned by Codex; append‑only queue of requested runs. Example seed:

requests:
  - id: "2025-10-17T01:23:45Z_ollama_llama3_8b_python_katas"
    suite: "codex/tasks/python_katas.yaml"
    profile: "ollama"
    backend:
      provider: "ollama"
      model: "llama3:8b-instruct-q4_K_M"
      temperature: 0.2
    notes: "Baseline, deterministic"


	3.	scripts/hfi_run.sh — executes a queued request locally (Docker), stores artifacts under results/runs/<ts>_hfi_<profile>/ and captures provenance via scripts/sysinfo.py.
	4.	scripts/sysinfo.py — emits sysinfo.json (OS, Python, GPUs via nvidia-smi, driver, etc.).
	5.	scripts/hfi_publish.sh — validates/harvests metrics, computes checksums, appends a JSON object to results/ledger.jsonl, stages artifacts.
	6.	scripts/append_to_ledger.py — helper (optional) invoked by publisher to append one JSON object per run.
	7.	Make targets:

hfi-run:      ## SUITE=... PROFILE=... → run queued job locally
hfi-publish:  ## append to ledger + stage results for commit



FEEDBACK.md (place this verbatim)

# Human Feedback Loop (HFL)

This repo supports offline GPU runs initiated by GPT‑5 Codex.

## TL;DR
1. `git pull`
2. Inspect `bench/hfi/FEEDBACK_QUEUE.yaml` (authored by Codex).
3. Run: `make hfi-run SUITE=<suite> PROFILE=<profile>`
4. Publish: `make hfi-publish`
5. Push: `git push`

Artifacts go to `results/runs/<timestamp>_hfi_<profile>/`. They are validated,
hashed, and appended to `results/ledger.jsonl`. A CSV view is maintained at
`results/dashboards/metrics.csv`.

Data contract Codex must honor
	•	Queue: bench/hfi/FEEDBACK_QUEUE.yaml is append‑only. Codex adds items and later marks them status: completed when matching ledger entries are present.
	•	Ledger: results/ledger.jsonl is append‑only; one JSON object per human run including run_dir, sysinfo, optional metrics.
	•	Metrics CSV: results/dashboards/metrics.csv is a flat table for quick parsing by Codex; minimum columns:
timestamp, profile, suite, backend_provider, backend_model, wall_s, tokens_in, tokens_out, tps, edits, files_changed, loc_delta, tests_pass, gpu_name, gpu_mem_total.

Codex behaviors to implement
	•	Queue writer: append new request objects without clobbering prior entries.
	•	Queue reconciler: mark status: completed when a corresponding ledger entry appears (match by id or (suite, profile, timestamp≈)), and link run_dir.
	•	Ingestor: read results/ledger.jsonl + CSV, then update results/analysis/latest_summary.md (tables by profile/model/suite) and adjust future requests (e.g., tune temperature, change model, schedule retries).

⸻

Compose design (requirements)

docker/compose.yml must:
	•	Expose:
	•	ollama at http://ollama:11434/v1
	•	vllm at http://vllm:8000/v1 (enabled when profile vllm is active)
	•	runner with repo mounted at /workspace
	•	Pass through env vars for base URL & keys (via profile .env files).
	•	Provide NVIDIA support for vllm when GPUs are present:

deploy:
  resources:
    reservations:
      devices:
        - capabilities: [gpu]


	•	Use volumes for model caches to avoid repeated downloads.

⸻

Make targets (requirements)
	•	make build — build runner and optional vllm images.
	•	make up — docker compose up -d (enable profile vllm with ENABLE_VLLM=1).
	•	make down — docker compose down -v.
	•	make smoke — run scripts/smoke.sh (check /v1/models + codex --version).
	•	make bench SUITE=python_katas PROFILE=ollama — run suite in runner.
	•	make harvest — refresh CSV aggregates from results/runs/*.
	•	make hfi-run SUITE=... PROFILE=... — execute HFL run locally.
	•	make hfi-publish — append to ledger and stage artifacts.

⸻

Task file expectations

Author tasks to be self‑contained, with explicit intent and acceptance tests. YAML structure is acceptable; each task includes:

- id: "kata:add_two_numbers"
  intent: "Implement add(a,b) to satisfy unit tests."
  workspace: "."
  steps:
    - run: "pytest -q bench/oracle/katas -k test_add_two_numbers || true"
    - edit: "src/katas/add.py"
    - run: "pytest -q bench/oracle/katas -k test_add_two_numbers"
  success:
    tests_pass: true
    max_edits: 3

Codex may adapt to the current CLI schema; runs must remain non‑interactive via codex exec --task.

⸻

Metrics to capture

For each (PROFILE, SUITE, TASK) record:
	•	Latency: wall time (and per‑step timings if available).
	•	Throughput: tokens in/out, tokens/sec (if backend reports).
	•	Edits: count, files changed, LOC delta.
	•	Success: unit tests pass/fail; retries.
	•	Resource: GPU utilization (sample nvidia-smi) or CPU % when GPU absent.
Missing fields should be NA.

⸻

Coding standards
	•	Lint with ruff; test with pytest (pytest -q in harness).
	•	Prefer numpy + stdlib; keep benchmarks light and deterministic.
	•	Shell scripts: set -euo pipefail; POSIX‑portable where feasible.

⸻

Security & safety
	•	Never exfiltrate credentials; read provider settings from env only.
	•	Restrict provider services to the Compose network; avoid host exposure.
	•	Codex edits should remain in workspace; no writes outside repo tree.

⸻

Maintainer evaluation (definition of done)
	1.	make build && make up && make smoke prints provider models and codex --version.
	2.	make bench SUITE=python_katas PROFILE=ollama runs end‑to‑end, writing results/runs/<ts>/*.
	3.	make harvest yields results/dashboards/metrics.csv with ≥5 rows.
	4.	Switching to PROFILE=vllm (GPU present) also completes successfully.
	5.	HFL: make hfi-run ... then make hfi-publish appends a new object to results/ledger.jsonl and stages artifacts.

⸻

Initial task queue (execute now)
	1.	M0: Scaffold repo, tooling, Makefile, README.
	2.	M1: Compose with runner, ollama, optional vllm; smoke script.
	3.	M2: Codex config template + exec wrapper.
	4.	[x] M3: Implement python_katas, bugfix_mini, repo_ops suites + oracles. COMMIT: fcfb4bc3bf1f5d46fb540e393f27303d02029f8a
	5.	[x] M4: Harness & metrics aggregator; CSV output. COMMIT: 11f56e55f17498e2632153199de4cab1e5cc4bd9
	6.	[x] HFL: Add bench/hfi and scripts; seed FEEDBACK_QUEUE.yaml with 1–2 requests. COMMIT: 11f56e55f17498e2632153199de4cab1e5cc4bd9
	7.	M5 (optional): CI workflow.
	8.	[x] Align Codex config template with upstream model_providers schema; ensure profiles map to providers and defaults. COMMIT: 0816921499cd25a7634eb22d31eb04915d84fe8a
	9.	[x] Pass --profile through exec wrappers and smoke tests so automation selects the intended backend. COMMIT: 0816921499cd25a7634eb22d31eb04915d84fe8a
	10.	[x] Capture Codex --json traces for richer metrics (tokens, edits, command outcomes) and surface them in metrics.json/CSV. COMMIT: 0816921499cd25a7634eb22d31eb04915d84fe8a

Begin with M0. Keep commits small. Append commit hashes into milestone boxes as you go.
