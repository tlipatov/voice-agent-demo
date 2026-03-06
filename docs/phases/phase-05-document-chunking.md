# Phase 05 - Document Chunking

## Goal
Implement deterministic chunking as part of embedding-service ingestion (not a standalone loader-local module).

## Depends On

- `docs/phases/phase-00-05-embedding-service.md`
- `docs/phases/phase-03-embedding-module.md`
- `docs/phases/phase-04-rag-data-layout.md`

## Implementation Tasks
- Implement chunking logic under the embedding service location:
  - `services/embedding_service/` (exact file name is implementation choice)
- Provide `chunk_document(text, chunk_size=500, overlap=50)` used by `POST /v1/ingest`.
- Prefer paragraph boundaries, fallback to smaller splits when needed.
- Return chunk records containing `chunk_id`, `text`, and metadata (`tenant_id`, `source_file`, `chunk_index`).
- Ensure chunking behavior aligns with the ingestion API contract documented in:
  - `docs/phases/phase-00-05-embedding-service.md`
  - `docs/phases/phase-00-05-done.md`

## Deliverables
- Deterministic chunking module/function integrated with embedding-service ingestion path.
- Test script (or unit tests) with sample outputs for embedding-service chunk preparation.

## Docker + Make Checkpoint
- Ensure chunking implementation is included in the `embedding-service` image.
- Validate chunking through embedding-service container execution path (ingestion endpoint flow).
- Build image with cd services/embedding_service && make build

## Acceptance
- Ingestion path produces valid chunks with complete metadata (`tenant_id`, `source_file`, `chunk_index`) before embedding/upsert.

## Testing
- Write pytests
- Launch the stack docker-compose up 
- Test and reitterate