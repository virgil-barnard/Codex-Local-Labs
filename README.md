# Codex Local Labs

Codex Local Labs provides a reproducible workspace for running the OpenAI Codex CLI against local
LLM providers such as Ollama and vLLM. The project ships with Docker tooling, benchmark harnesses,
and a human-feedback loop so maintainers can compare model performance on repeatable tasks.

## Prerequisites

- Docker Engine 24+
- Docker Compose plugin
- Python 3.11 (for local tooling)
- GNU Make

## Quickstart

1. Clone the repository and change into the project directory.
2. Copy provider environment templates from `docker/profiles` and populate them with base URLs
   and API keys.
3. Build container images:

   ```bash
   make build
   ```

4. Launch the stack (set `ENABLE_VLLM=1` to include the optional GPU service):

   ```bash
   make up
   ```

5. Run health checks to confirm providers and Codex are reachable:

   ```bash
   make smoke
   ```

6. Execute a benchmark suite from inside the runner container:

   ```bash
   make bench SUITE=python_katas PROFILE=ollama
   ```

7. Aggregate metrics for completed runs:

   ```bash
   make harvest
   ```

8. To perform a human-feedback run and publish results:

   ```bash
   make hfi-run SUITE=python_katas PROFILE=ollama
   make hfi-publish
   ```

   To append new manual-run requests or reconcile the queue with published
   results, use the queue management CLI:

   ```bash
   python -m bench.repo_ops.queue_cli add --suite python_katas --profile ollama --notes "Try new baseline"
   python -m bench.repo_ops.queue_cli list
   python -m bench.repo_ops.queue_cli reconcile
   ```

9. When finished, tear down the stack and remove volumes:

   ```bash
   make down
   ```

## Project Layout

Refer to `AGENTS.md` for the authoritative roadmap and milestones.
