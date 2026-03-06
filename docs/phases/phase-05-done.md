# Phase 05 - Done

## Phase

- Number: `05`
- Name: Document Chunking
- Date: 2026-03-06

## Implemented

- Added a dedicated deterministic chunking module for embedding-service ingestion:
  - `services/embedding_service/chunking.py`
  - Exposes `chunk_document(text, chunk_size=500, overlap=50, ...)`.
- Implemented paragraph-first chunk preparation with deterministic fallback splitting for oversized paragraphs:
  - Prefers paragraph grouping when possible.
  - Falls back to sentence/word-based splitting for long paragraphs.
  - Applies stable overlap behavior between consecutive chunks.
- `chunk_document(...)` now returns chunk records with the required shape:
  - `chunk_id`
  - `text`
  - `metadata` containing `tenant_id`, `source_file`, `chunk_index`
- Integrated chunking into `POST /v1/ingest` in:
  - `services/embedding_service/app.py`
  - Ingestion now uses chunk records from `chunk_document(...)` before embedding + Chroma upsert.
- Added/updated tests to validate chunk preparation and ingest integration:
  - `services/embedding_service/tests/test_chunking.py`
  - `services/embedding_service/tests/test_app.py`

## Docker + Make Checkpoint

- Verified embedding-service image build from service directory:
  - `cd services/embedding_service && make build`
  - Result: PASS (`docker.local.fyre.org/embedding-service:latest` built successfully)

## Validation Performed

- Embedding service unit tests (including new chunking tests):
  - `.venv/bin/python -m unittest services/embedding_service/tests/test_app.py services/embedding_service/tests/test_chunking.py`
  - Result: `Ran 7 tests ... OK`
- Ingest-path metadata contract validation:
  - Verified via `test_ingest_indexes_documents_and_chunks` that upsert metadata includes `tenant_id` and `chunk_index`.

## Acceptance Status

- Deterministic chunking implemented in embedding-service ingestion path: **PASS**
- Paragraph-first behavior with deterministic fallback splits: **PASS**
- Chunk metadata contract (`tenant_id`, `source_file`, `chunk_index`): **PASS**
- Test coverage for chunk preparation outputs and ingestion integration: **PASS**
