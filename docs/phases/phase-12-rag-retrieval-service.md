# Phase 12 - RAG Retrieval Serclientvice

## Goal
Retrieve tenant-specific data from embedding service for each query.

## Implementation Tasks
- Implement `services/agent_gateway/rag_retreival.py`.
- Read embeddigns service implementaton, see docs/phases/phase-00-05-embedding-service.md and docs/phases/phase-00-05-done.md
- Retreive from embeddings service on embedding_service:8010 
- Retrieve embeddings/query matches via embedding-service REST API.

## Deliverables
- Retrieval client with error handling and tests.

## Acceptance
- Returned snippets are relevant and isolated per tenant.

## Testing
- implement e2e tests 
- launch agent_gateway docker-compose up
- test
- reitterate
