from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLI_SRC = PROJECT_ROOT / "services" / "rag_cli" / "src"
sys.path.insert(0, str(CLI_SRC))

import cli


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class FakeCollection:
    def __init__(self):
        self.deleted = False
        self.get_payload = {
            "ids": ["silver_pine:hours.md:0"],
            "documents": ["We are open Monday-Friday 9am-6pm."],
            "metadatas": [{"tenant_id": "silver_pine", "source_file": "hours.md", "chunk_index": 0}],
        }

    def get(self, **_kwargs):
        return self.get_payload


class FakeChromaClient:
    def __init__(self):
        self.collection = FakeCollection()
        self.deleted_name: str | None = None

    def list_collections(self):
        return ["silver_pine_docs", "smith_law_docs"]

    def get_or_create_collection(self, _name: str):
        return self.collection

    def delete_collection(self, name: str):
        self.deleted_name = name


class RagCliTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_list_collections(self):
        with patch("cli._chroma_client_from_url", return_value=FakeChromaClient()):
            result = self.runner.invoke(cli.app, ["list", "--chroma-url", "http://chromadb:8001"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("silver_pine_docs", result.stdout)
        self.assertIn("smith_law_docs", result.stdout)

    def test_query_outputs_score_source_and_metadata(self):
        payload = {
            "tenant_id": "silver_pine",
            "query": "What are your hours?",
            "matches": [
                {
                    "document": "We are open Monday-Friday 9am-6pm.",
                    "metadata": {"source_file": "hours.md", "tenant_id": "silver_pine", "chunk_index": 0},
                    "distance": 0.18,
                }
            ],
        }
        with patch("cli.requests.request", return_value=FakeResponse(status_code=200, payload=payload)):
            result = self.runner.invoke(
                cli.app,
                [
                    "query",
                    "--tenant",
                    "silver_pine",
                    "--query",
                    "What are your hours?",
                    "--server",
                    "embedding_service:8010",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Top Results:", result.stdout)
        self.assertIn("Source: hours.md", result.stdout)
        self.assertIn("Score:", result.stdout)
        self.assertIn("Metadata:", result.stdout)

    def test_inspect_shows_chunk_metadata(self):
        with patch("cli._chroma_client_from_url", return_value=FakeChromaClient()):
            result = self.runner.invoke(
                cli.app,
                ["inspect", "--tenant", "silver_pine", "--chroma-url", "http://chromadb:8001"],
            )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Collection: silver_pine_docs", result.stdout)
        self.assertIn("source_file: hours.md", result.stdout)
        self.assertIn("chunk_index: 0", result.stdout)

    def test_delete_collection(self):
        fake_client = FakeChromaClient()
        with patch("cli._chroma_client_from_url", return_value=fake_client):
            result = self.runner.invoke(
                cli.app,
                ["delete", "--tenant", "silver_pine", "--yes", "--chroma-url", "http://chromadb:8001"],
            )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(fake_client.deleted_name, "silver_pine_docs")
        self.assertIn("Deleted collection 'silver_pine_docs'.", result.stdout)

    def test_ingest_single_tenant(self):
        target = cli.IngestTarget(tenant_id="silver_pine", local_path=Path("rag_data/silver_pine"), ingest_path="silver_pine")
        with (
            patch("cli._discover_targets", return_value=[target]),
            patch(
                "cli.requests.request",
                return_value=FakeResponse(
                    status_code=200,
                    payload={
                        "tenant_id": "silver_pine",
                        "collection": "silver_pine_docs",
                        "documents_indexed": 1,
                        "chunks_indexed": 3,
                    },
                ),
            ) as request_mock,
        ):
            result = self.runner.invoke(
                cli.app,
                [
                    "ingest",
                    "--tenant",
                    "silver_pine",
                    "--path",
                    "rag_data",
                    "--server",
                    "embedding_service:8010",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(request_mock.call_count, 1)
        self.assertIn("[OK] tenant=silver_pine", result.stdout)


if __name__ == "__main__":
    unittest.main()
