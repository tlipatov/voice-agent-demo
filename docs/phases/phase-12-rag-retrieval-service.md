# Phase 12 - RAG Retrieval Serclientvice

## Goal
Retrieve tenant-specific data from embedding service for each query.

Only work in the `services/agent_gateway` dir

## Implementation Tasks
- Reference: README.md , docs/phases/README.md, docs/TODO.md
- Implement `services/agent_gateway/rag_retreival.py`.
- Read embeddigns service implementaton, see `docs/phases/phase-00-05-embedding-service.md` , `docs/phases/phase-00-05-done.md`, `docs/phases/phase-07-rag-cli-tool.md` , `docs/phases/phase-07-done.md`
- Ensure `agent_gateway` service is in compose and can reach embeddings service: embedding_service:8010
- Retreive from embeddings service on embedding_service:8010 
- Retrieve embeddings/query matches via embedding-service REST API.

## Deliverables
- Retrieval client with error handling and tests.

## Acceptance
- Returned snippets are relevant and isolated per tenant.

## Testing
- implement e2e tests
- launch agent_gateway docker-compose up
- make test
- reitterate

## Documentation
- write docs/phases/phase-12-done.md
