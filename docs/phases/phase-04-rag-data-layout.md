# Phase 04 - RAG Data Layout

## Goal
Define tenant-isolated document storage conventions.

## Implementation Tasks
- Enforce `rag_data/<tenant_id>/...` folder structure.
- Seed sample tenants (`silver_pine`, `smith_law`) with markdown docs.
- Define collection mapping: `{tenant_id}_docs`.
- Add supported input types list (`.md`, `.txt`, `.pdf`).

## Deliverables
- Tenant data layout guide.
- Sample tenant folders with starter docs.

## Docker + Make Checkpoint
- Mount `rag_data/` into loader and gateway containers via compose.
- Rebuild/push affected images after loader discovery changes.

## Acceptance
- Loader discovers tenants automatically from mounted `rag_data`.
