# Phase 15 - Tool Execution Layer

## Goal
Implement external action tools for callback scheduling and confirmation email.

## Implementation Tasks
- Add `services/tools/calendar_tool.py` for `schedule_callback`.
- Add `services/tools/email_tool.py` for `send_confirmation_email`.
- Generate ICS attachment and send through Gmail integration.
- Add standalone tests with mocks for API interactions.

## Deliverables
- Calendar and email tools with stable interfaces.
- Credential/config requirements documentation.

## Docker + Make Checkpoint
- Build/tag/push `docker.local.fyre.org/tools:latest`.
- Ensure gateway can call tools service or shared module in compose.

## Acceptance
- Tool tests succeed and produce expected event/email outputs.
