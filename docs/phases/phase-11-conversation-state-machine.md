# Phase 11 - Conversation State Machine

## Goal
Implement stage-driven multi-turn conversation flow with Redis persistence.

## Implementation Tasks
- All work is done in the agent_gateway dir: `services/agent_gateway`
- add redis to `services/agent_gateway/docker-compose.yaml`
- Implement `services/agent_gateway/state_machine.py`.
- Define stages from greeting through booking and end.
- Define `SessionState` model and transition logic.
- Persist session data to Redis across turns.

## Deliverables
- State machine module and Redis adapter.
- Transition tests for common call scenarios.

## Docker + Make Checkpoint
- Ensure `redis` service is in compose and reachable by agent_gateway
- Rebuild gateway image after state machine integration.

## Acceptance
- Session state persists between turns and service requests.

## Testing
- create end to end tests in `services/agent_gateway/tests/`
- Bring up the docker redis and agent_gateway and run tests with make test
- reitterate
