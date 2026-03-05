# voice-agent-demo

This project is a multi-business voice receptionist demo designed to show how one platform can power different branded agent experiences for different organizations. It focuses on delivering consistent, helpful conversations, business-specific responses, and a clear path from prototype to real customer-facing voice interactions.

## Container Registry Convention

All service images are tagged and pushed as:

- `docker.local.fyre.org/agent-gateway:latest`
- `docker.local.fyre.org/rag-loader:latest`
- `docker.local.fyre.org/rag-cli:latest`
- `docker.local.fyre.org/tools:latest`
- `docker.local.fyre.org/chromadb:latest`
- `docker.local.fyre.org/vllm:latest`

## Make-Based Build and Push

Expected `make` workflow:

- `make build` builds all service images
- `make push` pushes all `:latest` images to `docker.local.fyre.org`
- `make release` runs `build` then `push`
- `make run` starts the local stack (compose)
- `make down` stops the local stack
- `make logs` tails compose logs

## Docker Compose Examples

Start full stack:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Start with local rebuild:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

Run only infra dependencies:

```bash
docker compose -f docker/docker-compose.yml up -d chromadb redis
```

Stop and remove containers:

```bash
docker compose -f docker/docker-compose.yml down
```

View service logs:

```bash
docker compose -f docker/docker-compose.yml logs -f agent_gateway
```

## Phase Execution Guides

See `docs/phases/README.md` and the per-phase files under `docs/phases/`.
