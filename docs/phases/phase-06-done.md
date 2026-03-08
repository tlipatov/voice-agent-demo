# Phase 06 - Done

## Phase

- Number: `06`
- Name: RAG Loader Pipeline
- Date: 2026-03-06

## Implemented

- Implemented loader pipeline CLI in:
  - `services/rag_loader/src/loader.py`
- Added end-to-end ingest orchestration through embedding service API (`POST /v1/ingest`):
  - Per-tenant payload generation using `tenant_id`, `path`, `recursive`, `chunk_size`, `overlap`, `batch_size`, `reset_collection`.
  - Server normalization to support `--server` values like `embedding_service:8010` and full URLs.
  - Single-tenant mode (`--tenant`) and multi-tenant discovery mode (automatic discovery under `--path`).
  - Per-tenant result output with success/failure handling and non-zero exit on failures.
- Added CLI options required by the phase:
  - `--tenant`, `--path`, `--server`
  - Plus ingest endpoint options and related runtime controls: `--recursive/--no-recursive`, `--chunk-size`, `--overlap`, `--batch-size`, `--reset-collection`, `--timeout`.
- Updated container packaging:
  - `services/rag_loader/Dockerfile` now uses a direct loader entrypoint:
    - `python /app/services/rag_loader/src/loader.py`
- Updated service usage documentation:
  - `services/rag_loader/README.md`
  - Includes local CLI usage and containerized `docker run` example against compose network.
- Added tests for loader behavior:
  - `services/rag_loader/tests/test_loader.py`
  - Covers server normalization, target discovery behavior, single/multi-tenant flow, and ingest error handling.

## Docker + Make Checkpoint

- `rag_loader` Makefile remains aligned with project service build/push pattern:
  - `make build SERVICE=rag-loader`
  - `make push SERVICE=rag-loader`
- Loader container entrypoint is now runnable as CLI and can target `embedding_service` by service DNS name on compose network.

## Validation Performed

- Loader + tenant layout tests:
  - `.venv/bin/python -m unittest services/rag_loader/tests/test_tenant_layout.py services/rag_loader/tests/test_loader.py`
  - Result: PASS

## Acceptance Status

- Working ingestion pipeline and CLI entrypoint implemented: **PASS**
- Loader calls embedding service `/v1/ingest` (no local embedding runtime): **PASS**
- Required loader Docker + Make artifacts present and runnable: **PASS**
- Test coverage added for pipeline logic: **PASS**
