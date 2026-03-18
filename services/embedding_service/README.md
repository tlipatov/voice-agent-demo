# Embedding Service

## Purpose

`embedding_service` provides GPU-backed embedding + vector operations over REST and gRPC:

- ingest documents from a path into ChromaDB (REST)
- query tenant collections by semantic similarity (REST + gRPC)

This service is the only runtime component that should load `sentence-transformers`.

## REST API

- `GET /healthz`
- `POST /v1/ingest`
  - body: `tenant_id`, `path`, `recursive`, `chunk_size`, `overlap`, `batch_size`, `reset_collection`
- `POST /v1/query`
  - body: `tenant_id`, `query`, `n_results`

## gRPC API

- `EmbeddingService.Query`
  - request: `tenant_id`, `query`, `n_results`
  - response: `tenant_id`, `query`, `matches[]`
- proto: `proto/embedding.proto`
- default gRPC port: `50051`

## Runtime Configuration

- `CHROMA_URL` (default: `http://chromadb:8001`)
- `INGEST_ROOT` (default: `/app/rag_data`)
- `EMBEDDING_DEVICE` (default: auto-detect, prefers `cuda`)
- `EMBEDDING_REQUIRE_GPU` (default: `false`)
- `GRPC_PORT` (default: `50051`)

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

gRPC query check (`grpcurl` example):

```bash
grpcurl -plaintext -d '{"tenant_id":"silver_pine","query":"What are your business hours?","n_results":3}' localhost:50051 EmbeddingService/Query
```
