from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit

import chromadb
import requests
import typer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.rag_loader.tenant_layout import discover_tenants

app = typer.Typer(
    add_completion=False,
    help="RAG CLI for ingestion, query, and Chroma collection inspection.",
)


@dataclass(frozen=True)
class IngestTarget:
    tenant_id: str
    local_path: Path
    ingest_path: str


def _tenant_collection_name(tenant_id: str) -> str:
    return f"{tenant_id}_docs"


def _normalize_server(server: str) -> str:
    server = server.strip()
    if not server:
        raise ValueError("server cannot be empty")
    if "://" not in server:
        server = f"http://{server}"

    parts = urlsplit(server)
    if not parts.netloc:
        raise ValueError(f"invalid server value: {server}")
    return server.rstrip("/")


def _normalize_chroma_url(chroma_url: str) -> tuple[str, int, bool]:
    raw = chroma_url.strip()
    if not raw:
        raise ValueError("chroma_url cannot be empty")
    if "://" not in raw:
        raw = f"http://{raw}"

    parsed = urlparse(raw)
    if not parsed.hostname:
        raise ValueError(f"invalid chroma_url value: {chroma_url}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.hostname, port, parsed.scheme == "https"


def _chroma_client_from_url(chroma_url: str) -> chromadb.HttpClient:
    host, port, ssl = _normalize_chroma_url(chroma_url)
    return chromadb.HttpClient(host=host, port=port, ssl=ssl)


def _extract_collection_names(collections: list[Any]) -> list[str]:
    names: list[str] = []
    for collection in collections:
        if isinstance(collection, str):
            names.append(collection)
            continue
        name = getattr(collection, "name", "")
        if name:
            names.append(str(name))
    return sorted(names)


def _build_ingest_payload(args: dict[str, Any], tenant_id: str, ingest_path: str) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "path": ingest_path,
        "recursive": args["recursive"],
        "chunk_size": args["chunk_size"],
        "overlap": args["overlap"],
        "batch_size": args["batch_size"],
        "reset_collection": args["reset_collection"],
    }


def _select_single_tenant_target(path_input: str, tenant_id: str) -> IngestTarget:
    source_path = Path(path_input)
    candidate_path = source_path / tenant_id
    if source_path.is_dir() and candidate_path.exists() and candidate_path.is_dir():
        ingest_path = str(candidate_path) if source_path.is_absolute() else tenant_id
        return IngestTarget(tenant_id=tenant_id, local_path=candidate_path, ingest_path=ingest_path)
    return IngestTarget(tenant_id=tenant_id, local_path=source_path, ingest_path=path_input)


def _discover_targets(path_input: str, tenant_id: str | None) -> list[IngestTarget]:
    if tenant_id:
        return [_select_single_tenant_target(path_input=path_input, tenant_id=tenant_id)]

    root = Path(path_input)
    tenant_ids = discover_tenants(root)
    if not tenant_ids:
        raise ValueError(
            f"No tenant directories found under '{path_input}'. "
            "Use --tenant for explicit ingestion."
        )

    targets: list[IngestTarget] = []
    for discovered_tenant in tenant_ids:
        tenant_path = root / discovered_tenant
        ingest_path = str(tenant_path) if root.is_absolute() else discovered_tenant
        targets.append(
            IngestTarget(
                tenant_id=discovered_tenant,
                local_path=tenant_path,
                ingest_path=ingest_path,
            )
        )
    return targets


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    timeout: float,
) -> dict[str, Any]:
    response = requests.request(method=method, url=url, json=payload, timeout=timeout)
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = {"error": response.text}
        raise RuntimeError(f"Request failed status={response.status_code}: {json.dumps(detail)}")
    return response.json()


@app.command("list")
def list_collections(
    chroma_url: str = typer.Option("http://chromadb:8001", help="Chroma URL, ex: http://chromadb:8001"),
) -> None:
    """List available Chroma collections."""
    try:
        client = _chroma_client_from_url(chroma_url)
        names = _extract_collection_names(client.list_collections())
    except Exception as exc:  # pragma: no cover - defensive for runtime environments
        typer.echo(f"Error listing collections: {exc}", err=True)
        raise typer.Exit(code=1)

    if not names:
        typer.echo("No collections found.")
        return

    for name in names:
        typer.echo(name)


@app.command("query")
def query_collection(
    tenant: str = typer.Option(..., "--tenant", help="Tenant ID, ex: silver_pine"),
    query: str = typer.Option(..., "--query", help="Query text."),
    n_results: int = typer.Option(5, "--n-results", min=1, max=50, help="Maximum number of results."),
    server: str = typer.Option(
        "embedding_service:8010",
        "--server",
        help="Embedding service host:port or URL.",
    ),
    timeout: float = typer.Option(30.0, "--timeout", min=0.1, help="HTTP timeout in seconds."),
) -> None:
    """Query tenant collection through embedding-service /v1/query."""
    try:
        server_url = _normalize_server(server)
        response = _request_json(
            method="POST",
            url=f"{server_url}/v1/query",
            payload={"tenant_id": tenant, "query": query, "n_results": n_results},
            timeout=timeout,
        )
    except (ValueError, RuntimeError, requests.RequestException) as exc:
        typer.echo(f"Query failed: {exc}", err=True)
        raise typer.Exit(code=1)

    matches = response.get("matches", [])
    if not matches:
        typer.echo("No matches found.")
        return

    typer.echo("Top Results:")
    for idx, match in enumerate(matches, start=1):
        metadata = match.get("metadata") or {}
        distance = match.get("distance")
        score = max(0.0, 1.0 - float(distance)) if isinstance(distance, (int, float)) else None
        source = metadata.get("source_file", "unknown")
        typer.echo(f"\n{idx}.")
        typer.echo(f"Text: {match.get('document', '')}")
        typer.echo(f"Source: {source}")
        if score is not None:
            typer.echo(f"Score: {score:.4f}")
        else:
            typer.echo("Score: n/a")
        typer.echo(f"Distance: {distance}")
        typer.echo(f"Metadata: {json.dumps(metadata, sort_keys=True)}")


