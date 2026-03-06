# Agent Gateway Service

## Purpose

`agent_gateway` is the API-facing service for call lifecycle and conversation orchestration.

## Responsibilities

- Expose FastAPI endpoints for call start/turn/end.
- Load tenant configuration and runtime context.
- Coordinate state machine, RAG retrieval, prompt building, and LLM calls.
- Return the final assistant response for each turn.

## Image Build/Push

From repository root:

```bash
make build SERVICE=agent-gateway
make push SERVICE=agent-gateway
```
