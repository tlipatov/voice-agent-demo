# Phase 16 - FastAPI Agent Gateway

## Goal
Expose the full voice-agent flow through API endpoints.

## Implementation Tasks
- Implement `services/agent_gateway/main.py`.
- Endpoints: `POST /call/start`, `POST /call/turn`, `POST /call/end`.
- Wire call flow: state -> RAG -> prompt -> vLLM -> state update -> response.
- Add request/response models and tenant validation.

## Deliverables
- Working gateway service API with docs and tests.

## Docker + Make Checkpoint
- Build/tag/push `docker.local.fyre.org/agent-gateway:latest`.
- Verify gateway works in compose against live `chromadb`, `redis`, and `vllm`.

## Acceptance
- Simulated conversations return coherent turn-by-turn responses.
