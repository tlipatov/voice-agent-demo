# Phase 12 Done - RAG Retrieval Service

## What Was Built

`services/agent_gateway/src/rag_retrieval.py` — a lightweight retrieval client that calls the embedding service `POST /v1/query` endpoint and returns ranked, tenant-isolated document snippets.

### Public API

```python
from services.agent_gateway.src.rag_retrieval import RagClient, RagMatch, RagRetrievalError

client = RagClient()                          # reads EMBEDDING_SERVICE_URL env var
client = RagClient(base_url="http://...:8010")  # explicit URL

matches: list[RagMatch] = client.query(
    tenant_id="silver_pine",
    query="appointment scheduling",
    n_results=5,                              # defaults to 5
)

# Each RagMatch:
#   match.document  - snippet text
#   match.metadata  - {"tenant_id": ..., "source_file": ..., "chunk_index": ...}
#   match.distance  - float (lower = more similar)
```

### Error Handling

| Condition | Exception |
|---|---|
| Service unreachable / HTTP error | `RagRetrievalError` |
| Malformed JSON response | `RagRetrievalError` |
| Empty `tenant_id` or `query` | `ValueError` |
| `n_results < 1` | `ValueError` |

## Infrastructure

`services/agent_gateway/docker-compose.yml` already connects to the external `embedding_service_net` network, so `http://embedding_service:8010` is reachable without changes.

## Tests

E2E tests added to `services/agent_gateway/tests/test_e2e.py` — class `RagRetrievalE2ETests`:

| Test method | What it verifies |
|---|---|
| `test_query_returns_list` | `client.query()` always returns a `list` (empty is fine if collection not ingested) |
| `test_query_results_are_tenant_isolated` | Every returned `RagMatch.metadata["tenant_id"]` matches the requested tenant |
| `test_query_result_fields` | Each match has non-empty `document` str, `metadata` dict, and float `distance` |
| `test_query_respects_n_results` | Number of returned matches does not exceed the requested `n_results` |
| `test_query_different_tenants_are_isolated` | Results for `silver_pine` contain no `smith_law` entries and vice versa |
| `test_unreachable_service_raises_retrieval_error` | A bad base URL raises `RagRetrievalError` (not an unhandled exception) |
| `test_empty_query_raises_value_error` | Passing `query=""` raises `ValueError` before any network call |
| `test_empty_tenant_raises_value_error` | Passing `tenant_id=""` raises `ValueError` before any network call |

All tests in `RagRetrievalE2ETests` skip gracefully when the embedding service is not reachable.

### Running Tests

```bash
cd services/agent_gateway
make test          # brings up docker-compose, runs all tests
```
