# Phase 06 - RAG Loader Pipeline

## Goal
Build ingestion from tenant documents into embedding service.

## Implementation Tasks
- Implement `services/rag_loader/src/loader.py`.
- Use embedding service /v1/ingest endpoint. For details look at `docs/phases/phase-00-05-embedding-service.md`
- Add CLI options: `--tenant <id>`  , `--path` `--server=embedding_service:port` and other options available to the /v1/ingest endpoint
- Add `services/rag_loader/README.md` with instructions how to use

## Deliverables
- Working ingestion pipeline and CLI entrypoint.
- `services/rag_loader/Dockerfile` and `services/rag_loader/Makefile` to package tool as a container. Use `services/embedding_service/Makefile` as example, make it same.

## Docker + Make Checkpoint
- Ensure loader container can reach `embedding_service` over compose network.
- Build/tag/push `docker.local.fyre.org/rag-loader:latest`.
- Validate ingestion via `docker run --rm rag_loader ...`.

## Acceptance
- Running loader populates `<tenant>_docs` with chunk embeddings.

## Testing

Add tests
