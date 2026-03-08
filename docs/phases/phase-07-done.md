# Phase 07 - Done

## Phase

- Number: `07`
- Name: RAG CLI Tool
- Date: 2026-03-08

## Implemented

- Implemented a functional Typer-based unified CLI in:
  - `services/rag_cli/src/cli.py`
- Added required command set:
  - `list`
  - `query --tenant <id> --query "<text>"`
  - `inspect --tenant <id>`
  - `delete --tenant <id>`
- Incorporated loader functionality into this CLI with:
  - `ingest [--tenant <id>] --path --server --recursive/--no-recursive --chunk-size --overlap --batch-size --reset-collection --timeout`
  - Multi-tenant discovery mode and single-tenant explicit mode.
- Query command integrates via embedding-service REST API:
  - `POST /v1/query`
  - Output includes result text, source file, metadata, distance, and computed score.
- Collection inspection and management commands implemented against Chroma:
  - Collection listing, tenant collection metadata inspection, and delete workflow with confirmation support.
- Updated container packaging for executable CLI image:
  - `services/rag_cli/Dockerfile` now uses:
    - `python /app/services/rag_cli/src/cli.py`
- Updated CLI usage documentation:
  - `services/rag_cli/README.md`
  - Includes local usage, one-shot Docker examples, and test commands.
- Added tests:
  - `services/rag_cli/tests/test_cli.py`
    - Covers list/query/inspect/delete/ingest command behavior.
  - `services/rag_cli/tests/test_e2e.py`
    - Containerized end-to-end harness for `ingest` + `query` against embedding service.
    - Guarded by `RUN_RAG_CLI_E2E=1`.

## Docker + Make Checkpoint

- `rag_cli` service artifacts are present and aligned with project conventions:
  - `services/rag_cli/Makefile`
  - `services/rag_cli/Dockerfile`
  - Image tag target: `docker.local.fyre.org/rag-cli:latest`
- One-shot CLI container run examples are documented in `services/rag_cli/README.md`.

## Validation Performed

- Unit tests:
  - `.venv/bin/python -m unittest services/rag_cli/tests/test_cli.py`
  - Result: PASS
- E2E test harness execution (default behavior):
  - `.venv/bin/python -m unittest services/rag_cli/tests/test_e2e.py`
  - Result: PASS (skipped by default unless `RUN_RAG_CLI_E2E=1`)

## Acceptance Status

- Functional `rag_cli` command set implemented: **PASS**
- Query operations run through embedding-service REST API: **PASS**
- Loader functionality unified into `rag_cli` via `ingest`: **PASS**
- Usage docs and Docker one-shot examples added: **PASS**
- Tests added (unit + e2e harness): **PASS**
