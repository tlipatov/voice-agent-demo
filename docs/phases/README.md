# Voice Agent Platform - Phase Implementation Guides

This directory contains one implementation guide per phase from `docs/TODO.md`.

## Generated Phase Files

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
2. Build service image(s): `make build`
3. Push image(s): `make push`
4. Run stack: `make run` (or `docker compose -f docker/docker-compose.yml up -d`)
5. Verify acceptance criteria with containerized services.

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
