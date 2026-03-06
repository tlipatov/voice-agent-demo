# Phase 06 - RAG Loader Pipeline

## Goal
Build ingestion from tenant documents into ChromaDB collections.

## Implementation Tasks
- Implement `services/rag_loader/loader.py`.
- Flow: discover tenant -> load document -> chunk -> embed -> write to Chroma.
- Add CLI options: `--tenant <id>` and optional `--all`.
- Add parser support for `.md`, `.txt`, `.pdf` (PDF parsing included).
- Add ingestion summary output (files, chunks, errors).
- Make chromadb server host and port configureable

## Deliverables
- Working ingestion pipeline and CLI entrypoint.

## Docker + Make Checkpoint
- Ensure loader container can reach `chromadb` over compose network.
- Build/tag/push `docker.local.fyre.org/rag-loader:latest`.
- Validate ingestion via `docker compose run --rm rag_loader ...`.

## Acceptance
- Running loader populates `<tenant>_docs` with chunk embeddings.
