# Phase 03 - Refactor Plan

## Why this refactor is needed

Yes, `docs/phases/phase-03-embedding-module.md` should be updated.

The current Phase 03 guide is partially outdated relative to what was delivered in `docs/phases/phase-03-done.md` and what is now needed for the embedding-service-first architecture.

## Gaps to address

1. **Scope drift from original Phase 03 doc**
   - Original Phase 03 only describes basic helper functions.
   - Delivered Phase 03 includes a packaged library (`shared/embeddings/pyproject.toml`) and tests under `shared/embeddings/tests/`.
2. **New runtime requirements are undocumented**
   - Current embedding module logic includes device selection and optional GPU enforcement behavior.
3. **Ownership boundary for sentence-transformers is not explicit**
   - We now want `sentence-transformers` runtime usage isolated to the embedding service path.
4. **Quality issue in phase text**
   - Current line `These are python libraries that care pip installed` should be corrected.

## Required updates to `phase-03-embedding-module.md`

- Keep the existing goal, but clarify that Phase 03 provides a **shared package used by the embedding service**.
- Add a subsection documenting behavior now expected from the module:
  - model name is `sentence-transformers/all-MiniLM-L6-v2`
  - environment-driven device selection (`EMBEDDING_DEVICE`, auto-detect CUDA fallback to CPU)
  - optional hard GPU requirement (`EMBEDDING_REQUIRE_GPU=true`)
- Add packaging as an explicit deliverable:
  - `shared/embeddings/pyproject.toml`
  - `shared/embeddings/README.md`
- Update checkpoint text to require service image install via pip of `shared/embeddings`.
- Fix typos/wording in implementation tasks.

## Required cross-phase alignment (documentation only)

To enforce "sentence-transformers is strictly used in embedding service":

- Phase 03 should state that the module is consumed by embedding-service runtime APIs.
- Later phases (loader/CLI/gateway) should reference embedding-service REST endpoints for embedding/query operations instead of loading model runtime directly.
- Any service requirements/docs that currently imply direct sentence-transformers use should be queued for follow-up refactor docs.

## Snippets another agent should preserve/align with

These snippets represent current expected embedding module behavior and should be treated as Phase 03 reference behavior:

```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
```

```python
def get_model_device() -> str:
    device = os.getenv("EMBEDDING_DEVICE")
    if device:
        return device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"
```

```python
def ensure_gpu_ready() -> None:
    if _env_flag("EMBEDDING_REQUIRE_GPU", False) and get_model_device() != "cuda":
        raise RuntimeError("GPU is required for embeddings but CUDA is not available.")
```

```python
def load_embedding_model() -> "SentenceTransformer":
    return _load_embedding_model(get_model_device())
```

## Acceptance criteria for this refactor doc task

- `phase-03-refactor.md` exists and clearly describes:
  - what in Phase 03 is outdated
  - what must be changed in Phase 03 docs
  - what boundaries must be documented for sentence-transformers ownership
- No code changes are required as part of this refactor documentation step.
