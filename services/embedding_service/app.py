"""Embedding service API for ingestion and retrieval against ChromaDB."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pypdf import PdfReader

from chunking import chunk_document
from embedding_model import (
    embed_documents,
    embed_text,
    ensure_gpu_ready,
    get_model_device,
    load_embedding_model,
)

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}

app = FastAPI(title="Embedding Service", version="1.0.0")


class IngestRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    path: str = Field(min_length=1, description="Absolute path or path relative to INGEST_ROOT")
    recursive: bool = True
    chunk_size: int = Field(default=500, ge=100, le=5000)
    overlap: int = Field(default=50, ge=0, le=1000)
    batch_size: int = Field(default=32, ge=1, le=256)
    reset_collection: bool = False


class QueryRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    n_results: int = Field(default=5, ge=1, le=50)


def _collection_name(tenant_id: str) -> str:
    return f"{tenant_id}_docs"


def _chroma_client() -> chromadb.HttpClient:
    chroma_url = os.getenv("CHROMA_URL", "http://chromadb:8001")
    parsed = urlparse(chroma_url)
    host = parsed.hostname or "chromadb"
    port = parsed.port or 8001
    ssl = parsed.scheme == "https"
    return chromadb.HttpClient(host=host, port=port, ssl=ssl)


def _resolve_ingest_path(raw_path: str) -> Path:
    ingest_root = Path(os.getenv("INGEST_ROOT", "/app/rag_data")).resolve()
    input_path = Path(raw_path)
    resolved = input_path.resolve() if input_path.is_absolute() else (ingest_root / input_path).resolve()
    if not resolved.exists():
        raise HTTPException(status_code=404, detail=f"Input path does not exist: {resolved}")
    return resolved


def _iter_document_paths(path: Path, recursive: bool) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_EXTENSIONS else []

    pattern = "**/*" if recursive else "*"
    return sorted(
        [
            file_path
            for file_path in path.glob(pattern)
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )


def _read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    raise ValueError(f"Unsupported document type: {path.suffix}")


@app.on_event("startup")
def _startup() -> None:
    ensure_gpu_ready()
    load_embedding_model()


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "embedding_device": get_model_device()}


@app.post("/v1/ingest")
def ingest_documents(request: IngestRequest) -> dict[str, Any]:
    if request.overlap >= request.chunk_size:
        raise HTTPException(status_code=400, detail="overlap must be smaller than chunk_size.")

    resolved_path = _resolve_ingest_path(request.path)
    documents = _iter_document_paths(resolved_path, request.recursive)
    if not documents:
        raise HTTPException(status_code=400, detail="No supported documents found to ingest.")

    records: list[dict[str, Any]] = []
    for doc_path in documents:
        content = _read_document(doc_path)
        chunk_records = chunk_document(
            content,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            tenant_id=request.tenant_id,
            source_file=str(doc_path),
        )
        for record in chunk_records:
            records.append(
                {
                    "id": f"{request.tenant_id}:{record['chunk_id']}",
                    "text": record["text"],
                    "metadata": record["metadata"],
                }
            )

    if not records:
        raise HTTPException(status_code=400, detail="No non-empty chunks produced from input path.")

    client = _chroma_client()
    collection_name = _collection_name(request.tenant_id)
    if request.reset_collection:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    collection = client.get_or_create_collection(collection_name)

    for start in range(0, len(records), request.batch_size):
        batch = records[start : start + request.batch_size]
        embeddings = embed_documents([record["text"] for record in batch])
        collection.upsert(
            ids=[record["id"] for record in batch],
            embeddings=embeddings,
            documents=[record["text"] for record in batch],
            metadatas=[record["metadata"] for record in batch],
        )

    return {
        "tenant_id": request.tenant_id,
        "collection": collection_name,
        "documents_indexed": len(documents),
        "chunks_indexed": len(records),
    }


@app.post("/v1/query")
def query_documents(request: QueryRequest) -> dict[str, Any]:
    client = _chroma_client()
    collection = client.get_or_create_collection(_collection_name(request.tenant_id))
    query_embedding = embed_text(request.query)
    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=request.n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]

    matches = []
    for idx, doc in enumerate(documents):
        matches.append(
            {
                "document": doc,
                "metadata": metadatas[idx] if idx < len(metadatas) else {},
                "distance": distances[idx] if idx < len(distances) else None,
            }
        )

    return {"tenant_id": request.tenant_id, "query": request.query, "matches": matches}
