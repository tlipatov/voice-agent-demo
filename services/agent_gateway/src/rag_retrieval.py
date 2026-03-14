"""RAG retrieval client for agent_gateway.

Queries the embedding service REST API to retrieve tenant-specific document
snippets relevant to a given query.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class RagMatch:
    document: str
    metadata: dict[str, Any]
    distance: float


class RagRetrievalError(Exception):
    """Raised when retrieval from the embedding service fails."""


class RagClient:
    """Client for querying the embedding service /v1/query endpoint."""

    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        raw = base_url or os.getenv("EMBEDDING_SERVICE_URL", "http://embedding_service:8010")
        self._base_url = raw.rstrip("/")
        self._timeout = timeout

    def query(self, tenant_id: str, query: str, n_results: int = 5) -> list[RagMatch]:
        """Return ranked document matches for the given tenant and query text."""
        if not tenant_id:
            raise ValueError("tenant_id must not be empty")
        if not query:
            raise ValueError("query must not be empty")
        if n_results < 1:
            raise ValueError("n_results must be >= 1")

        payload = json.dumps(
            {"tenant_id": tenant_id, "query": query, "n_results": n_results}
        ).encode()

        req = Request(
            url=f"{self._base_url}/v1/query",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=self._timeout) as response:
                body = json.loads(response.read().decode())
        except URLError as exc:
            raise RagRetrievalError(
                f"Embedding service unreachable at {self._base_url}: {exc}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise RagRetrievalError(
                f"Invalid JSON response from embedding service: {exc}"
            ) from exc

        matches = body.get("matches", [])
        return [
            RagMatch(
                document=m["document"],
                metadata=m.get("metadata", {}),
                distance=m["distance"],
            )
            for m in matches
        ]
