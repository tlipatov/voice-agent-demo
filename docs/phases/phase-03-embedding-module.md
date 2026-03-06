# Phase 03 - Embedding Module

## Goal
Implement shared embedding utilities for single and batch text embedding.

## Implementation Tasks
- Create `shared/embeddings/embedding_model.py`.
- Implement `load_embedding_model()`, `embed_text(text)`, `embed_documents(list_of_text)`.
- Use `sentence-transformers/all-MiniLM-L6-v2`.
- Add lightweight tests for shape and non-empty output.
- These are python libraries that care pip installed

## Deliverables
- Reusable embedding module.
- Tests for core embedding calls.

## Docker + Make Checkpoint
- Ensure module is available inside `rag-loader`, `rag-cli`, and `agent-gateway` images via pip install
- Rebuild impacted images with `make build`.

## Acceptance
- `embed_text("Hello world")` returns a vector embedding in containerized runtime.
