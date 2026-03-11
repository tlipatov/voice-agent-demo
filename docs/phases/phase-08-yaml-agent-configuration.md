# Phase 08 - YAML Agent Configuration

## Goal
Define immutable per-tenant agent behavior using YAML files.

## Implementation Tasks
- Add tenant files under `configs/tenants/`.
- Include sections: `tenant_id`, `business_profile`, `personality`, `agent_behavior`, `rag`, `integrations`.
- Keep runtime behavior driven from YAML-only values.
- Document update process (edit file + redeploy/restart).

## Deliverables
- Baseline configs for each tenant.
- Configuration authoring guide.
- make up a few tenants

## Docker + Make Checkpoint
- Mount `configs/tenants/` into gateway container or bake in image.
- Rebuild gateway image after config schema/location changes.
- gateway service placeholder services/agent_gateway/

## Acceptance
- Agent behavior changes only when YAML changes and container restarts.
