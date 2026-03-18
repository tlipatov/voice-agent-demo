"""End-to-end tests for embedding service gRPC query API."""

from __future__ import annotations

import json
import math
import os
import socket
import time
import unittest
import urllib.error
import urllib.request

try:
    import grpc
except ModuleNotFoundError:  # pragma: no cover - environment-dependent.
    grpc = None  # type: ignore[assignment]

if grpc is not None:
    from proto import embedding_pb2, embedding_pb2_grpc


BASE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8010").rstrip("/")
INGEST_URL = f"{BASE_URL}/v1/ingest"
GRPC_TARGET = os.getenv("EMBEDDING_GRPC_TARGET", "localhost:50051")


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


def _wait_for_grpc_ready(timeout_seconds: int = 120) -> None:
    host, port = GRPC_TARGET.rsplit(":", 1)
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, int(port)), timeout=5):
                return
        except OSError as exc:  # pragma: no cover - startup retries.
            last_error = exc
        time.sleep(2)
    raise AssertionError(f"gRPC service did not become ready in time. Last error: {last_error}")


@unittest.skipIf(grpc is None, "grpcio is not installed in the test runner environment")
class EmbeddingServiceGrpcE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _wait_for_grpc_ready()
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
        if ingest_status != 200:
            raise AssertionError(f"Expected ingest to succeed. status={ingest_status} payload={ingest_payload}")

    def test_query_returns_ranked_matches(self) -> None:
        with grpc.insecure_channel(GRPC_TARGET) as channel:
            stub = embedding_pb2_grpc.EmbeddingServiceStub(channel)
            response = stub.Query(
                embedding_pb2.QueryRequest(
                    tenant_id="silver_pine", query="What are your business hours?", n_results=3
                )
            )

        self.assertEqual(response.tenant_id, "silver_pine")
        self.assertEqual(response.query, "What are your business hours?")
        self.assertGreater(len(response.matches), 0)
        self.assertEqual(response.matches[0].metadata["tenant_id"], "silver_pine")
        self.assertTrue(math.isfinite(response.matches[0].distance))

    def test_query_validates_required_fields(self) -> None:
        with grpc.insecure_channel(GRPC_TARGET) as channel:
            stub = embedding_pb2_grpc.EmbeddingServiceStub(channel)

            with self.assertRaises(grpc.RpcError) as empty_tenant_error:
                stub.Query(embedding_pb2.QueryRequest(tenant_id="", query="hello", n_results=3))
            self.assertEqual(empty_tenant_error.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

            with self.assertRaises(grpc.RpcError) as empty_query_error:
                stub.Query(embedding_pb2.QueryRequest(tenant_id="silver_pine", query="", n_results=3))
            self.assertEqual(empty_query_error.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)


if __name__ == "__main__":
    unittest.main()
