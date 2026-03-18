"""vLLM client for agent_gateway.

Provides streaming and non-streaming chat completions via the OpenAI-compatible
vLLM /v1/chat/completions endpoint.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Generator, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMClientError(Exception):
    """Raised when LLM completion request fails."""


@dataclass(frozen=True)
class ChatMessage:
    """A single message in a chat conversation."""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class CompletionChoice:
    """A single choice in a completion response."""

    index: int
    message: ChatMessage
    finish_reason: str | None


@dataclass(frozen=True)
class CompletionUsage:
    """Token usage statistics for a completion."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class CompletionResponse:
    """Response from a non-streaming chat completion."""

    id: str
    model: str
    choices: tuple[CompletionChoice, ...]
    usage: CompletionUsage | None
    created: int

    @property
    def content(self) -> str:
        """Return the content of the first choice, or empty string if none."""
        if self.choices:
            return self.choices[0].message.content
        return ""


@dataclass(frozen=True)
class StreamDelta:
    """A single delta chunk from a streaming response."""

    role: str | None
    content: str


@dataclass(frozen=True)
class StreamChunk:
    """A single chunk from a streaming completion."""

    id: str
    model: str
    delta: StreamDelta
    finish_reason: str | None


class LLMClient:
    """Client for vLLM OpenAI-compatible /v1/chat/completions endpoint.

    Supports both streaming and non-streaming completions with configurable
    timeout and retry behavior.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the LLM client.

        Args:
            base_url: Base URL for vLLM server. Defaults to VLLM_BASE_URL env var
                or http://localhost:11434.
            model: Model identifier. Defaults to VLLM_MODEL env var
                or llama3.2:3b-instruct-q4_K_M.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts on transient failures.
            retry_delay: Base delay between retries (doubles on each retry).
        """
        raw_url = base_url or os.getenv("VLLM_BASE_URL", "http://localhost:11434")
        self._base_url = raw_url.rstrip("/")
        self._model = model or os.getenv("VLLM_MODEL", "llama3.2:3b-instruct-q4_K_M")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def model(self) -> str:
        return self._model

    def _validate_messages(self, messages: list[dict[str, str]]) -> None:
        """Validate messages format."""
        if not messages:
            raise ValueError("messages must not be empty")
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"messages[{i}] must be a dict")
            if "role" not in msg:
                raise ValueError(f"messages[{i}] missing 'role' key")
            if "content" not in msg:
                raise ValueError(f"messages[{i}] missing 'content' key")

    def _build_request(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Request:
        """Build HTTP request for chat completions."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        data = json.dumps(payload).encode()
        return Request(
            url=f"{self._base_url}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    def _execute_with_retry(
        self,
        request: Request,
        stream: bool = False,
    ) -> Any:
        """Execute request with retry logic.

        Returns:
            For non-streaming: parsed JSON response dict.
            For streaming: response object (caller must read).
        """
        last_error: Exception | None = None
        delay = self._retry_delay

        for attempt in range(self._max_retries):
            try:
                response = urlopen(request, timeout=self._timeout)
                if stream:
                    return response
                body = response.read().decode()
                return json.loads(body)
            except HTTPError as exc:
                # Don't retry 4xx errors
                if 400 <= exc.code < 500:
                    raise LLMClientError(
                        f"LLM request failed with status {exc.code}: {exc.reason}"
                    ) from exc
                last_error = exc
            except URLError as exc:
                last_error = exc
            except json.JSONDecodeError as exc:
                raise LLMClientError(
                    f"Invalid JSON response from LLM service: {exc}"
                ) from exc
            except TimeoutError as exc:
                last_error = exc

            if attempt < self._max_retries - 1:
                time.sleep(delay)
                delay *= 2

        raise LLMClientError(
            f"LLM service unreachable at {self._base_url} after {self._max_retries} attempts: {last_error}"
        ) from last_error

    def _parse_completion_response(self, data: dict[str, Any]) -> CompletionResponse:
        """Parse a non-streaming completion response."""
        choices = []
        for choice_data in data.get("choices", []):
            msg_data = choice_data.get("message", {})
            message = ChatMessage(
                role=msg_data.get("role", "assistant"),
                content=msg_data.get("content", ""),
            )
            choice = CompletionChoice(
                index=choice_data.get("index", 0),
                message=message,
                finish_reason=choice_data.get("finish_reason"),
            )
            choices.append(choice)

        usage_data = data.get("usage")
        usage = None
        if usage_data:
            usage = CompletionUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        return CompletionResponse(
            id=data.get("id", ""),
            model=data.get("model", self._model),
            choices=tuple(choices),
            usage=usage,
            created=data.get("created", 0),
        )

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Generate a non-streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters passed to the API.

        Returns:
            CompletionResponse with generated content.

        Raises:
            ValueError: If messages are invalid.
            LLMClientError: If the request fails.
        """
        self._validate_messages(messages)
        request = self._build_request(
            messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        data = self._execute_with_retry(request, stream=False)
        return self._parse_completion_response(data)

    def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Generator[StreamChunk, None, None]:
        """Generate a streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters passed to the API.

        Yields:
            StreamChunk objects with delta content.

        Raises:
            ValueError: If messages are invalid.
            LLMClientError: If the request fails.
        """
        self._validate_messages(messages)
        request = self._build_request(
            messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        try:
            response = self._execute_with_retry(request, stream=True)
            yield from self._parse_stream(response)
        except LLMClientError:
            raise
        except Exception as exc:
            raise LLMClientError(
                f"Streaming completion failed: {exc}"
            ) from exc

    def _parse_stream(self, response: Any) -> Iterator[StreamChunk]:
        """Parse SSE stream from response."""
        try:
            for line in response:
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                line = line.strip()
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        chunk = self._parse_stream_chunk(data)
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue
        finally:
            response.close()

    def _parse_stream_chunk(self, data: dict[str, Any]) -> StreamChunk | None:
        """Parse a single streaming chunk."""
        choices = data.get("choices", [])
        if not choices:
            return None

        choice = choices[0]
        delta_data = choice.get("delta", {})
        delta = StreamDelta(
            role=delta_data.get("role"),
            content=delta_data.get("content", ""),
        )

        return StreamChunk(
            id=data.get("id", ""),
            model=data.get("model", self._model),
            delta=delta,
            finish_reason=choice.get("finish_reason"),
        )

    def stream_text(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Generate streaming text content only.

        Convenience method that yields only the text content from each chunk,
        filtering out empty content.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters passed to the API.

        Yields:
            String content from each chunk.
        """
        for chunk in self.stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            if chunk.delta.content:
                yield chunk.delta.content

    def health_check(self) -> bool:
        """Check if the LLM service is reachable.

        Returns:
            True if service responds, False otherwise.
        """
        try:
            request = Request(
                url=f"{self._base_url}/v1/models",
                headers={"Content-Type": "application/json"},
                method="GET",
            )
            with urlopen(request, timeout=5.0) as response:
                return response.status == 200
        except (URLError, TimeoutError):
            return False
