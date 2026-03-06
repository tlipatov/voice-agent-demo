# Phase 02 - Done

## Phase

- Number: `02`
- Name: ChromaDB Service
- Date: 2026-03-05

## Implemented

- Added `docker/chromadb/Dockerfile` based on `python:3.11`.
- Installed `chromadb` in the image and configured startup command:
  - `chroma run --host 0.0.0.0 --port 8001 --path /data`
- Added `docker/chromadb/Makefile` with:
  - `build`
  - `push`
  - `release`
- Updated top-level `Makefile` to support `SERVICE=chromadb` and delegate builds/pushes to `docker/chromadb/Makefile`.

## Persistence + Healthcheck

- Updated `docker/docker-compose.yml`:
  - Fixed ChromaDB port mapping to `8001:8001`
  - Added persistent local volume `chromadb_data:/data`
  - Added container healthcheck against:
    - `http://localhost:8001/api/v2/heartbeat`

## Local Commands

- Build image:
  - `make build SERVICE=chromadb`
- Push image:
  - `make push SERVICE=chromadb`
- Run ChromaDB container with compose:
  - `docker-compose -f docker/docker-compose.yml up -d chromadb`
- Manual healthcheck:
  - `curl http://localhost:8001/api/v2/heartbeat`

## Validation Performed

- `make -n build SERVICE=chromadb` -> PASS (delegates to `docker/chromadb/Makefile`)
- `make -n push SERVICE=chromadb` -> PASS (delegates to `docker/chromadb/Makefile`)
- `make list-services` -> PASS (`chromadb` included)
- `docker-compose -f docker/docker-compose.yml config` -> PASS

## Acceptance Status

- Buildable `chromadb` image: **PASS**
- Local run and healthcheck commands documented: **PASS**
- Persistent volume strategy present: **PASS**
