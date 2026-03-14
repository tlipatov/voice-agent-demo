# Phase 10 - Agent Context Builder

## Goal
Convert validated YAML config into immutable runtime context.

## Implementation Tasks
- Implement `services/agent_gateway/context_builder.py`.
- Build `AgentContext` object from tenant config.
- Cache context by tenant at startup.
- Ensure no runtime mutation of context values.
- Ensure `agent_gateway` service is in compose and can reach embeddings service: embedding_service:8010
- ensure the docker compose is using network embedding_service_default
- ensure it can reach the embeddings service: see docs/phases/phase-00-05-embedding-service.md and docs/phases/phase-00-05-done.md
- brings up with docker-compose up

## Deliverables
- Context builder module with tests.
- Startup load path integrated into gateway.

## Docker + Make Checkpoint
- Rebuild/tag/push `docker.local.fyre.org/agent-gateway:latest`.
- Verify startup logs show tenant context loaded once.

## Acceptance
- Context is loaded once per service start and reused during requests.

## Testing
- implement e2e tests
- start docker compose
- test
- reitterate