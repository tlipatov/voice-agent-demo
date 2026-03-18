"""Unit tests for the vLLM client."""

from __future__ import annotations

import json
import sys
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, ClassVar

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.agent_gateway.src.llm_client import (
    ChatMessage,
    CompletionChoice,
    CompletionResponse,
    CompletionUsage,
    LLMClient,
    LLMClientError,
    StreamChunk,
    StreamDelta,
)


class MockLLMHandler(BaseHTTPRequestHandler):
    """Mock HTTP handler for testing LLM client."""

    response_data: ClassVar[dict[str, Any] | None] = None
    stream_chunks: ClassVar[list[dict[str, Any]] | None] = None
    status_code: ClassVar[int] = 200
    error_message: ClassVar[str | None] = None

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_POST(self) -> None:
        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.server.received_body = self.rfile.read(content_length).decode()
            request_data = json.loads(body)

            if self.status_code != 200:
                self.send_error(self.status_code, self.error_message or "Error")
                return

            self.send_response(200)

            if request_data.get("stream", False) and self.stream_chunks:
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for chunk in self.stream_chunks:
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(self.response_data).encode())
        else:
            self.send_error(404, "Not Found")

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"object": "list", "data": []}).encode())
        else:
            self.send_error(404, "Not Found")


class LLMClientDataclassTests(unittest.TestCase):
    """Tests for LLM client dataclasses."""

    def test_chat_message_to_dict(self) -> None:
        msg = ChatMessage(role="user", content="Hello")
        self.assertEqual(msg.to_dict(), {"role": "user", "content": "Hello"})

    def test_completion_response_content_property(self) -> None:
        msg = ChatMessage(role="assistant", content="Hi there")
        choice = CompletionChoice(index=0, message=msg, finish_reason="stop")
        response = CompletionResponse(
            id="test-id",
            model="test-model",
            choices=(choice,),
            usage=None,
            created=0,
        )
        self.assertEqual(response.content, "Hi there")

    def test_completion_response_empty_choices(self) -> None:
        response = CompletionResponse(
            id="test-id",
            model="test-model",
            choices=(),
            usage=None,
            created=0,
        )
        self.assertEqual(response.content, "")

    def test_completion_usage_fields(self) -> None:
        usage = CompletionUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        self.assertEqual(usage.prompt_tokens, 10)
        self.assertEqual(usage.completion_tokens, 20)
        self.assertEqual(usage.total_tokens, 30)

    def test_stream_delta_fields(self) -> None:
        delta = StreamDelta(role="assistant", content="Hello")
        self.assertEqual(delta.role, "assistant")
        self.assertEqual(delta.content, "Hello")

    def test_stream_chunk_fields(self) -> None:
        delta = StreamDelta(role=None, content="test")
        chunk = StreamChunk(
            id="chunk-id",
            model="test-model",
            delta=delta,
            finish_reason=None,
        )
        self.assertEqual(chunk.id, "chunk-id")
        self.assertEqual(chunk.delta.content, "test")


class LLMClientValidationTests(unittest.TestCase):
    """Tests for LLM client input validation."""

    def setUp(self) -> None:
        self.client = LLMClient(base_url="http://localhost:9999")

    def test_empty_messages_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.client.complete([])
        self.assertIn("messages must not be empty", str(ctx.exception))

    def test_message_not_dict_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.client.complete(["not a dict"])  # type: ignore
        self.assertIn("must be a dict", str(ctx.exception))

    def test_message_missing_role_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.client.complete([{"content": "Hello"}])
        self.assertIn("missing 'role' key", str(ctx.exception))

    def test_message_missing_content_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.client.complete([{"role": "user"}])
        self.assertIn("missing 'content' key", str(ctx.exception))


class LLMClientConfigTests(unittest.TestCase):
    """Tests for LLM client configuration."""

    def test_default_base_url(self) -> None:
        client = LLMClient()
        self.assertEqual(client.base_url, "http://localhost:11434")

    def test_custom_base_url(self) -> None:
        client = LLMClient(base_url="http://custom:8080")
        self.assertEqual(client.base_url, "http://custom:8080")

    def test_base_url_trailing_slash_stripped(self) -> None:
        client = LLMClient(base_url="http://custom:8080/")
        self.assertEqual(client.base_url, "http://custom:8080")

    def test_default_model(self) -> None:
        client = LLMClient()
        self.assertEqual(client.model, "llama3.2:3b-instruct-q4_K_M")

    def test_custom_model(self) -> None:
        client = LLMClient(model="custom-model")
        self.assertEqual(client.model, "custom-model")


