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


class PromptBuilderE2ETests(unittest.TestCase):
    """E2E tests for prompt_builder using real tenant configs and live RAG."""

    def setUp(self) -> None:
        from services.agent_gateway.src.context_builder import load_startup_context
        load_startup_context.cache_clear()
        self._contexts = load_startup_context(str(TENANT_CONFIG_DIR))

    def tearDown(self) -> None:
        from services.agent_gateway.src.context_builder import load_startup_context
        load_startup_context.cache_clear()

    def test_build_messages_returns_list_of_dicts(self) -> None:
        from services.agent_gateway.src.prompt_builder import build_messages
        from services.agent_gateway.src.state_machine import SessionState

        context = self._contexts["silver_pine"]
        state = SessionState(session_id="e2e-test")
        msgs = build_messages(context, state, [], "What are your hours?")

        self.assertIsInstance(msgs, list)
        self.assertTrue(len(msgs) >= 2)
        for msg in msgs:
            self.assertIn("role", msg)
            self.assertIn("content", msg)
            self.assertIsInstance(msg["role"], str)
            self.assertIsInstance(msg["content"], str)

    def test_first_message_is_system(self) -> None:
        from services.agent_gateway.src.prompt_builder import build_messages
        from services.agent_gateway.src.state_machine import SessionState

        context = self._contexts["silver_pine"]
        state = SessionState(session_id="e2e-test")
        msgs = build_messages(context, state, [], "Hello")
        self.assertEqual(msgs[0]["role"], "system")

    def test_last_message_matches_transcript(self) -> None:
        from services.agent_gateway.src.prompt_builder import build_messages
        from services.agent_gateway.src.state_machine import SessionState

        context = self._contexts["silver_pine"]
        state = SessionState(session_id="e2e-test")
        msgs = build_messages(context, state, [], "What are your hours?")
        self.assertEqual(msgs[-1]["content"], "What are your hours?")

    def test_build_messages_with_live_rag(self) -> None:
        if not _embedding_service_is_healthy(EMBEDDING_SERVICE_URL):
            self.skipTest(f"Embedding service not reachable at {EMBEDDING_SERVICE_URL}/healthz")

        from services.agent_gateway.src.prompt_builder import _RAG_BLOCK_HEADER, build_messages
        from services.agent_gateway.src.rag_retrieval import RagClient
        from services.agent_gateway.src.state_machine import SessionState

        context = self._contexts["silver_pine"]
        client = RagClient(base_url=EMBEDDING_SERVICE_URL)
        matches = client.query(
            tenant_id=context.tenant_id,
            query="appointment scheduling",
            n_results=context.rag_top_k,
        )
        state = SessionState(session_id="e2e-rag-test")
        msgs = build_messages(context, state, matches, "How do I book an appointment?")

        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["content"], "How do I book an appointment?")
        if matches:
            rag_msg = next((m for m in msgs if _RAG_BLOCK_HEADER in m.get("content", "")), None)
            self.assertIsNotNone(rag_msg, "RAG block should be present when matches returned")

    def test_determinism_with_all_tenants(self) -> None:
        from services.agent_gateway.src.prompt_builder import build_messages
        from services.agent_gateway.src.state_machine import SessionState

        import json
        for tenant_id, context in self._contexts.items():
            state = SessionState(session_id=f"det-{tenant_id}")
            transcript = "What services do you offer?"
            out_a = json.dumps(build_messages(context, state, [], transcript), sort_keys=True)
            out_b = json.dumps(build_messages(context, state, [], transcript), sort_keys=True)
            self.assertEqual(out_a, out_b, f"Non-deterministic output for tenant {tenant_id}")

    def test_each_tenant_has_distinct_system_message(self) -> None:
        from services.agent_gateway.src.prompt_builder import build_messages
        from services.agent_gateway.src.state_machine import SessionState

        system_contents = set()
        for tenant_id, context in self._contexts.items():
            state = SessionState(session_id=f"uniq-{tenant_id}")
            msgs = build_messages(context, state, [], "Hi")
            system_contents.add(msgs[0]["content"])

        self.assertEqual(
            len(system_contents),
            len(self._contexts),
            "Each tenant must produce a distinct system message",
        )


if __name__ == "__main__":
    unittest.main()
