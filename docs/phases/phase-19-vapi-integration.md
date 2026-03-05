# Phase 19 - VAPI Integration

## Goal
Connect live phone calls to the gateway using VAPI webhooks.

## Implementation Tasks
- Configure VAPI to send transcript turns to `POST /call/turn`.
- Map VAPI payload/session IDs to internal session state IDs.
- Return text responses for VAPI TTS/audio playback.
- Add request verification and retry-safe handling.

## Deliverables
- Working webhook integration and operational runbook.

## Docker + Make Checkpoint
- Ensure gateway container is externally reachable (ingress/reverse proxy).
- Rebuild/push gateway image after webhook adapter updates.
- Validate release flow with `make release`.

## Acceptance
- End-to-end live call successfully interacts with agent responses.
