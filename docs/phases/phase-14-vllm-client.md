# Phase 14 - vLLM Client

## Goal
Integrate gateway with vLLM `POST /v1/chat/completions` including streaming.

Only work in the `services/agent_gateway` dir

for dev/testing
use Vllm running on http://192.168.69.14:11434
model: llama3.2:3b-instruct-q4_K_M

## Implementation Tasks
- Implement `services/agent_gateway/llm_client.py`.
- Add VLLM URL:PORT configuration
- Model configuration
- Add non-stream and stream response handlers.
- Add configurable timeout/retry behavior.
- Add smoke test script for completion generation.

## Deliverables
- Production-ready vLLM client adapter.
- Test script and environment config docs.

## Docker + Make Checkpoint
- Rebuild/push gateway image after client integration.

## Acceptance
- Smoke test returns valid completion in containerized environment.

## Testing
- implement e2e tests
- launch agent_gateway docker-compose up
- make test
- reitterate
