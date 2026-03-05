# Phase 18 - Local Agent Testing Script

## Goal
Provide a local script to simulate call conversations without VAPI.

## Implementation Tasks
- Implement `scripts/test_agent.py`.
- Simulate start/turn/end flow against gateway endpoints.
- Include canned interactions (hours question, callback request).
- Print transcript and latency per turn.

## Deliverables
- Reusable local test harness script.
- Sample scenarios for regression checks.

## Docker + Make Checkpoint
- Run script against compose stack (`make run` first).
- Optionally run script inside utility container for consistent environment.

## Acceptance
- Full simulated call flow completes with expected stage progression.
