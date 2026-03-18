#!/usr/bin/env python3
"""Smoke test script for vLLM client.

This script verifies the vLLM client can:
1. Connect to the vLLM server
2. Generate non-streaming completions
3. Generate streaming completions

Usage:
    python scripts/smoke_test_llm.py
    VLLM_BASE_URL=http://localhost:11434 python scripts/smoke_test_llm.py
    python scripts/smoke_test_llm.py --url http://192.168.69.14:11434 --model llama3.2:3b-instruct-q4_K_M
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agent_gateway.src.llm_client import (
    LLMClient,
    LLMClientError,
)


def print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f" {text}")
    print('=' * 60)


def print_success(text: str) -> None:
    print(f"[OK] {text}")


def print_failure(text: str) -> None:
    print(f"[FAIL] {text}")


def print_info(text: str) -> None:
    print(f"[INFO] {text}")


def test_health_check(client: LLMClient) -> bool:
    print_header("Health Check")
    print_info(f"Base URL: {client.base_url}")
    print_info(f"Model: {client.model}")

    if client.health_check():
        print_success("vLLM server is reachable")
        return True
    else:
        print_failure("vLLM server is not reachable")
        return False


def test_non_streaming(client: LLMClient) -> bool:
    print_header("Non-Streaming Completion")

    messages = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": "What is 2 + 2? Answer with just the number."},
    ]

    print_info("Sending completion request...")
    print_info(f"Messages: {messages}")

    try:
        response = client.complete(
            messages=messages,
            temperature=0.1,
            max_tokens=10,
        )

        print_success(f"Response ID: {response.id}")
        print_success(f"Model: {response.model}")
        print_success(f"Content: {response.content!r}")
        print_success(f"Finish reason: {response.choices[0].finish_reason}")

        if response.usage:
            print_info(f"Tokens: prompt={response.usage.prompt_tokens}, "
                      f"completion={response.usage.completion_tokens}, "
                      f"total={response.usage.total_tokens}")

        return True

    except LLMClientError as e:
        print_failure(f"Completion failed: {e}")
        return False
    except Exception as e:
        print_failure(f"Unexpected error: {e}")
        return False


def test_streaming(client: LLMClient) -> bool:
    print_header("Streaming Completion")

    messages = [
        {"role": "user", "content": "Count from 1 to 5."},
    ]

    print_info("Sending streaming request...")
    print_info(f"Messages: {messages}")

    try:
        chunks = []
        full_text = ""

        print("\n--- Streaming output ---")
        for chunk in client.stream(
            messages=messages,
            temperature=0.1,
            max_tokens=30,
        ):
            chunks.append(chunk)
            if chunk.delta.content:
                print(chunk.delta.content, end="", flush=True)
                full_text += chunk.delta.content

        print("\n--- End streaming ---\n")

        print_success(f"Received {len(chunks)} chunks")
        print_success(f"Full text: {full_text!r}")

        finish_reasons = [c.finish_reason for c in chunks if c.finish_reason]
        if finish_reasons:
            print_success(f"Finish reason: {finish_reasons[-1]}")

        return True

    except LLMClientError as e:
        print_failure(f"Streaming failed: {e}")
        return False
    except Exception as e:
        print_failure(f"Unexpected error: {e}")
        return False


def test_stream_text(client: LLMClient) -> bool:
    print_header("Stream Text (Convenience Method)")

    messages = [
        {"role": "user", "content": "Say 'hello world' exactly."},
    ]

    print_info("Using stream_text convenience method...")

    try:
        text_chunks = list(
            client.stream_text(
                messages=messages,
                temperature=0.1,
                max_tokens=10,
            )
        )

        full_text = "".join(text_chunks)
        print_success(f"Received {len(text_chunks)} text chunks")
        print_success(f"Full text: {full_text!r}")

        return True

    except LLMClientError as e:
        print_failure(f"Stream text failed: {e}")
        return False
    except Exception as e:
        print_failure(f"Unexpected error: {e}")
        return False


def test_agent_style_prompt(client: LLMClient) -> bool:
    print_header("Agent-Style Prompt Test")

    system_prompt = """You are an AI receptionist for Silver Pine Wellness Center.

Personality:
- Tone: Empathetic and caring
- Pace: Calm and measured
- Formality: Professional but warm

Rules:
- Never give medical advice
- Be helpful and courteous
- Keep responses concise

Respond to the caller's question."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What are your business hours?"},
    ]

    print_info("Testing with agent-style system prompt...")

    try:
        response = client.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        print_success(f"Response: {response.content}")
        return True

    except LLMClientError as e:
        print_failure(f"Agent prompt test failed: {e}")
        return False
    except Exception as e:
        print_failure(f"Unexpected error: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test for vLLM client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default=os.getenv("VLLM_BASE_URL", "http://192.168.69.14:11434"),
        help="vLLM server base URL",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("VLLM_MODEL", "llama3.2:3b-instruct-q4_K_M"),
        help="Model to use",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Request timeout in seconds",
    )

    args = parser.parse_args()

    print_header("vLLM Client Smoke Test")
    print_info(f"URL: {args.url}")
    print_info(f"Model: {args.model}")
    print_info(f"Timeout: {args.timeout}s")

    client = LLMClient(
        base_url=args.url,
        model=args.model,
        timeout=args.timeout,
    )

    tests = [
        ("Health Check", test_health_check),
        ("Non-Streaming", test_non_streaming),
        ("Streaming", test_streaming),
        ("Stream Text", test_stream_text),
        ("Agent-Style Prompt", test_agent_style_prompt),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn(client)
            results.append((name, passed))
        except Exception as e:
            print_failure(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    print_header("Summary")
    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, p in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
