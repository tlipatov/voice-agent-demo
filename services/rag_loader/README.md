# RAG Loader Service

## Purpose

`rag_loader` orchestrates tenant ingestion by calling the embedding service API:

- `POST /v1/ingest`

It does **not** load embedding models locally. It discovers tenants, builds ingest payloads, and reports per-tenant indexing results.

## CLI Entrypoint

- Script: `services/rag_loader/src/loader.py`

### Options

- `--tenant <id>`: ingest one tenant (if omitted, discover all tenant directories under `--path`)
- `--path <path>`: tenant root path for discovery or direct path for single-tenant ingest (default: `rag_data`)
- `--server <host:port|url>`: embedding service address (default: `embedding_service:8010`)
- `--recursive` / `--no-recursive`
- `--chunk-size <int>`
- `--overlap <int>`
- `--batch-size <int>`
- `--reset-collection`
- `--timeout <seconds>`

### Examples

Ingest all tenants under `rag_data/`:

```bash
python services/rag_loader/src/loader.py --path rag_data --server http://localhost:8010
```

Ingest one tenant and reset collection:

```bash
python services/rag_loader/src/loader.py \
  --tenant silver_pine \
  --path rag_data \
  --server embedding_service:8010 \
  --reset-collection
```

## Container Usage

Build and push (from repository root):

```bash
make build SERVICE=rag-loader
make push SERVICE=rag-loader
```

Run with compose network service name:

```bash
docker run --rm \
  --network voice-agent-demo_default \
  -v "$(pwd)/rag_data:/app/rag_data:ro" \
  docker.local.fyre.org/rag-loader:latest \
  --path /app/rag_data \
  --server embedding_service:8010
```
