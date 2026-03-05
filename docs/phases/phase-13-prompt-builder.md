# Phase 13 - Prompt Builder

## Goal
Build deterministic LLM message payloads from context, state, and retrieval output.

## Implementation Tasks
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
