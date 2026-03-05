# Phase 14 - vLLM Client

## Goal
Integrate gateway with vLLM `POST /v1/chat/completions` including streaming.

## Implementation Tasks
- Implement `services/agent_gateway/llm_client.py`.
- Add non-stream and stream response handlers.
- Add configurable timeout/retry behavior.
- Add smoke test script for completion generation.

## Deliverables
- Production-ready vLLM client adapter.
- Test script and environment config docs.

## Docker + Make Checkpoint
- Ensure compose includes `vllm` service and model configuration.
- Rebuild/push gateway image after client integration.

## Acceptance
- Smoke test returns valid completion in containerized environment.