class LLMClientCompleteTests(unittest.TestCase):
    """Tests for non-streaming completions with mock server."""

    server: HTTPServer
    server_thread: Thread

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = HTTPServer(("127.0.0.1", 0), MockLLMHandler)
        cls.server_thread = Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        host, port = self.server.server_address
        self.client = LLMClient(
            base_url=f"http://{host}:{port}",
            timeout=5.0,
            max_retries=1,
        )
        MockLLMHandler.status_code = 200
        MockLLMHandler.error_message = None

    def test_complete_returns_response(self) -> None:
        MockLLMHandler.response_data = {
            "id": "chatcmpl-123",
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello, world!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 10,
                "total_tokens": 15,
            },
            "created": 1234567890,
        }

        response = self.client.complete([{"role": "user", "content": "Hi"}])

        self.assertIsInstance(response, CompletionResponse)
        self.assertEqual(response.id, "chatcmpl-123")
        self.assertEqual(response.content, "Hello, world!")
        self.assertEqual(len(response.choices), 1)
        self.assertIsNotNone(response.usage)
        self.assertEqual(response.usage.total_tokens, 15)

    def test_complete_sends_correct_payload(self) -> None:
        MockLLMHandler.response_data = {
            "id": "test",
            "model": "test-model",
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}
            ],
            "created": 0,
        }

        self.client.complete(
            [{"role": "user", "content": "Hello"}],
            temperature=0.5,
            max_tokens=100,
        )

        sent_payload = json.loads(self.server.received_body)
        self.assertEqual(sent_payload["messages"], [{"role": "user", "content": "Hello"}])
        self.assertEqual(sent_payload["temperature"], 0.5)
        self.assertEqual(sent_payload["max_tokens"], 100)
        self.assertFalse(sent_payload["stream"])

    def test_complete_4xx_raises_without_retry(self) -> None:
        MockLLMHandler.status_code = 400
        MockLLMHandler.error_message = "Bad Request"

        with self.assertRaises(LLMClientError) as ctx:
            self.client.complete([{"role": "user", "content": "Hi"}])
        self.assertIn("400", str(ctx.exception))

    def test_complete_5xx_retries_and_fails(self) -> None:
        MockLLMHandler.status_code = 500
        MockLLMHandler.error_message = "Internal Server Error"

        client = LLMClient(
            base_url=f"http://{self.server.server_address[0]}:{self.server.server_address[1]}",
            timeout=2.0,
            max_retries=2,
            retry_delay=0.1,
        )

        with self.assertRaises(LLMClientError) as ctx:
            client.complete([{"role": "user", "content": "Hi"}])
        self.assertIn("2 attempts", str(ctx.exception))


class LLMClientStreamTests(unittest.TestCase):
    """Tests for streaming completions with mock server."""

    server: HTTPServer
    server_thread: Thread

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = HTTPServer(("127.0.0.1", 0), MockLLMHandler)
        cls.server_thread = Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        host, port = self.server.server_address
        self.client = LLMClient(
            base_url=f"http://{host}:{port}",
            timeout=5.0,
            max_retries=1,
        )
        MockLLMHandler.status_code = 200
        MockLLMHandler.error_message = None

    def test_stream_yields_chunks(self) -> None:
        MockLLMHandler.stream_chunks = [
            {
                "id": "chunk-1",
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            },
            {
                "id": "chunk-2",
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
            },
            {
                "id": "chunk-3",
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"content": " world"}, "finish_reason": "stop"}],
            },
        ]

        chunks = list(self.client.stream([{"role": "user", "content": "Hi"}]))

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].delta.role, "assistant")
        self.assertEqual(chunks[1].delta.content, "Hello")
        self.assertEqual(chunks[2].delta.content, " world")
        self.assertEqual(chunks[2].finish_reason, "stop")

    def test_stream_text_yields_content_only(self) -> None:
        MockLLMHandler.stream_chunks = [
            {
                "id": "chunk-1",
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            },
            {
                "id": "chunk-2",
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
            },
            {
                "id": "chunk-3",
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"content": " world"}, "finish_reason": "stop"}],
            },
        ]

        text_chunks = list(self.client.stream_text([{"role": "user", "content": "Hi"}]))

        self.assertEqual(text_chunks, ["Hello", " world"])


class LLMClientHealthTests(unittest.TestCase):
    """Tests for health check functionality."""

    server: HTTPServer
    server_thread: Thread

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = HTTPServer(("127.0.0.1", 0), MockLLMHandler)
        cls.server_thread = Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_health_check_returns_true_when_reachable(self) -> None:
        host, port = self.server.server_address
        client = LLMClient(base_url=f"http://{host}:{port}")
        self.assertTrue(client.health_check())

    def test_health_check_returns_false_when_unreachable(self) -> None:
        client = LLMClient(base_url="http://localhost:19999")
        self.assertFalse(client.health_check())


if __name__ == "__main__":
    unittest.main()
