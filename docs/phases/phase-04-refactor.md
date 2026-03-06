# Phase 04 - Refactor Plan

## Why this refactor is needed

`docs/phases/phase-04-rag-data-layout.md` is still mostly valid, but it is missing alignment with the embedding-service-first architecture introduced after the original Phase 04 implementation.

`docs/phases/phase-04-done.md` correctly captures what was completed at that time and should be treated as historical completion evidence. It does not need to be rewritten, but current guidance needs an add-on refactor plan.

## What remains valid from Phase 04

- Tenant layout convention: `rag_data/<tenant_id>/...`
- Collection naming convention: `{tenant_id}_docs`
- Supported input types: `.md`, `.txt`, `.pdf`
- Seed tenant examples and tenant discovery intent

## Gaps to address in current Phase 04 guidance

1. **Service responsibility drift**
   - Existing Phase 04 wording implies loader-centric ingestion path.
   - Current direction is embedding-service REST ingestion/query as the primary embedding boundary.
2. **Compose mount target is outdated**
   - Current checkpoint mentions mounting `rag_data` into loader and gateway only.
   - For embedding-service ingestion by path, `rag_data` must be mounted into `embedding_service` as a first-class requirement.
3. **Boundary with Phase 03 is not explicit**
   - Phase 04 should reference Phase 03 ownership boundary: model runtime usage belongs to embedding service.

## Required updates to `phase-04-rag-data-layout.md`

- Keep goal and base structure unchanged.
- Update implementation/checkpoint language to state:
  - `rag_data` is mounted where document ingestion by path is executed (embedding service).
  - Loader/CLI may orchestrate ingest/query, but should not own model runtime.
- Add a short interoperability note:
  - collection name contract `{tenant_id}_docs` is shared by embedding service, loader, CLI, and gateway.
- Keep acceptance focused on tenant discovery/layout validity, and add one line:
  - ingestion path consumers must resolve paths within mounted `rag_data`.

## Suggested wording snippets for the next docs pass

```md
- Mount `rag_data/` into `embedding_service` for path-based ingestion triggers.
- Keep tenant folder contract stable: `rag_data/<tenant_id>/...`.
```

```md
Collection naming remains `{tenant_id}_docs` across all retrieval/ingestion clients.
```

```md
Loader/CLI/gateway integrate via embedding-service APIs for embedding operations; they do not load sentence-transformers runtime directly.
```

## Acceptance criteria for this refactor doc task

- `phase-04-refactor.md` exists and documents Phase 04 changes required by embedding-service-first scope.
- No code changes are required in this task.
