# RAG Loader Service

## Purpose

`rag_loader` ingests tenant documents and indexes them into the vector database.

## Responsibilities

- Discover tenant content under `rag_data/`.
- Read and normalize supported document formats.
- Chunk documents and generate embeddings.
- Upsert chunk vectors and metadata into Chroma collections.

## Image Build/Push

From repository root:

```bash
make build SERVICE=rag-loader
make push SERVICE=rag-loader
```
