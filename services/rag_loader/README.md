# RAG Loader Service

## Purpose

`rag_loader` ingests tenant documents and indexes them into the vector database.

## Responsibilities

- Discover tenant content under `rag_data/`.
- Read and normalize supported document formats.
- Chunk documents and generate embeddings.
- Upsert chunk vectors and metadata into Chroma collections.
- Map collection names as `{tenant_id}_docs`.

## Tenant Discovery Layout

- Tenant root: `rag_data/<tenant_id>/...`
- Supported file types: `.md`, `.txt`, `.pdf`
- Discovery/mapping helpers:
  - `services/rag_loader/tenant_layout.py`

## Image Build/Push

From repository root:

```bash
make build SERVICE=rag-loader
make push SERVICE=rag-loader
```
