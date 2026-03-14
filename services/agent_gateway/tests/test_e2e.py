"""End-to-end startup and RAG retrieval tests for agent gateway."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

APP_PATH = REPO_ROOT / "services" / "agent_gateway" / "src" / "app.py"
TENANT_CONFIG_DIR = REPO_ROOT / "configs" / "tenants"
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8010").rstrip("/")


def _embedding_service_is_healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/healthz", timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


class AgentGatewayE2ETests(unittest.TestCase):
    def test_startup_loads_context_once_and_reaches_embedding_service(self) -> None:
        if not _embedding_service_is_healthy(EMBEDDING_SERVICE_URL):
            self.skipTest(f"Embedding service is not reachable at {EMBEDDING_SERVICE_URL}/healthz")

        env = os.environ.copy()
        env["TENANT_CONFIG_DIR"] = str(TENANT_CONFIG_DIR)
        env["EMBEDDING_SERVICE_URL"] = EMBEDDING_SERVICE_URL

        result = subprocess.run(
            [sys.executable, str(APP_PATH)],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Loaded 3 tenant context(s)", result.stdout)
        self.assertIn("tenant=silver_pine", result.stdout)
        self.assertIn("Embedding service reachable at", result.stdout)


class RagRetrievalE2ETests(unittest.TestCase):
    """E2E tests for the RAG retrieval client against a live embedding service."""

    def setUp(self) -> None:
        if not _embedding_service_is_healthy(EMBEDDING_SERVICE_URL):
            self.skipTest(f"Embedding service is not reachable at {EMBEDDING_SERVICE_URL}/healthz")
        from services.agent_gateway.src.rag_retrieval import RagClient
        self.client = RagClient(base_url=EMBEDDING_SERVICE_URL)

    def test_query_returns_list(self) -> None:
        """Query should always return a list (empty if collection not yet ingested)."""
        results = self.client.query(tenant_id="silver_pine", query="appointment scheduling", n_results=3)
        self.assertIsInstance(results, list)

    def test_query_results_are_tenant_isolated(self) -> None:
        """Results must belong to the queried tenant only."""
        from services.agent_gateway.src.rag_retrieval import RagMatch
        results = self.client.query(tenant_id="silver_pine", query="wellness", n_results=5)
        for match in results:
            self.assertIsInstance(match, RagMatch)
            self.assertEqual(
                match.metadata.get("tenant_id"), "silver_pine",
                "Match metadata tenant_id must match requested tenant",
            )

    def test_query_result_fields(self) -> None:
        """Each match must have document text, metadata dict, and numeric distance."""
        results = self.client.query(tenant_id="silver_pine", query="clinic hours", n_results=2)
        for match in results:
            self.assertIsInstance(match.document, str)
            self.assertTrue(len(match.document) > 0)
            self.assertIsInstance(match.metadata, dict)
            self.assertIsInstance(match.distance, float)

    def test_query_respects_n_results(self) -> None:
        """Returned matches must not exceed requested n_results."""
        results = self.client.query(tenant_id="silver_pine", query="appointment", n_results=2)
        self.assertLessEqual(len(results), 2)

    def test_query_different_tenants_are_isolated(self) -> None:
        """Two different tenants must never share results from each other's collections."""
        results_a = self.client.query(tenant_id="silver_pine", query="services", n_results=5)
        results_b = self.client.query(tenant_id="smith_law", query="services", n_results=5)
        tenant_ids_a = {m.metadata.get("tenant_id") for m in results_a}
        tenant_ids_b = {m.metadata.get("tenant_id") for m in results_b}
        if results_a:
            self.assertNotIn("smith_law", tenant_ids_a)
        if results_b:
            self.assertNotIn("silver_pine", tenant_ids_b)

    def test_unreachable_service_raises_retrieval_error(self) -> None:
        """A bad URL must raise RagRetrievalError, not an unhandled exception."""
        from services.agent_gateway.src.rag_retrieval import RagClient, RagRetrievalError
        bad_client = RagClient(base_url="http://localhost:19999", timeout=2.0)
        with self.assertRaises(RagRetrievalError):
            bad_client.query(tenant_id="silver_pine", query="test", n_results=1)

    def test_empty_query_raises_value_error(self) -> None:
        from services.agent_gateway.src.rag_retrieval import RagRetrievalError
        with self.assertRaises(ValueError):
            self.client.query(tenant_id="silver_pine", query="", n_results=1)

    def test_empty_tenant_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.client.query(tenant_id="", query="appointment", n_results=1)


if __name__ == "__main__":
    unittest.main()
