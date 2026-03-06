# Embedding Service

## Purpose

`embedding_service` provides GPU-backed embedding + vector operations over REST:

- ingest documents from a path into ChromaDB
- query tenant collections by semantic similarity

This service is the only runtime component that should load `sentence-transformers`.

## REST API

- `GET /healthz`
- `POST /v1/ingest`
  - body: `tenant_id`, `path`, `recursive`, `chunk_size`, `overlap`, `batch_size`, `reset_collection`
- `POST /v1/query`
  - body: `tenant_id`, `query`, `n_results`

## Runtime Configuration

- `CHROMA_URL` (default: `http://chromadb:8001`)
- `INGEST_ROOT` (default: `/app/rag_data`)
- `EMBEDDING_DEVICE` (default: auto-detect, prefers `cuda`)
- `EMBEDDING_REQUIRE_GPU` (default: `false`)

## Image Build/Push

From repository root:

```bash
make build SERVICE=embedding-service
make push SERVICE=embedding-service
```

## Local Smoke Test (CPU)

Start ChromaDB + embedding service:

```bash
docker compose -f docker/docker-compose.embedding-service.yml up -d
```

Health check:

```bash
curl http://localhost:8010/healthz
```
