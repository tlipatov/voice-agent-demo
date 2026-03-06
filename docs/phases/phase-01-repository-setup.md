# Phase 01 - Repository Setup

## Goal
Create the baseline project structure and Python dependency setup for all services.

## Implementation Tasks
- Create directories from the TODO plan under `services/`, `shared/`, `configs/`, `docker/`, `scripts/`, and `rag_data/`.
- Add `requirements.txt` with all listed packages.
- Add `.env.example` with service URLs (`CHROMA_URL`, `REDIS_URL`, `VLLM_URL`).
- Add setup instructions for virtualenv and install.

## Deliverables
- Repository skeleton committed.
- `requirements.txt` install succeeds.
- Setup instructions documented.

## Docker + Make Checkpoint
- Ensure service folders align with image naming convention for `docker.local.fyre.org/[service]:latest`.
- Confirm `make build SERVICE=<service>` delegates to and builds from each service `Makefile`.
- Confirm each service container installs dependencies from its own `services/<service>/requirements.txt`.

## Acceptance
- Fresh clone can install dependencies and import key modules.
