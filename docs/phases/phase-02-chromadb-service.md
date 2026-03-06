# Phase 02 - ChromaDB Service

## Goal
Run ChromaDB as a standalone container service on port `8001`.

## Implementation Tasks
- Create `docker/chromadb/Dockerfile` from `python:3.11`.
- Install `chromadb` and run `chroma run --host 0.0.0.0 --port 8001`.
- Add persistent volume strategy for local testing.
- Add healthcheck expectations to docs.

## Deliverables
- Buildable `chromadb` image.
- Local run command and healthcheck command.

## Docker + Make Checkpoint
- Tag image as `docker.local.fyre.org/chromadb:latest`.
- Add/verify `make build-chromadb` and include in `make build`.
- Add/verify `make push-chromadb` and include in `make push`.

## Acceptance
- `curl http://localhost:8001/api/v2/heartbeat` returns healthy status in containerized run.
