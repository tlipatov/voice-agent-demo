# Voice Agent Platform - Phase Implementation Guides

This directory contains one implementation guide per phase from `docs/TODO.md`.

## Generated Phase Files

- `phase-00-05-embedding-service.md`
- `phase-01-repository-setup.md`
- `phase-02-chromadb-service.md`
- `phase-03-embedding-module.md`
- `phase-04-rag-data-layout.md`
- `phase-05-document-chunking.md`
- `phase-06-rag-loader-pipeline.md`
- `phase-07-rag-cli-tool.md`
- `phase-08-yaml-agent-configuration.md`
- `phase-09-yaml-schema-validation.md`
- `phase-10-agent-context-builder.md`
- `phase-11-conversation-state-machine.md`
- `phase-12-rag-retrieval-service.md`
- `phase-13-prompt-builder.md`
- `phase-14-vllm-client.md`
- `phase-15-tool-execution-layer.md`
- `phase-16-fastapi-agent-gateway.md`
- `phase-17-docker-compose.md`
- `phase-18-local-agent-testing-script.md`
- `phase-19-vapi-integration.md`

## Standard Delivery Workflow (Docker + Make)

Use this flow at the end of each phase:

1. Implement and test phase changes locally.
2. Build service image(s): `make build SERVICE=<service>`
3. Push image(s): `make push SERVICE=<service>`
4. Run stack: `docker compose -f docker/docker-compose.yml up -d`
5. Verify acceptance criteria with containerized services.

## Implementation Conventions for Agents

When implementing or updating any runnable component in a phase:

- Ensure it has its own `Makefile` for build/push/release commands.
- Ensure it has its own `README.md` that explains:
  - what it is for
  - how to build and run it locally
  - how to verify health/acceptance checks

Expected locations:

- App services: `services/<service>/Makefile` and `services/<service>/README.md`
- Infra containers: `docker/<container>/Makefile` and `docker/<container>/README.md`

## Docker Compose Examples

Bring up all services:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Rebuild and restart:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

Tear down:

```bash
docker compose -f docker/docker-compose.yml down
```

Check logs:

```bash
docker compose -f docker/docker-compose.yml logs -f
```
