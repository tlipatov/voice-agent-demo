# Phase 00.5 - Embedding Service

## Goal
Introduce a dedicated GPU-capable embedding service that owns model runtime (`sentence-transformers`) and exposes REST APIs for ingestion and query, so later phases (chunking, loader, CLI) integrate through a stable contract.

Sub-goals
- Runs as a container
- Built with a Makefile
- Built wit

## Position in Sequence

This phase is a prerequisite and must be implemented **after**:
- Phase 02 (`chromadb` service)
- Phase 03 (shared embedding module)
- Phase 04 (tenant data layout)

And **before**:
- Phase 05 (document chunking implementation details used by ingestion)
- Phase 06 (RAG loader pipeline integration)
- Phase 07 (RAG CLI integration)

## Non-Goals

- Do not move embedding model runtime into loader/CLI/gateway.
- Do not bypass API contracts by embedding directly in other services.
- Do not redefine tenant layout conventions from Phase 04.

## Preconditions and Dependencies

- ChromaDB reachable via `CHROMA_URL`.
- Shared package exists in `shared/embeddings/` from Phase 03.
- shared package is pip installable via Dockerfile
- Tenant documents available under `rag_data/<tenant_id>/...` from Phase 04.
- Runtime GPU support available for service container/host.

## Service Ownership Boundary

- `embedding_service` is the only runtime component that loads `sentence-transformers`.
- `rag_loader`, `rag_cli`, and `agent_gateway` call embedding-service REST endpoints.
- Shared embedding utilities remain in `shared/embeddings`, but runtime loading occurs through embedding-service process only.

## API Contract (for downstream phases)

### `GET /healthz`

Purpose:
- Basic health and readiness for service orchestration.

Expected response (example):

```json
{
  "status": "ok",
  "embedding_device": "cuda"
}
```

### `POST /v1/ingest`

Purpose:
- Trigger ingestion by path; reads files, chunks content, embeds chunks, upserts to Chroma collection `{tenant_id}_docs`.

Request body:

```json
{
  "tenant_id": "silver_pine",
  "path": "silver_pine",
  "recursive": true,
  "chunk_size": 500,
  "overlap": 50,
  "batch_size": 32,
  "reset_collection": false
}
```

Notes:
- `path` may be relative to `INGEST_ROOT` or absolute.
- Supported file types: `.md`, `.txt`, `.pdf`.
- Chunk metadata contract must include: `tenant_id`, `source_file`, `chunk_index`.

Successful response (example):

```json
{
  "tenant_id": "silver_pine",
  "collection": "silver_pine_docs",
  "documents_indexed": 2,
  "chunks_indexed": 16
}
```

Error behavior:
- `404` when path does not exist.
- `400` when no supported documents found or no chunks produced.
- `500` for unexpected processing/storage failures.

### `POST /v1/query`

Purpose:
- Query a tenant collection with semantic similarity and return ranked matches.

Request body:

```json
{
  "tenant_id": "silver_pine",
  "query": "What are your business hours?",
  "n_results": 5
}
```

Successful response (example):

```json
{
  "tenant_id": "silver_pine",
  "query": "What are your business hours?",
  "matches": [
    {
      "document": "We are open Monday through Friday ...",
      "metadata": {
        "tenant_id": "silver_pine",
        "source_file": "/app/rag_data/silver_pine/hours.md",
        "chunk_index": 0
      },
      "distance": 0.14
    }
  ]
}
```

## Runtime Configuration

- `CHROMA_URL` (example: `http://chromadb:8001`)
- `INGEST_ROOT` (example: `/app/rag_data`)
- `EMBEDDING_DEVICE` (`cuda` or `cpu`; default auto-detect)
- `EMBEDDING_REQUIRE_GPU` (`true`/`false`; fail startup if GPU required but unavailable)

## Chunking Requirements (handoff to Phase 05)

The ingestion endpoint must apply deterministic chunking rules that Phase 05 will formalize:
- paragraph-first splitting
- overlap support (`overlap`)
- stable chunk metadata (`tenant_id`, `source_file`, `chunk_index`)

Phase 05 should treat chunking as an embedding-service ingestion concern, not loader-local business logic.

## Integration Requirements for Phase 06 (Loader)

- Loader orchestrates ingestion by calling `POST /v1/ingest`.
- Loader is responsible for tenant discovery and triggering ingest per tenant/path.
- Loader should not embed locally with `sentence-transformers`.
- Loader acceptance should validate successful ingestion summaries from the API.

## Integration Requirements for Phase 07 (CLI)

- CLI `query` command must call `POST /v1/query`.
- CLI `list/inspect/delete` can use Chroma APIs directly unless later centralized.
- CLI should present query score/distance, source file, and metadata from API results.
- CLI should not load embedding model runtime locally.

## Docker + Make Checkpoint

- Add service directory and artifacts:
  - `services/embedding_service/`
  - `services/embedding_service/Makefile`
  - `services/embedding_service/README.md`
  - `services/embedding_service/Dockerfile`
- Add top-level Make support:
  - `make build SERVICE=embedding-service`
  - `make push SERVICE=embedding-service`
- Add compose service and runtime dependencies:
  - `embedding_service` depends on healthy `chromadb`
  - mount `rag_data` into embedding service
  - expose API port (project choice)
  - configure GPU runtime (project/environment specific)

## Acceptance

- Health endpoint returns `status=ok` and selected embedding device.
- Ingest endpoint indexes supported documents from path into `{tenant_id}_docs`.
- Query endpoint returns ranked matches with metadata for the requested tenant.
- Downstream phases (06/07) can be implemented against this API contract without embedding runtime duplication.

## Testing

- Add any necessery tests
- Look how we build docker/chromadb container if needed, do not reubild unless needed.
- Write a dockercompose to launch docker.local.fyre.org/chromadb:latest and embedding-service for testing
- Run chromadb container
- Run embedding-service container using CPU, perform ingest and query tests

Test and reitterate