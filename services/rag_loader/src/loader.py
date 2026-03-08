from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.rag_loader.tenant_layout import discover_tenants


@dataclass(frozen=True)
class IngestTarget:
    tenant_id: str
    local_path: Path
    ingest_path: str


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


def _build_ingest_payload(args: argparse.Namespace, tenant_id: str, ingest_path: str) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "path": ingest_path,
        "recursive": args.recursive,
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
        "batch_size": args.batch_size,
        "reset_collection": args.reset_collection,
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


def _ingest(server: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    response = requests.post(
        f"{server}/v1/ingest",
        json=payload,
        timeout=timeout,
    )
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = {"error": response.text}
        raise RuntimeError(
            f"Ingest failed for tenant='{payload['tenant_id']}' status={response.status_code}: "
            f"{json.dumps(detail)}"
        )
    return response.json()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest tenant documents into embedding_service via /v1/ingest.",
    )
    parser.add_argument("--tenant", help="Tenant ID to ingest. If omitted, all tenants under --path.")
    parser.add_argument(
        "--path",
        default="rag_data",
        help="Root path for tenant discovery or direct tenant path for single-tenant mode.",
    )
    parser.add_argument(
        "--server",
        default="embedding_service:8010",
        help="Embedding service host:port or URL (default: embedding_service:8010).",
    )
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether ingestion should recurse into subdirectories (default: true).",
    )
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--reset-collection", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None and len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        print(
            "\nHint: connect to the compose network and provide the embedding service host, for example:",
            file=sys.stderr,
        )
        print(
            "  docker run --rm --network embedding_service_default "
            "-v \"$PWD/rag_data:/app/rag_data:ro\" docker.local.fyre.org/rag-loader:latest "
            "--path /app/rag_data --server embedding_service:8010",
            file=sys.stderr,
        )
        return 2

    args = parser.parse_args(argv)

    if args.overlap >= args.chunk_size:
        parser.error("--overlap must be smaller than --chunk-size")

    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")

    if args.timeout <= 0:
        parser.error("--timeout must be > 0")

    try:
        server = _normalize_server(args.server)
        targets = _discover_targets(path_input=args.path, tenant_id=args.tenant)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    failures = 0
    for target in targets:
        payload = _build_ingest_payload(args=args, tenant_id=target.tenant_id, ingest_path=target.ingest_path)
        try:
            result = _ingest(server=server, payload=payload, timeout=args.timeout)
        except (RuntimeError, requests.RequestException) as exc:
            failures += 1
            print(f"[FAIL] tenant={target.tenant_id} path={target.ingest_path} error={exc}", file=sys.stderr)
            continue

        print(
            "[OK] "
            f"tenant={result.get('tenant_id', target.tenant_id)} "
            f"collection={result.get('collection')} "
            f"documents={result.get('documents_indexed')} "
            f"chunks={result.get('chunks_indexed')}"
        )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
