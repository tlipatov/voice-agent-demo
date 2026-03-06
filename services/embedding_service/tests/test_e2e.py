"""End-to-end tests for embedding service ingest/query APIs."""

from __future__ import annotations

import json
import os
import time
import unittest
import urllib.error
import urllib.request


BASE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8010").rstrip("/")
HEALTH_URL = f"{BASE_URL}/healthz"
INGEST_URL = f"{BASE_URL}/v1/ingest"
QUERY_URL = f"{BASE_URL}/v1/query"


def _json_request(method: str, url: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8")
        parsed = json.loads(data) if data else {}
        return exc.code, parsed


def _wait_for_service_ready(timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=5) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    if payload.get("status") == "ok":
                        return
        except Exception as exc:  # pragma: no cover - only for startup retries.
            last_error = exc
        time.sleep(2)
    raise AssertionError(f"Embedding service did not become healthy in time. Last error: {last_error}")


class EmbeddingServiceE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _wait_for_service_ready()

    def test_v1_ingest_indexes_tenant_documents(self):
        status, payload = _json_request(
            "POST",
            INGEST_URL,
            {
                "tenant_id": "silver_pine",
                "path": "silver_pine",
                "recursive": True,
                "chunk_size": 500,
                "overlap": 50,
                "batch_size": 16,
                "reset_collection": True,
            },
        )

        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["tenant_id"], "silver_pine")
        self.assertEqual(payload["collection"], "silver_pine_docs")
        self.assertEqual(payload["documents_indexed"], 2)
        self.assertGreater(payload["chunks_indexed"], 0)

    def test_v1_query_returns_ranked_matches(self):
        ingest_status, ingest_payload = _json_request(
            "POST",
            INGEST_URL,
            {
                "tenant_id": "silver_pine",
                "path": "silver_pine",
                "recursive": True,
                "chunk_size": 500,
                "overlap": 50,
                "batch_size": 16,
                "reset_collection": True,
            },
        )
        self.assertEqual(ingest_status, 200, ingest_payload)

        status, payload = _json_request(
            "POST",
            QUERY_URL,
            {
                "tenant_id": "silver_pine",
                "query": "What are your business hours?",
                "n_results": 3,
            },
        )

        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["tenant_id"], "silver_pine")
        self.assertEqual(payload["query"], "What are your business hours?")
        self.assertGreater(len(payload["matches"]), 0)

        first_match = payload["matches"][0]
        metadata = first_match.get("metadata", {})
        self.assertEqual(metadata.get("tenant_id"), "silver_pine")
        self.assertIn("silver_pine", metadata.get("source_file", ""))
        self.assertIsNotNone(first_match.get("distance"))


if __name__ == "__main__":
    unittest.main()
