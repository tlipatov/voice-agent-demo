from __future__ import annotations

from pathlib import Path

SUPPORTED_INPUT_TYPES = (".md", ".txt", ".pdf")


def discover_tenants(rag_data_root: str | Path = "rag_data") -> list[str]:
    """Return tenant IDs discovered as subdirectories in rag_data root."""
    root_path = Path(rag_data_root)
    if not root_path.exists():
        return []

    tenants = [
        path.name
        for path in root_path.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]
    return sorted(tenants)


def collection_name_for_tenant(tenant_id: str) -> str:
    """Map a tenant ID to its Chroma collection name."""
    return f"{tenant_id}_docs"


def list_supported_documents(tenant_id: str, rag_data_root: str | Path = "rag_data") -> list[Path]:
    """List supported tenant documents for ingestion."""
    tenant_path = Path(rag_data_root) / tenant_id
    if not tenant_path.exists():
        return []

    docs: list[Path] = []
    for path in tenant_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_TYPES:
            docs.append(path)

    return sorted(docs)
