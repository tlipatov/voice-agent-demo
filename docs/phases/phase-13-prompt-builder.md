# Phase 13 - Prompt Builder

## Goal
Build deterministic LLM message payloads from context, state, and retrieval output.

Only work in the `services/agent_gateway` dir

## Implementation Tasks
- Reference: README.md , docs/phases/README.md, docs/TODO.md
- To understand how RAG works, wee embeddings serivce implementaton, see `docs/phases/phase-00-05-embedding-service.md` , `docs/phases/phase-00-05-done.md`, `docs/phases/phase-07-rag-cli-tool.md` , `docs/phases/phase-07-done.md` and `docs/phases/phase-12-*`
- Implement `services/agent_gateway/prompt_builder.py`.
- Inputs: `AgentContext`, `SessionState`, RAG results, user transcript.
- Output: structured chat messages (system/rules/rag/history/user).
- Add deterministic ordering and token-budget strategy.

## Deliverables
- Prompt builder implementation and golden tests.

## Docker + Make Checkpoint
- Rebuild agent gateway image with prompt builder updates.
- Validate generated prompts inside container test run.

## Acceptance
- Same input produces identical message JSON output.

## Testing
- implement e2e tests
- launch agent_gateway docker-compose up
- make test
- reitterate

## Documentation
- write docs/phases/phase-13-done.md
