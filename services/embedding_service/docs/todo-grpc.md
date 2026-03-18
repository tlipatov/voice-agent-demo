# TODO: Add gRPC `/v1/query` to embedding_service

## Context

`services/embedding_service` is a FastAPI/uvicorn service (port 8010) that exposes:
- `GET /healthz`
- `POST /v1/ingest`
- `POST /v1/query` — embeds the query text, queries the tenant's ChromaDB collection, returns ranked matches

We want to expose **query only** over gRPC for low-latency RAG calls. The REST API must remain unchanged. The core query logic in `app.py::query_documents` should be reused directly — do not duplicate it.

---

## Files to create

### `proto/embedding.proto`

Define the protobuf service and messages. Place it at `services/embedding_service/proto/embedding.proto`.

```
service EmbeddingService {
  rpc Query (QueryRequest) returns (QueryResponse);
}

message QueryRequest {
  string tenant_id = 1;
  string query     = 2;
  int32  n_results = 3;   // default 5, range 1–50
}

message QueryResponse {
  string tenant_id = 1;
  string query     = 2;
  repeated Match matches = 3;
}

message Match {
  string document = 1;
  map<string, string> metadata = 2;  // all values serialized as strings
  float distance = 3;
}
```

Notes:
- ChromaDB metadata values are strings, ints, or floats. Serialize all as strings in the proto map to keep it simple.
- `distance` should be 0.0 when absent (proto3 default).

### `grpc_server.py`

A standalone module at `services/embedding_service/grpc_server.py` that:

1. Imports the generated stubs from `proto/`.
2. Implements `EmbeddingServiceServicer.Query`:
   - Validates `tenant_id` (non-empty) and `query` (non-empty); return `grpc.StatusCode.INVALID_ARGUMENT` on failure.
   - Clamps `n_results` to range [1, 50]; default to 5 if 0.
   - Calls the shared helper `_do_query(tenant_id, query, n_results)` (see `app.py` refactor below).
   - Maps the result dicts to `Match` proto messages.
   - Returns `QueryResponse`.
3. Exposes a `serve(port: int)` function that creates a `grpc.server`, adds the servicer, and calls `server.start()` / `server.wait_for_termination()`.
4. When run as `__main__`, reads `GRPC_PORT` env var (default `50051`) and calls `serve()`.

### `proto/__init__.py`

Empty file so the `proto/` package is importable.

---

## Files to modify

### `requirements.txt`

Add:
```
grpcio
grpcio-tools
```

### `app.py`

Refactor the query logic out of the FastAPI handler into a shared private function so `grpc_server.py` can reuse it without importing FastAPI internals:

```python
def _do_query(tenant_id: str, query: str, n_results: int) -> dict:
    """Core query logic. Returns the same dict shape as the REST response."""
    client = _chroma_client()
    collection = client.get_or_create_collection(_collection_name(tenant_id))
    query_embedding = embed_text(query)
    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]
    matches = []
    for idx, doc in enumerate(documents):
        matches.append({
            "document": doc,
            "metadata": metadatas[idx] if idx < len(metadatas) else {},
            "distance": distances[idx] if idx < len(distances) else None,
        })
    return {"tenant_id": tenant_id, "query": query, "matches": matches}
```

Then update `query_documents` to delegate to `_do_query`. No change to the REST contract.

### `Dockerfile`

1. Add a `RUN` step to compile the proto **before** copying application code:
   ```dockerfile
   COPY services/embedding_service/proto /app/services/embedding_service/proto
   RUN python -m grpc_tools.protoc \
       -I /app/services/embedding_service/proto \
       --python_out=/app/services/embedding_service/proto \
       --grpc_python_out=/app/services/embedding_service/proto \
       /app/services/embedding_service/proto/embedding.proto
   ```
2. Expose gRPC port: `EXPOSE 50051`
3. Change `CMD` to launch both servers. The simplest approach is a small `entrypoint.sh` shell script that starts `grpc_server.py` in the background then launches uvicorn in the foreground:
   ```bash
   #!/bin/sh
   python grpc_server.py &
   exec uvicorn app:app --host 0.0.0.0 --port 8010
   ```
   Add `COPY services/embedding_service/entrypoint.sh /app/services/embedding_service/entrypoint.sh` and `RUN chmod +x ...` and update `CMD` accordingly.

### `docker-compose.yml`

Add the gRPC port mapping to the `embedding_service` service:
```yaml
ports:
  - "8010:8010"
  - "50051:50051"
```

Add env var:
```yaml
environment:
  - GRPC_PORT=50051
```

### `Makefile`

No structural changes required. The existing `e2e-test` target runs `tests/test_e2e.py`; add the gRPC test file to the same test run (see below).

Update:
```makefile
e2e-test:
	@set -e; \
	$(COMPOSE) up -d; \
	trap '$(COMPOSE) down' EXIT; \
	python3 -m unittest tests/test_e2e.py tests/test_grpc_e2e.py
```

---

## Files to create (tests)

### `tests/test_grpc_e2e.py`

End-to-end test that:
1. Waits for gRPC port to be reachable (with a timeout loop, similar to `_wait_for_service_ready` in `test_e2e.py`).
2. Creates a `grpc.insecure_channel("localhost:50051")` and a stub.
3. Requires that ingest has already run (call REST ingest for `silver_pine` in `setUpClass`, same as `test_e2e.py`).
4. Calls `stub.Query(QueryRequest(tenant_id="silver_pine", query="What are your business hours?", n_results=3))`.
5. Asserts:
   - `response.tenant_id == "silver_pine"`
   - `response.query == "What are your business hours?"`
   - `len(response.matches) > 0`
   - `response.matches[0].metadata["tenant_id"] == "silver_pine"`
   - `response.matches[0].distance` is a finite float
6. Tests error case: empty `tenant_id` or `query` returns `grpc.RpcError` with `INVALID_ARGUMENT`.

---

## Implementation order

1. Add `grpcio` and `grpcio-tools` to `requirements.txt`.
2. Write `proto/embedding.proto`.
3. Refactor `_do_query` out of `app.py`.
4. Write `grpc_server.py`.
5. Write `entrypoint.sh`.
6. Update `Dockerfile` (proto compile step + entrypoint).
7. Update `docker-compose.yml` (port + env).
8. Write `tests/test_grpc_e2e.py`.
9. Update `Makefile` e2e-test target.
10. Run `make test` and confirm both REST and gRPC tests pass.

---

## Constraints

- Do not remove or modify any existing REST endpoint.
- Do not add gRPC for ingest — query only.
- The generated proto stubs (`*_pb2.py`, `*_pb2_grpc.py`) must be committed; do not rely on a build step outside Docker.
- Use `grpc.server(futures.ThreadPoolExecutor(max_workers=4))` — the embedding model is already loaded at startup, calls are CPU/GPU bound and thread-safe.
- Port `50051` is the gRPC port. Make it configurable via `GRPC_PORT` env var.
