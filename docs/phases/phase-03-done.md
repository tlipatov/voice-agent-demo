# Phase 03 - Done

## Phase

- Number: `03`
- Name: Embedding Module
- Date: 2026-03-05

## Implemented

- Added standalone installable embeddings library under:
  - `shared/embeddings/`
- Added library packaging files:
  - `shared/embeddings/pyproject.toml`
  - `shared/embeddings/README.md`
- Kept shared embedding module at:
  - `shared/embeddings/embedding_model.py`
- Implemented required API:
  - `load_embedding_model()`
  - `embed_text(text)`
  - `embed_documents(list_of_text)`
- Configured the embedding model as required:
  - `sentence-transformers/all-MiniLM-L6-v2`
- Moved lightweight tests to live with the library:
  - `shared/embeddings/tests/test_embedding_model.py`
- Removed unnecessary package marker files (`__init__.py`) across `shared/` and `services/` directories.

## Docker + Make Checkpoint

- Updated impacted service Dockerfiles to install the shared embeddings library with pip during image builds:
  - `services/rag_loader/Dockerfile`
  - `services/rag_cli/Dockerfile`
  - `services/agent_gateway/Dockerfile`
- Verified build delegation for impacted images:
  - `make -n build SERVICE=rag-loader` -> PASS
  - `make -n build SERVICE=rag-cli` -> PASS
  - `make -n build SERVICE=agent-gateway` -> PASS

## Validation Performed

- Unit tests:
  - `python3 -m unittest tests/test_embedding_model.py` (run from `shared/embeddings`)
  - Result: `Ran 3 tests ... OK`
- Packaging smoke (library metadata):
  - `python3 -m venv .venv && ./.venv/bin/pip install --dry-run ./shared/embeddings`
  - Result: `Would install voice-agent-embeddings-0.1.0`
- Local direct smoke attempt:
  - `python3 -c "from shared.embeddings.embedding_model import embed_text; print(len(embed_text('Hello world')))"`
  - Result: failed locally with `ModuleNotFoundError: No module named 'sentence_transformers'` because the host environment does not yet have runtime deps installed.

## Acceptance Status

- Reusable embedding module present: **PASS**
- Core embedding tests (shape + non-empty output): **PASS**
- Container dependency path for embedding model package: **PASS**
- Direct host runtime call without installing dependencies first: **BLOCKED** (expected to pass after `pip install -r requirements.txt` or inside service containers)
