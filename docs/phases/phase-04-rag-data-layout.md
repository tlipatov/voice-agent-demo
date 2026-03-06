# Phase 04 - RAG Data Layout

## Goal
Define tenant-isolated document storage conventions.

## Implementation Tasks
- Enforce `rag_data/<tenant_id>/...` folder structure.
- Seed sample tenants (`silver_pine`, `smith_law`) with markdown docs.
- Define collection mapping: `{tenant_id}_docs`.
- Add supported input types list (`.md`, `.txt`, `.pdf`).
- Mount `rag_data/` into `embedding_service` for path-based ingestion triggers.
- Keep loader/CLI/gateway focused on orchestration and API integration, not model runtime ownership.

## Deliverables
- Tenant data layout guide.
- Sample tenant folders with starter docs.

## Interoperability Contract
- Collection naming remains `{tenant_id}_docs` across embedding service, loader, CLI, and gateway integrations.

## Docker + Make Checkpoint
- Mount `rag_data/` into any container that resolves ingestion paths; this includes `embedding_service` as a first-class requirement.
- Loader and gateway mounts remain valid for discovery and retrieval use cases.
- Rebuild/push affected images after loader discovery changes.

## Acceptance
- Loader discovers tenants automatically from mounted `rag_data`.
- Ingestion path consumers resolve document paths within mounted `rag_data`.
