# Phase 00.5 - Done

## Phase

- Number: `00-05`
- Name: Embedding Service
- Date: 2026-03-06

## Implemented

- Added and completed the dedicated `embedding_service` runtime boundary in `services/embedding_service/app.py`:
  - `GET /healthz` returns `status` and selected embedding device.
  - `POST /v1/ingest` ingests `.md`, `.txt`, and `.pdf` files from `INGEST_ROOT`-relative or absolute paths.
  - `POST /v1/query` returns ranked tenant matches with metadata and distance.
- Enforced contract guardrails and deterministic behavior:
  - Added request validation for `overlap < chunk_size`.
  - Implemented paragraph-first chunking with deterministic fallback splitting for oversized paragraphs.
  - Preserved stable chunk metadata (`tenant_id`, `source_file`, `chunk_index`).
- Added service tests:
  - `services/embedding_service/tests/test_app.py`
  - Covers `healthz`, ingest validation, ingest upsert flow, query match shaping, and chunking behavior.
- Updated shared embedding test compatibility:
  - `shared/embeddings/tests/test_embedding_model.py` now supports `SentenceTransformer(..., device=...)` construction.
- Fixed Python compatibility for shared embedding package used by the embedding-service image:
  - `shared/embeddings/pyproject.toml` -> `requires-python = ">=3.10"`
- Added dedicated CPU integration compose file for this phase:
  - `docker/docker-compose.embedding-service.yml`
  - Runs only `chromadb` + `embedding_service`, mounts `rag_data`, and sets CPU runtime env.
- Updated service docs:
  - `services/embedding_service/README.md` with local CPU smoke-test instructions.
- Resolved a runtime startup regression discovered during compose testing:
  - Root cause: stale `*.egg-info` metadata from `shared/embeddings` was copied into Docker build context and caused unconstrained dependency resolution (`sentence-transformers 5.x` + `transformers 5.x`) against `torch 2.2.2`.
  - Pinned shared embedding runtime deps in `shared/embeddings/pyproject.toml`:
    - `sentence-transformers==2.7.0`
    - `transformers==4.41.2`
  - Hardened image packaging in `services/embedding_service/Dockerfile` by copying only `pyproject.toml`, `README.md`, and `embedding_model.py` from `shared/embeddings`.
  - Added build-artifact ignores in `.dockerignore`:
    - `*.egg-info`
    - `build`

## ChromaDB Integration Corrections

To keep embedding-service integration working against current Chroma versions:

- Updated Chroma container command in `docker/chromadb/Dockerfile`:
  - `chromadb run ...` -> `chroma run ...`
- Updated heartbeat checks to v2 endpoint:
  - `docker/docker-compose.yml`
  - `docker/docker-compose.embedding-service.yml`
  - `docker/chromadb/README.md`
  - `docs/phases/phase-02-chromadb-service.md`
  - `docs/phases/phase-02-done.md`
  - `docs/TODO.md`
  - Endpoint: `http://localhost:8001/api/v2/heartbeat`

## Docker + Make Checkpoint

- Embedding service image build verified from service directory:
  - `cd services/embedding_service && make build`
- Dedicated test compose file added for this phase:
  - `docker-compose -f docker/docker-compose.embedding-service.yml up -d`

## Validation Performed

- Unit tests (embedding service):
  - `.venv/bin/python -m unittest services/embedding_service/tests/test_app.py`
  - Result: `Ran 5 tests ... OK`
- Unit tests (shared embeddings):
  - `PYTHONPATH=shared/embeddings .venv/bin/python -m unittest shared/embeddings/tests/test_embedding_model.py`
  - Result: `Ran 3 tests ... OK`
- Embedding service image build:
  - `make build` (from `services/embedding_service/`)
  - Result: PASS
- Compose startup (phase-specific stack):
  - `docker-compose -f docker/docker-compose.embedding-service.yml up -d`
  - Result: `chromadb` and `embedding_service` containers started
- Compose startup (service-level stack after dependency fix):
  - `cd services/embedding_service && docker-compose up -d`
  - Result: `embedding_service` reached `Application startup complete` and served `uvicorn` on port `8010`

## Acceptance Status

- Health endpoint contract implemented: **PASS**
- Ingest endpoint contract implemented (including `.pdf`): **PASS**
- Query endpoint contract implemented with ranked matches + metadata: **PASS**
- Dedicated embedding runtime ownership boundary enforced: **PASS**
- Docker + Make integration for embedding-service: **PASS**
- Phase-specific compose for CPU integration testing: **PASS**
