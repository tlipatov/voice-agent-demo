# Phase Refactor 04 - Done

## Refactor

- Number: `04`
- Date: 2026-03-06
- Source: `docs/phases/phase-04-refactor.md`

## What Was Updated

- Updated `docs/phases/phase-04-rag-data-layout.md` to align Phase 04 guidance with embedding-service-first ingestion:
  - kept original Phase 04 goals and tenant layout structure
  - added explicit requirement to mount `rag_data/` into `embedding_service` for path-based ingestion
  - clarified that loader/CLI/gateway orchestrate ingestion/query flows and do not own model runtime
  - added interoperability contract that collection naming remains `{tenant_id}_docs` across embedding service, loader, CLI, and gateway
  - updated acceptance language to require ingestion path consumers to resolve paths within mounted `rag_data`

## Validation

- Confirmed `docker/docker-compose.yml` already mounts `../rag_data:/app/rag_data:ro` into:
  - `embedding_service`
  - `rag_loader`
  - `agent_gateway`
- Refactor implemented as documentation alignment; no runtime code changes were required.
