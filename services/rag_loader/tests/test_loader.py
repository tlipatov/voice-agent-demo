from __future__ import annotations

import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOADER_SRC = PROJECT_ROOT / "services" / "rag_loader" / "src"
sys.path.insert(0, str(LOADER_SRC))

import loader


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class RagLoaderTests(unittest.TestCase):
    def test_normalize_server_accepts_host_port(self):
        self.assertEqual(loader._normalize_server("embedding_service:8010"), "http://embedding_service:8010")

    def test_discover_targets_for_relative_root_uses_tenant_relative_ingest_paths(self):
        with patch("loader.discover_tenants", return_value=["alpha", "beta"]):
            targets = loader._discover_targets(path_input="rag_data", tenant_id=None)
        self.assertEqual([target.tenant_id for target in targets], ["alpha", "beta"])
        self.assertEqual([target.ingest_path for target in targets], ["alpha", "beta"])

    def test_discover_targets_for_absolute_root_uses_absolute_ingest_paths(self):
        with patch("loader.discover_tenants", return_value=["alpha"]):
            targets = loader._discover_targets(path_input="/app/rag_data", tenant_id=None)
        self.assertEqual(targets[0].ingest_path, "/app/rag_data/alpha")

    def test_main_ingests_all_discovered_tenants(self):
        with (
            patch("loader.discover_tenants", return_value=["alpha", "beta"]),
            patch(
                "loader._ingest",
                side_effect=[
                    {"tenant_id": "alpha", "collection": "alpha_docs", "documents_indexed": 1, "chunks_indexed": 2},
                    {"tenant_id": "beta", "collection": "beta_docs", "documents_indexed": 2, "chunks_indexed": 5},
                ],
            ) as ingest_mock,
        ):
            exit_code = loader.main(["--path", "rag_data", "--server", "embedding_service:8010"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(ingest_mock.call_count, 2)
        payloads = [call.kwargs["payload"] for call in ingest_mock.call_args_list]
        self.assertEqual(payloads[0]["tenant_id"], "alpha")
        self.assertEqual(payloads[0]["path"], "alpha")
        self.assertEqual(payloads[1]["tenant_id"], "beta")
        self.assertEqual(payloads[1]["path"], "beta")

    def test_main_single_tenant_uses_explicit_path(self):
        with patch("loader._ingest", return_value={"tenant_id": "alpha"}) as ingest_mock:
            exit_code = loader.main(
                ["--tenant", "alpha", "--path", "/app/rag_data/alpha", "--server", "http://embedding_service:8010"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(ingest_mock.call_count, 1)
        payload = ingest_mock.call_args.kwargs["payload"]
        self.assertEqual(payload["tenant_id"], "alpha")
        self.assertEqual(payload["path"], "/app/rag_data/alpha")

    def test_ingest_surfaces_error_details(self):
        with patch(
            "loader.requests.post",
            return_value=FakeResponse(status_code=400, payload={"detail": "No docs"}),
        ):
            with self.assertRaises(RuntimeError):
                loader._ingest(
                    server="http://embedding_service:8010",
                    payload={"tenant_id": "alpha"},
                    timeout=30,
                )

    def test_main_without_arguments_prints_help_and_returns_error(self):
        with (
            patch.object(loader.sys, "argv", ["loader.py"]),
            patch("sys.stderr", new_callable=StringIO) as stderr,
        ):
            exit_code = loader.main(None)

        self.assertEqual(exit_code, 2)
        stderr_output = stderr.getvalue()
        self.assertIn("usage:", stderr_output)
        self.assertIn("docker run --rm --network embedding_service_default", stderr_output)


if __name__ == "__main__":
    unittest.main()
