# Phase 01 - Done

## Phase

- Number: `01`
- Name: Repository Setup
- Date: 2026-03-05

## Implemented

- Created baseline project structure under:
  - `services/agent_gateway/`
  - `services/rag_loader/`
  - `services/rag_cli/`
  - `services/tools/`
  - `shared/embeddings/`
  - `shared/schemas/`
  - `configs/tenants/`
  - `docker/`
  - `scripts/`
  - `rag_data/`
- Added package markers:
  - `services/__init__.py`
  - `services/agent_gateway/__init__.py`
  - `services/rag_loader/__init__.py`
  - `services/rag_cli/__init__.py`
  - `services/tools/__init__.py`
  - `shared/__init__.py`
  - `shared/embeddings/__init__.py`
  - `shared/schemas/__init__.py`
- Added `requirements.txt` with the Phase 01 package list.
- Added `.env.example` with:
  - `CHROMA_URL`
  - `REDIS_URL`
  - `VLLM_URL`
- Added setup documentation in `docs/setup.md`.
- Updated `README.md` with a local setup section pointing to `docs/setup.md`.

## Docker + Make Checkpoint

- Added `Makefile` targets:
  - `make build SERVICE=<service>`
  - `make push SERVICE=<service>`
  - `make release SERVICE=<service>`
  - `make list-services`
- Added per-service `Makefile`s:
  - `services/agent_gateway/Makefile`
  - `services/rag_loader/Makefile`
  - `services/rag_cli/Makefile`
  - `services/tools/Makefile`
- Added service Dockerfiles:
  - `services/agent_gateway/Dockerfile`
  - `services/rag_loader/Dockerfile`
  - `services/rag_cli/Dockerfile`
  - `services/tools/Dockerfile`
- Added per-service dependency files and switched Dockerfiles to use them:
  - `services/agent_gateway/requirements.txt`
  - `services/rag_loader/requirements.txt`
  - `services/rag_cli/requirements.txt`
  - `services/tools/requirements.txt`
- Added `.dockerignore` to prevent local virtualenv and dev artifacts from being copied into images.
- Added initial compose skeleton: `docker/docker-compose.yml`.
- Verified build target wiring with:
  - `make -n build SERVICE=agent-gateway`
  - `make -n push SERVICE=agent-gateway`
  - Result: top-level targets delegate to per-service `Makefile`s and preserve image naming `docker.local.fyre.org/[service]:latest`.

## Validation Performed

- Virtual environment creation:
  - `python3 -m venv .venv`
- Dependency install:
  - `pip install -r requirements.txt`
  - Result: success (exit code `0`)
- Import smoke test:
  - `python -c "import fastapi, chromadb, typer; print('dependencies-ok')"`
  - Result: printed `dependencies-ok`

## Acceptance Status

- Fresh clone dependency install: **PASS**
- Python environment and key imports: **PASS**
- Project structure created: **PASS**
