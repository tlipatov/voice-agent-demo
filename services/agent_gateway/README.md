# Agent Gateway Service

## Purpose

`agent_gateway` is the API-facing service for call lifecycle and conversation orchestration.

## Responsibilities

- Expose FastAPI endpoints for call start/turn/end.
- Load tenant configuration and runtime context.
- Coordinate state machine, RAG retrieval, prompt building, and LLM calls.
- Return the final assistant response for each turn.

## Phase 08: Tenant YAML Configuration

- Tenant configs live in `configs/tenants/`.
- Gateway startup loads all `*.yaml` files from `TENANT_CONFIG_DIR` (default: `/app/configs/tenants`).
- Configs are immutable during runtime (loaded once at startup).

## Phase 10: Agent Context Builder

- Startup now builds `AgentContext` objects from validated tenant configs.
- Runtime context is cached once per process and reused across request handling.
- Context values are immutable (`frozen=True` dataclasses + immutable mapping snapshot).
- When `EMBEDDING_SERVICE_URL` is set, gateway startup validates `GET /healthz` before loading contexts.

## Phase 11: Conversation State Machine

- Added `services/agent_gateway/src/state_machine.py` with:
  - Stage enum from greeting through booking end-state.
  - `SessionState` model for `session_id`, stage, caller details, and history.
  - `ConversationStateMachine` transition engine for common voice call flows.
  - `RedisSessionStore` for cross-turn persisted session state in Redis.
- Added tests for state transitions and Redis persistence under `services/agent_gateway/tests/`.
- Startup now validates Redis connectivity when `REDIS_URL` is configured.
- Service-level compose now includes Redis and sets:
  - `REDIS_URL=redis://redis:6379/0`

### Local startup check

```bash
python services/agent_gateway/src/app.py
```

Expected output includes all loaded tenant runtime contexts and their configured RAG collections.

### Update workflow

1. Edit a tenant file in `configs/tenants/`.
2. Rebuild image when needed:
   - `make build SERVICE=agent-gateway`
3. Restart/redeploy gateway to apply changes:
   - `docker compose -f docker/docker-compose.yml up -d --build agent_gateway`

### Standalone compose (gateway-only)

Use this when `embedding_service` is already running in its own stack:

```bash
docker-compose -f services/agent_gateway/docker-compose.yml up -d
```

## Image Build/Push

From repository root:

```bash
make build SERVICE=agent-gateway
make push SERVICE=agent-gateway
```
