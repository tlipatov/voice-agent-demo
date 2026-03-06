# Phase 03 - Embedding Module

## Goal
Provide a reusable shared embeddings package consumed by the embedding-service runtime.

## Implementation Tasks
- Keep core module at `shared/embeddings/embedding_model.py`.
- Implement and maintain:
  - `load_embedding_model()`
  - `embed_text(text)`
  - `embed_documents(list_of_text)`
- Use model `sentence-transformers/all-MiniLM-L6-v2`.
- Document and preserve runtime behavior:
  - device selection via `EMBEDDING_DEVICE` when provided
  - automatic CUDA detection with CPU fallback when unset
  - optional hard GPU requirement via `EMBEDDING_REQUIRE_GPU=true`
- Add lightweight tests for output shape and non-empty vectors.

## Deliverables
- Shared embeddings library:
  - `shared/embeddings/embedding_model.py`
  - `shared/embeddings/pyproject.toml`
  - `shared/embeddings/README.md`
- Tests under `shared/embeddings/tests/`.

## Ownership Boundary
- `sentence-transformers` runtime loading belongs to `embedding_service` only.
- Other services must consume embedding/query behavior through embedding-service REST APIs rather than loading model runtime directly.

## Docker + Make Checkpoint
- Ensure `services/embedding_service` installs `shared/embeddings` via pip during image build.
- Rebuild impacted image with `make build SERVICE=embedding-service`.

## Acceptance
- `embed_text("Hello world")` returns a vector embedding in containerized embedding-service runtime.
