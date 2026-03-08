# RAG CLI Service

## Purpose

`rag_cli` provides command-line utilities for ingestion, vector DB inspection, and retrieval testing without running the full agent flow.

## Responsibilities

- List available tenant collections.
- Run semantic queries against tenant collections via embedding-service `POST /v1/query`.
- Inspect chunk metadata for debugging.
- Support operational tasks like collection cleanup.
- Trigger ingestion via embedding-service `POST /v1/ingest` (loader functionality unified in this tool).

## CLI Entrypoint

- Script: `services/rag_cli/src/cli.py`

### Commands

- `list [--chroma-url <url>]`
- `query --tenant <id> --query "<text>" [--server <host:port|url>] [--n-results <int>]`
- `inspect --tenant <id> [--limit <int>] [--chroma-url <url>]`
- `delete --tenant <id> [--yes] [--chroma-url <url>]`
- `ingest [--tenant <id>] [--path <path>] [--server <host:port|url>] ...`

### Local Examples

```bash
python services/rag_cli/src/cli.py list --chroma-url http://localhost:8001
python services/rag_cli/src/cli.py ingest --tenant silver_pine --path rag_data --server http://localhost:8010
python services/rag_cli/src/cli.py query --tenant silver_pine --query "What are your business hours?" --server http://localhost:8010
python services/rag_cli/src/cli.py inspect --tenant silver_pine --chroma-url http://localhost:8001
python services/rag_cli/src/cli.py delete --tenant silver_pine --yes --chroma-url http://localhost:8001
```

## Image Build/Push

From repository root:

```bash
make build SERVICE=rag-cli
make push SERVICE=rag-cli
```

## One-shot Container Examples

Ingest from mounted `rag_data`:

```bash
docker run --rm \
  --network embedding_service_default \
  -v "$(pwd)/rag_data:/app/rag_data:ro" \
  docker.local.fyre.org/rag-cli:latest \
  ingest --tenant silver_pine --path /app/rag_data --server embedding_service:8010
```

Query from container:

```bash
docker run --rm \
  --network embedding_service_default \
  docker.local.fyre.org/rag-cli:latest \
  query --tenant silver_pine --query "What are your business hours?" --server embedding_service:8010
```

List collections:

```bash
docker run --rm \
  --network embedding_service_default \
  docker.local.fyre.org/rag-cli:latest \
  list --chroma-url http://chromadb:8001
```

## Tests

Run unit tests:

```bash
python -m unittest services/rag_cli/tests/test_cli.py
```

Run optional containerized e2e test (requires running embedding service + image built):

```bash
RUN_RAG_CLI_E2E=1 python -m unittest services/rag_cli/tests/test_e2e.py
```
