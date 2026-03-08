# Phase 07 - RAG CLI Tool

## Goal
Provide a CLI to query and inspect vector data without running full agent flow.

## Implementation Tasks
- Build Typer app in `services/rag_cli/`.
- Commands:
  - `list`
  - `query --tenant <id> --query "<text>"`
  - `inspect --tenant <id>`
  - `delete --tenant <id>`
- Execute query operations through embedding-service REST APIs.
- Display score, source file, and metadata in query output.
- Make embedding-service
- Use argparse and add cli help
- Look at the loader cli for consistency: services/rag_loader docs/phases/phase-06*
- You will incorporate the loader functionality into this tool to make a single unified cli tool


## Deliverables
- Functional `rag_cli` command set.
- Usage docs with examples.

## Docker + Make Checkpoint
- Build/tag/push `docker.local.fyre.org/rag-cli:latest`.
- Add compose service or one-shot run examples for CLI container.
- create and use a Dockerfile and Makefile services/rag_cli/


## Acceptance
- RAG operations work from CLI container without agent gateway service.

## Testing

Add tests

Full end to end tests, you will test the cli tool against running embedings server just like the rag loader tool docker run -it --network embedding_service_default --rm docker.local.fyre.org/rag-loader:latest --server embedding_service:8010 --tenant silver_pine --path silver_pine
