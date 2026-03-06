# RAG Data Layout

Tenant documents must be organized under:

`rag_data/<tenant_id>/...`

Examples:

- `rag_data/silver_pine/faq.md`
- `rag_data/smith_law/hours.md`

## Conventions

- One folder per tenant ID.
- Tenant folder name is the `tenant_id` used by runtime configuration.
- Chroma collection name mapping is: `{tenant_id}_docs`.
- Supported input types are:
  - `.md`
  - `.txt`
  - `.pdf`

## Notes

- Keep files focused and business-specific (hours, FAQ, services, policies).
- Avoid mixing documents from different tenants in the same folder.
