# Phase Refactor 03 - Done

## Refactor

- Number: `03`
- Date: 2026-03-06
- Source: `docs/phases/phase-03-refactor.md`

## What Was Updated

- Updated `docs/phases/phase-03-embedding-module.md` to align with delivered behavior and packaging:
  - clarified Phase 03 as a shared package used by embedding-service runtime
  - documented model/device behavior:
    - `sentence-transformers/all-MiniLM-L6-v2`
    - `EMBEDDING_DEVICE` override
    - CUDA auto-detect with CPU fallback
    - `EMBEDDING_REQUIRE_GPU=true` hard requirement
  - added explicit package deliverables:
    - `shared/embeddings/pyproject.toml`
    - `shared/embeddings/README.md`
  - corrected wording/typos in implementation tasks
  - updated checkpoint to require pip install of `shared/embeddings` in `embedding_service` image build

## Cross-Phase Alignment Applied

- Updated `docs/phases/phase-06-rag-loader-pipeline.md`:
  - loader flow now references embedding-service ingest API usage
  - network/config checkpoint updated to include embedding-service endpoint
- Updated `docs/phases/phase-07-rag-cli-tool.md`:
  - query operations now reference embedding-service REST APIs
  - corrected endpoint/config wording typos
- Updated `docs/phases/phase-12-rag-retrieval-service.md`:
  - query embedding step now references embedding-service REST usage

## Boundary Clarification

- Runtime `sentence-transformers` ownership is now documented under embedding-service.
- Loader/CLI/gateway docs now describe service-to-service embedding/query usage instead of direct model runtime loading.

## Validation

- This refactor was documentation-only and required no code changes to `shared/embeddings/embedding_model.py`.
