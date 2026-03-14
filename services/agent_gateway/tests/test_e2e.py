"""End-to-end startup tests for agent gateway."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
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


if __name__ == "__main__":
    unittest.main()
