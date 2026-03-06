# Phase 12 - RAG Retrieval Service

## Goal
Retrieve tenant-specific context from ChromaDB for each user query.

## Implementation Tasks
- Implement `services/agent_gateway/rag_service.py`.
- Add `retrieve_context(query, tenant_id, top_k=5)`.
- Retrieve embeddings/query matches via embedding-service REST API.
- Query tenant collection and return normalized results.

## Deliverables
- Retrieval service with error handling and tests.

## Docker + Make Checkpoint
- Verify gateway container can reach Chroma service in compose.
- Rebuild/push gateway image with retrieval module.

## Acceptance
- Returned snippets are relevant and isolated per tenant.
