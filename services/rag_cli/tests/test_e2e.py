from __future__ import annotations

import os
import subprocess
import unittest


class RagCliE2ETests(unittest.TestCase):
    def test_container_ingest_and_query_against_embedding_service(self):
        if os.getenv("RUN_RAG_CLI_E2E") != "1":
            self.skipTest("Set RUN_RAG_CLI_E2E=1 to run containerized e2e test.")

        ingest_cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            os.getenv("RAG_CLI_DOCKER_NETWORK", "embedding_service_default"),
            "-v",
            f"{os.getcwd()}/rag_data:/app/rag_data:ro",
            "docker.local.fyre.org/rag-cli:latest",
            "ingest",
            "--tenant",
            os.getenv("RAG_CLI_TENANT", "silver_pine"),
            "--path",
            "/app/rag_data",
            "--server",
            os.getenv("RAG_CLI_SERVER", "embedding_service:8010"),
        ]
        ingest = subprocess.run(ingest_cmd, check=False, capture_output=True, text=True)
        self.assertEqual(ingest.returncode, 0, msg=f"Ingest failed:\n{ingest.stdout}\n{ingest.stderr}")

        query_cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            os.getenv("RAG_CLI_DOCKER_NETWORK", "embedding_service_default"),
            "docker.local.fyre.org/rag-cli:latest",
            "query",
            "--tenant",
            os.getenv("RAG_CLI_TENANT", "silver_pine"),
            "--query",
            os.getenv("RAG_CLI_QUERY", "What are your business hours?"),
            "--server",
            os.getenv("RAG_CLI_SERVER", "embedding_service:8010"),
        ]
        query = subprocess.run(query_cmd, check=False, capture_output=True, text=True)
        self.assertEqual(query.returncode, 0, msg=f"Query failed:\n{query.stdout}\n{query.stderr}")
        self.assertIn("Top Results:", query.stdout)
        self.assertIn("Source:", query.stdout)
        self.assertIn("Score:", query.stdout)


if __name__ == "__main__":
    unittest.main()
