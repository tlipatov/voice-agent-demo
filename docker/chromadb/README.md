# ChromaDB Container

This directory contains the standalone ChromaDB container definition used by the local voice-agent stack.

## What It Is

- A Docker image definition for ChromaDB, exposed on port `8001`
- A local persistent data path mounted at `/data`
- A local `Makefile` for `build`, `push`, and `release`

## Files

- `docker/chromadb/Dockerfile` - builds the ChromaDB image
- `docker/chromadb/Makefile` - image lifecycle commands

## Build and Push

From the repository root:

```bash
make build SERVICE=chromadb
make push SERVICE=chromadb
```

Or directly in this folder:

```bash
make -C docker/chromadb build
make -C docker/chromadb push
```

## Run Locally (Docker Compose)

```bash
docker-compose -f docker/docker-compose.yml up -d chromadb
```

Healthcheck:

```bash
curl http://localhost:8001/api/v1/heartbeat
```

## Run with Docker CLI

```bash
docker run --rm -it \
  --name chromadb \
  -p 8001:8001 \
  -v chromadb_data:/data \
  docker.local.fyre.org/chromadb:latest
```

## NVIDIA GPU Run Notes

ChromaDB itself is CPU-oriented and does not require a GPU for normal operation. If you want to run it in a GPU-enabled Docker environment, use Docker with the NVIDIA runtime installed.

Prerequisites:

- NVIDIA driver installed on host
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- Docker GPU support verified (for example: `docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi`)

Run command:

```bash
docker run --rm -it \
  --name chromadb \
  --gpus all \
  -p 8001:8001 \
  -v chromadb_data:/data \
  docker.local.fyre.org/chromadb:latest
```

The `--gpus all` flag grants GPU access to the container, but ChromaDB will still primarily use CPU unless you add GPU-dependent components in your own stack.
