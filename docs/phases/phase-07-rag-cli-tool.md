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
- Display score, source file, and metadata in query output.

## Deliverables
- Functional `rag_cli` command set.
- Usage docs with examples.

## Docker + Make Checkpoint
- Build/tag/push `docker.local.fyre.org/rag-cli:latest`.
- Add compose service or one-shot run examples for CLI container.

## Acceptance
- RAG operations work from CLI container without agent gateway service.
