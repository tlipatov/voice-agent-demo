# Phase 17 - Docker Compose

## Goal
Orchestrate all services with a single compose file.

## Implementation Tasks
- Create `docker/docker-compose.yml`.
- Add services: `agent_gateway`, `chromadb`, `vllm`, `redis`.
- Configure env vars, volumes, healthchecks, and dependencies.
- Add GPU assignment strategy for `vllm` and optional `chromadb`.

## Deliverables
- Compose file and `.env` example for local stack.

## Docker + Make Checkpoint
- Add `make run`, `make down`, `make logs` wrappers for compose commands.
- Confirm compose references images in `docker.local.fyre.org/...:latest` or local builds.

## Acceptance
- `docker compose up` starts healthy multi-service system.
