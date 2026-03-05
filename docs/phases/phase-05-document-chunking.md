# Phase 05 - Document Chunking

## Goal
Create paragraph-first chunking with overlap and metadata.

## Implementation Tasks
- Implement `services/rag_loader/chunker.py`.
- Add `chunk_document(text, chunk_size=500, overlap=50)`.
- Prefer paragraph boundaries, fallback to smaller splits when needed.
- Return chunk records containing `chunk_id`, `text`, and metadata (`tenant_id`, `source_file`, `chunk_index`).

## Deliverables
- Deterministic chunking module.
- Test script with sample outputs.

## Docker + Make Checkpoint
- Ensure chunker is included in `rag-loader` image.
- Validate chunking in container execution path.

## Acceptance
- Chunking script prints valid chunks with complete metadata.
