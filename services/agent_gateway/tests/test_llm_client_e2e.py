"""End-to-end tests for the vLLM client against a live vLLM server."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://192.168.69.14:11434")
VLLM_MODEL = os.getenv("VLLM_MODEL", "llama3.2:3b-instruct-q4_K_M")


def _vllm_is_healthy(url: str) -> bool:
    """Check if vLLM service is reachable."""
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"{url}/v1/models", timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


class LLMClientE2ETests(unittest.TestCase):
    """E2E tests for the LLM client against a live vLLM server."""

    def setUp(self) -> None:
        if not _vllm_is_healthy(VLLM_BASE_URL):
            self.skipTest(f"vLLM service is not reachable at {VLLM_BASE_URL}/v1/models")

        from services.agent_gateway.src.llm_client import LLMClient

        self.client = LLMClient(
            base_url=VLLM_BASE_URL,
            model=VLLM_MODEL,
            timeout=60.0,
        )

    def test_health_check_passes(self) -> None:
        """Health check should return True when service is running."""
        self.assertTrue(self.client.health_check())

    def test_complete_returns_valid_response(self) -> None:
        """Non-streaming completion should return a valid response."""
        from services.agent_gateway.src.llm_client import CompletionResponse

        response = self.client.complete(
            messages=[{"role": "user", "content": "Say 'Hello' and nothing else."}],
            temperature=0.1,
            max_tokens=10,
        )

        self.assertIsInstance(response, CompletionResponse)
        self.assertTrue(len(response.content) > 0)
        self.assertTrue(len(response.choices) >= 1)

    def test_complete_with_system_message(self) -> None:
        """Completion with system message should work."""
        response = self.client.complete(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2? Answer with just the number."},
            ],
            temperature=0.1,
            max_tokens=5,
        )

        self.assertTrue(len(response.content) > 0)
        self.assertIn("4", response.content)

    def test_complete_with_conversation_history(self) -> None:
        """Completion with multi-turn conversation should work."""
        response = self.client.complete(
            messages=[
                {"role": "user", "content": "My name is Alice."},
                {"role": "assistant", "content": "Nice to meet you, Alice!"},
                {"role": "user", "content": "What is my name?"},
            ],
            temperature=0.1,
            max_tokens=20,
        )

        self.assertTrue(len(response.content) > 0)
        self.assertIn("Alice", response.content)

    def test_stream_yields_chunks(self) -> None:
        """Streaming completion should yield chunks."""
        from services.agent_gateway.src.llm_client import StreamChunk

        chunks = list(
            self.client.stream(
                messages=[{"role": "user", "content": "Count from 1 to 3."}],
                temperature=0.1,
                max_tokens=20,
            )
        )

        self.assertTrue(len(chunks) > 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, StreamChunk)

    def test_stream_text_concatenates_to_valid_response(self) -> None:
        """stream_text should yield text that concatenates to a valid response."""
        text_chunks = list(
            self.client.stream_text(
                messages=[{"role": "user", "content": "Say 'test' and nothing else."}],
                temperature=0.1,
                max_tokens=10,
            )
        )

        full_text = "".join(text_chunks)
        self.assertTrue(len(full_text) > 0)

    def test_stream_matches_complete_output(self) -> None:
        """Streaming and non-streaming should produce similar outputs."""
        messages = [{"role": "user", "content": "What is the capital of France?"}]

        complete_response = self.client.complete(
            messages=messages,
            temperature=0.1,
            max_tokens=20,
        )

        stream_text = "".join(
            self.client.stream_text(
                messages=messages,
                temperature=0.1,
                max_tokens=20,
            )
        )

        self.assertIn("Paris", complete_response.content)
        self.assertIn("Paris", stream_text)

    def test_temperature_affects_output(self) -> None:
        """Different temperatures should potentially produce different outputs."""
        messages = [{"role": "user", "content": "Write a random word."}]

        responses_low_temp = [
            self.client.complete(messages, temperature=0.0, max_tokens=5).content
            for _ in range(2)
        ]

        self.assertEqual(
            responses_low_temp[0],
            responses_low_temp[1],
            "Temperature 0.0 should produce deterministic output",
        )


class LLMClientPromptIntegrationTests(unittest.TestCase):
    """Tests for LLM client integration with prompt_builder output."""

    def setUp(self) -> None:
        if not _vllm_is_healthy(VLLM_BASE_URL):
            self.skipTest(f"vLLM service is not reachable at {VLLM_BASE_URL}/v1/models")

        from services.agent_gateway.src.llm_client import LLMClient

        self.client = LLMClient(
            base_url=VLLM_BASE_URL,
            model=VLLM_MODEL,
            timeout=60.0,
        )

    def test_accepts_prompt_builder_message_format(self) -> None:
        """LLM client should accept messages in the format produced by prompt_builder."""
        messages = [
            {
                "role": "system",
                "content": "You are a receptionist for Silver Pine Wellness. Be helpful and professional.",
            },
            {"role": "user", "content": "What are your hours?"},
        ]

        response = self.client.complete(messages, temperature=0.5, max_tokens=50)

        self.assertTrue(len(response.content) > 0)
        self.assertEqual(response.choices[0].message.role, "assistant")

    def test_handles_long_system_prompt(self) -> None:
        """LLM client should handle longer system prompts."""
        long_context = """
        You are an AI receptionist for Silver Pine Wellness Center.

        Business Information:
        - Name: Silver Pine Wellness
        - Industry: Healthcare
        - Location: 123 Main Street

        Personality:
        - Tone: Empathetic and caring
        - Pace: Calm and measured
        - Formality: Professional but warm

        Rules:
        - Never give medical advice
        - Always confirm caller phone number
        - Be patient with elderly callers

        Current Context:
        The caller is asking about appointment scheduling.
        """

        messages = [
            {"role": "system", "content": long_context},
            {"role": "user", "content": "I'd like to book an appointment."},
        ]

        response = self.client.complete(messages, temperature=0.5, max_tokens=100)

        self.assertTrue(len(response.content) > 0)


if __name__ == "__main__":
    unittest.main()
