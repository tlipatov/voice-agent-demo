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

## Image Build/Push

From repository root:

```bash
make build SERVICE=agent-gateway
make push SERVICE=agent-gateway
```
