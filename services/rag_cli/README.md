# RAG CLI Service

## Purpose

`rag_cli` provides command-line utilities for vector DB inspection and retrieval testing.

## Responsibilities

- List available tenant collections.
- Run semantic queries against tenant collections.
- Inspect chunk metadata for debugging.
- Support operational tasks like collection cleanup.

## Image Build/Push

From repository root:

```bash
make build SERVICE=rag-cli
make push SERVICE=rag-cli
```
