# Phase 09 - YAML Schema Validation

## Goal
Validate tenant YAML files at startup and fail fast on invalid configs.

## Implementation Tasks
- Implement Pydantic models in `shared/schemas/agent_config.py`.
- Add YAML loader + validator helper.
- Add explicit startup validation in gateway and related services.
- Add positive/negative test fixtures.

## Deliverables
- Typed schema models and validation wiring.
- Clear error output with file and field context.

## Docker + Make Checkpoint
- Ensure validation is part of container startup path.
- Rebuild/push gateway image after validation changes.

## Acceptance
- Invalid YAML prevents service startup in container logs.
