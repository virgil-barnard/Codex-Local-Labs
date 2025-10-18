SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

COMPOSE ?= docker compose
COMPOSE_FILE := docker/compose.yml
ENABLE_VLLM ?= 0

ifeq ($(ENABLE_VLLM),1)
COMPOSE_PROFILES := --profile vllm
else
COMPOSE_PROFILES :=
endif

.PHONY: help build up down smoke bench harvest hfi-run hfi-publish

help:
	@echo "Available targets:"
	@echo "  make build        Build runner and optional vLLM images"
	@echo "  make up           Start docker compose stack"
	@echo "  make down         Stop docker compose stack and remove volumes"
	@echo "  make smoke        Run provider health checks"
	@echo "  make bench        Execute benchmark suite (requires SUITE, PROFILE)"
	@echo "  make harvest      Aggregate benchmark results"
	@echo "  make hfi-run      Perform a human feedback run"
	@echo "  make hfi-publish  Publish human feedback artifacts"

build:
	$(COMPOSE) -f $(COMPOSE_FILE) $(COMPOSE_PROFILES) build

up:
	$(COMPOSE) -f $(COMPOSE_FILE) $(COMPOSE_PROFILES) up -d

down:
	$(COMPOSE) -f $(COMPOSE_FILE) down -v

smoke:
        SMOKE_PROFILE=$(PROFILE) PROFILE=$(PROFILE) ./scripts/smoke.sh

bench:
	@test -n "$(SUITE)" || (echo "SUITE is required" >&2 && exit 1)
	@test -n "$(PROFILE)" || (echo "PROFILE is required" >&2 && exit 1)
	SUITE=$(SUITE) PROFILE=$(PROFILE) ./bench/harness/run_suite.sh

harvest:
	python -m bench.harness.harvest_metrics

hfi-run:
	@test -n "$(SUITE)" || (echo "SUITE is required" >&2 && exit 1)
	@test -n "$(PROFILE)" || (echo "PROFILE is required" >&2 && exit 1)
	SUITE=$(SUITE) PROFILE=$(PROFILE) ./scripts/hfi_run.sh

hfi-publish:
	./scripts/hfi_publish.sh
