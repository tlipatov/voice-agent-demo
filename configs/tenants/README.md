# Tenant YAML Configuration Guide

This directory contains immutable per-tenant agent behavior configs.

## Required File Rules

- One file per tenant: `configs/tenants/<tenant_id>.yaml`
- `tenant_id` inside YAML must match the filename stem.
- Required top-level sections:
  - `tenant_id`
  - `business_profile`
  - `personality`
  - `agent_behavior`
  - `rag`
  - `integrations`

## Authoring Template

```yaml
tenant_id: your_tenant_id
business_profile:
  name: "Business Name"
  industry: "Industry"
personality:
  tone: "friendly"
  pace: "steady"
  formality: "professional"
agent_behavior:
  greeting: "Greeting text"
  rules:
    - "Behavior rule 1"
    - "Behavior rule 2"
rag:
  collection: "your_tenant_id_docs"
  top_k: 5
integrations:
  calendar:
    provider: "google"
  email:
    provider: "gmail"
```

## Update Process

1. Edit the tenant YAML file under `configs/tenants/`.
2. Rebuild the gateway image if config packaging/location changed:
   - `make build SERVICE=agent-gateway`
3. Restart/redeploy `agent_gateway` so startup reloads configs:
   - `docker compose -f docker/docker-compose.yml up -d --build agent_gateway`

Behavior changes only apply after restart because configs are loaded once at service startup.
