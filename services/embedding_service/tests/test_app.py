"""Unit tests for embedding service API behavior."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = PROJECT_ROOT / "services" / "embedding_service"
SHARED_EMBEDDINGS_DIR = PROJECT_ROOT / "shared" / "embeddings"
sys.path.insert(0, str(SERVICE_DIR))
sys.path.insert(0, str(SHARED_EMBEDDINGS_DIR))

# Keep unit tests independent from optional local dependency installs.
sys.modules.setdefault("pypdf", types.SimpleNamespace(PdfReader=object))

import app as embedding_app
from chunking import chunk_document


class FakeCollection:
    def __init__(self):
        self.upsert_calls: list[dict] = []
        self.query_response = {
            "documents": [["hours chunk"]],
            "metadatas": [[{"tenant_id": "silver_pine", "source_file": "/tmp/hours.md", "chunk_index": 0}]],
            "distances": [[0.12]],
        }

    def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)

    def query(self, **kwargs):
        return self.query_response


class FakeChromaClient:
    def __init__(self):
        self.collection = FakeCollection()
        self.deleted: list[str] = []

    def delete_collection(self, name: str):
        self.deleted.append(name)

    def get_or_create_collection(self, _name: str):
        return self.collection


class EmbeddingServiceTests(unittest.TestCase):
    def setUp(self):
        self.startup_patches = [
            patch("app.ensure_gpu_ready", return_value=None),
            patch("app.load_embedding_model", return_value=object()),
        ]
        for p in self.startup_patches:
            p.start()
        self.client = TestClient(embedding_app.app)

    def tearDown(self):
        self.client.close()
        for p in reversed(self.startup_patches):
            p.stop()

    def test_healthz_reports_status_and_device(self):
        with patch("app.get_model_device", return_value="cpu"):
            response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "embedding_device": "cpu"})

    def test_chunk_document_returns_chunk_records_with_metadata(self):
        records = chunk_document(
            "A" * 25,
            chunk_size=10,
            overlap=3,
            tenant_id="silver_pine",
            source_file="/tmp/a.txt",
        )

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["text"], "A" * 10)
        self.assertTrue(records[1]["text"].startswith("A" * 3))
        self.assertEqual(
            records[0]["metadata"],
            {
                "tenant_id": "silver_pine",
                "source_file": "/tmp/a.txt",
                "chunk_index": 0,
            },
        )

    def test_ingest_rejects_overlap_larger_than_chunk_size(self):
        response = self.client.post(
            "/v1/ingest",
            json={
                "tenant_id": "silver_pine",
                "path": "silver_pine",
                "chunk_size": 100,
                "overlap": 100,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("overlap must be smaller", response.text)

    def test_ingest_indexes_documents_and_chunks(self):
        fake_client = FakeChromaClient()
        with (
            patch("app._resolve_ingest_path", return_value=Path("/tmp/silver_pine")),
            patch("app._iter_document_paths", return_value=[Path("/tmp/silver_pine/hours.md")]),
            patch("app._read_document", return_value="Business hours are 9 to 5."),
            patch("app.embed_documents", return_value=[[0.1, 0.2, 0.3]]),
            patch("app._chroma_client", return_value=fake_client),
        ):
            response = self.client.post(
                "/v1/ingest",
                json={
                    "tenant_id": "silver_pine",
                    "path": "silver_pine",
                    "recursive": True,
                    "chunk_size": 500,
                    "overlap": 50,
                    "batch_size": 32,
                    "reset_collection": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["collection"], "silver_pine_docs")
        self.assertEqual(payload["documents_indexed"], 1)
        self.assertEqual(payload["chunks_indexed"], 1)
        self.assertEqual(len(fake_client.collection.upsert_calls), 1)
        self.assertEqual(fake_client.deleted, ["silver_pine_docs"])
        upsert_call = fake_client.collection.upsert_calls[0]
        self.assertEqual(upsert_call["metadatas"][0]["tenant_id"], "silver_pine")
        self.assertEqual(upsert_call["metadatas"][0]["chunk_index"], 0)

    def test_query_returns_ranked_matches(self):
        fake_client = FakeChromaClient()
        with (
            patch("app._chroma_client", return_value=fake_client),
            patch("app.embed_text", return_value=[0.9, 0.8, 0.7]),
        ):
            response = self.client.post(
                "/v1/query",
                json={
                    "tenant_id": "silver_pine",
                    "query": "What are your business hours?",
                    "n_results": 5,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tenant_id"], "silver_pine")
        self.assertEqual(len(payload["matches"]), 1)
        self.assertEqual(payload["matches"][0]["distance"], 0.12)


if __name__ == "__main__":
    unittest.main()