@app.command("inspect")
def inspect_collection(
    tenant: str = typer.Option(..., "--tenant", help="Tenant ID, ex: silver_pine"),
    limit: int = typer.Option(10, "--limit", min=1, max=200, help="Number of chunks to inspect."),
    chroma_url: str = typer.Option("http://chromadb:8001", help="Chroma URL, ex: http://chromadb:8001"),
) -> None:
    """Inspect chunk metadata for a tenant collection."""
    collection_name = _tenant_collection_name(tenant)
    try:
        client = _chroma_client_from_url(chroma_url)
        collection = client.get_or_create_collection(collection_name)
        records = collection.get(limit=limit, include=["documents", "metadatas"])
    except Exception as exc:  # pragma: no cover - defensive for runtime environments
        typer.echo(f"Inspect failed: {exc}", err=True)
        raise typer.Exit(code=1)

    ids = records.get("ids", []) or []
    documents = records.get("documents", []) or []
    metadatas = records.get("metadatas", []) or []

    if not ids:
        typer.echo(f"Collection '{collection_name}' is empty.")
        return

    typer.echo(f"Collection: {collection_name}")
    typer.echo(f"Chunks shown: {len(ids)}")
    for idx, chunk_id in enumerate(ids):
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        text = documents[idx] if idx < len(documents) else ""
        source = metadata.get("source_file", "unknown")
        chunk_index = metadata.get("chunk_index", "n/a")
        preview = text.replace("\n", " ")[:120]
        typer.echo(f"\n- id: {chunk_id}")
        typer.echo(f"  source_file: {source}")
        typer.echo(f"  chunk_index: {chunk_index}")
        typer.echo(f"  metadata: {json.dumps(metadata, sort_keys=True)}")
        typer.echo(f"  text_preview: {preview}")


@app.command("delete")
def delete_collection(
    tenant: str = typer.Option(..., "--tenant", help="Tenant ID, ex: silver_pine"),
    chroma_url: str = typer.Option("http://chromadb:8001", help="Chroma URL, ex: http://chromadb:8001"),
    yes: bool = typer.Option(False, "--yes", help="Delete without confirmation prompt."),
) -> None:
    """Delete tenant Chroma collection."""
    collection_name = _tenant_collection_name(tenant)
    if not yes and not typer.confirm(f"Delete collection '{collection_name}'?"):
        typer.echo("Cancelled.")
        raise typer.Exit(code=1)

    try:
        client = _chroma_client_from_url(chroma_url)
        client.delete_collection(collection_name)
    except Exception as exc:  # pragma: no cover - defensive for runtime environments
        typer.echo(f"Delete failed: {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Deleted collection '{collection_name}'.")


@app.command("ingest")
def ingest_documents(
    tenant: str | None = typer.Option(None, "--tenant", help="Tenant ID. If omitted, discover all tenants under --path."),
    path: str = typer.Option(
        "rag_data",
        "--path",
        help="Root path for tenant discovery or direct tenant path for single-tenant mode.",
    ),
    server: str = typer.Option(
        "embedding_service:8010",
        "--server",
        help="Embedding service host:port or URL (default: embedding_service:8010).",
    ),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Recurse into subdirectories."),
    chunk_size: int = typer.Option(500, "--chunk-size", min=100, max=5000),
    overlap: int = typer.Option(50, "--overlap", min=0, max=1000),
    batch_size: int = typer.Option(32, "--batch-size", min=1, max=256),
    reset_collection: bool = typer.Option(False, "--reset-collection", help="Delete tenant collection before ingest."),
    timeout: float = typer.Option(120.0, "--timeout", min=0.1, help="HTTP timeout in seconds."),
) -> None:
    """Ingest tenant documents through embedding-service /v1/ingest."""
    if overlap >= chunk_size:
        typer.echo("--overlap must be smaller than --chunk-size", err=True)
        raise typer.Exit(code=2)

    try:
        server_url = _normalize_server(server)
        targets = _discover_targets(path_input=path, tenant_id=tenant)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2)

    payload_args = {
        "recursive": recursive,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "batch_size": batch_size,
        "reset_collection": reset_collection,
    }

    failures = 0
    for target in targets:
        payload = _build_ingest_payload(args=payload_args, tenant_id=target.tenant_id, ingest_path=target.ingest_path)
        try:
            result = _request_json(
                method="POST",
                url=f"{server_url}/v1/ingest",
                payload=payload,
                timeout=timeout,
            )
        except (RuntimeError, requests.RequestException) as exc:
            failures += 1
            typer.echo(
                f"[FAIL] tenant={target.tenant_id} path={target.ingest_path} error={exc}",
                err=True,
            )
            continue

        typer.echo(
            "[OK] "
            f"tenant={result.get('tenant_id', target.tenant_id)} "
            f"collection={result.get('collection')} "
            f"documents={result.get('documents_indexed')} "
            f"chunks={result.get('chunks_indexed')}"
        )

    if failures:
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
