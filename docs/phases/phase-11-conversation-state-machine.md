# Phase 11 - Conversation State Machine

## Goal
Implement stage-driven multi-turn conversation flow with Redis persistence.

## Implementation Tasks
- Implement `services/agent_gateway/state_machine.py`.
- Define stages from greeting through booking and end.
- Define `SessionState` model and transition logic.
- Persist session data to Redis across turns.

## Deliverables
- State machine module and Redis adapter.
- Transition tests for common call scenarios.

## Docker + Make Checkpoint
- Ensure `redis` service is in compose and reachable by gateway.
- Rebuild gateway image after state machine integration.

## Acceptance
- Session state persists between turns and service requests.
