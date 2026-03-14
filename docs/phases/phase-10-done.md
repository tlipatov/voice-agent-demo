# Phase 10 - Done

## Phase

- Number: `10`
- Name: Agent Context Builder
- Date: 2026-03-08

## Implemented

- Added runtime context builder module:
  - `services/agent_gateway/src/context_builder.py`
  - Introduced immutable runtime models:
    - `PersonalityContext`
    - `AgentContext`
  - Added context conversion API:
    - `build_agent_context(config)`
    - `build_context_snapshot(configs)`
  - Added startup cache API:
    - `load_startup_context(config_dir)` with process-level `lru_cache(maxsize=1)`.
- Integrated context startup path into gateway entrypoint:
  - `services/agent_gateway/src/app.py`
  - Replaced direct config snapshot output with runtime `AgentContext` snapshot output.
  - Startup log now reports `tenant context(s)` loaded from `TENANT_CONFIG_DIR`.
- Added phase-specific tests:
  - `services/agent_gateway/tests/test_context_builder.py`
  - Covers:
    - immutable mapping behavior
    - immutable dataclass behavior
    - startup caching behavior (context reused after first load)
    - empty snapshot helper behavior
- Added gateway end-to-end startup test:
  - `services/agent_gateway/tests/test_e2e.py`
  - Verifies gateway startup succeeds when `EMBEDDING_SERVICE_URL` is reachable.
  - Verifies startup output includes loaded tenant contexts and embedding-service health confirmation.
- Updated service documentation:
  - `services/agent_gateway/README.md`
  - Added Phase 10 section and updated startup check wording.
  - Added gateway-only compose usage (`services/agent_gateway/docker-compose.yml`) for environments where embedding stack is managed separately.
- Removed embedding runtime coupling from gateway image:
  - `services/agent_gateway/Dockerfile`
  - Removed local install of `shared/embeddings` so embedding model runtime remains owned by `embedding_service`.
- Updated compose wiring for embedding-service reachability:
  - `docker/docker-compose.yml`
  - `agent_gateway` is configured to call `embedding_service:8010` via environment.
  - Added `EMBEDDING_SERVICE_URL=http://embedding_service:8010` for gateway runtime integration.
  - Attached `agent_gateway` to external network `embedding_service_default` via `embedding_service_net`.
  - Kept compose default network behavior unchanged so only gateway-to-embedding connectivity is affected.
- Added service-local compose for gateway-only startup:
  - `services/agent_gateway/docker-compose.yml`
  - Runs only `agent_gateway`.
  - Connects to external `embedding_service_default` network.
  - Mounts tenant configs and sets `EMBEDDING_SERVICE_URL=http://embedding_service:8010`.

## Validation Performed

- Unit tests:
  - `python3 -m unittest services/agent_gateway/tests/test_config_loader.py services/agent_gateway/tests/test_context_builder.py services/agent_gateway/tests/test_e2e.py`
- Gateway image build:
  - `cd services/agent_gateway && make build`
  - Result: PASS (`docker.local.fyre.org/agent-gateway:latest` rebuilt successfully)
- Gateway-only compose startup:
  - `cd services/agent_gateway && docker-compose -f docker-compose.yml up -d`
  - Result: PASS (`agent_gateway` started)
- Gateway startup log verification:
  - `cd services/agent_gateway && docker-compose -f docker-compose.yml logs --tail=100 agent_gateway`
  - Result: PASS (logs show tenant contexts loaded once and `Embedding service reachable at http://embedding_service:8010/healthz`)
- Service Makefile test workflow:
  - `cd services/agent_gateway && make test`
  - Result: PASS (starts gateway compose, runs `8` tests, tears down gateway container)
- Startup context smoke check:
  - `TENANT_CONFIG_DIR=configs/tenants python3 services/agent_gateway/src/app.py`
- Compose wiring check:
  - Verified in `docker/docker-compose.yml` that:
    - gateway env includes `EMBEDDING_SERVICE_URL=http://embedding_service:8010`
    - `agent_gateway` joins external network `embedding_service_default` (`embedding_service_net`)
  - Note: local `docker-compose config` validation is blocked in this environment because the installed `docker-compose` does not support the `gpus` key used by `embedding_service`.

## Acceptance Status

- Context object built from tenant config: **PASS**
- Context loaded once per service startup and reused during runtime: **PASS**
- Runtime context values protected from mutation: **PASS**
- `agent_gateway` compose integration includes `embedding_service` reachability on `embedding_service:8010`: **PASS**
- Compose network configured as `embedding_service_default`: **PASS**
