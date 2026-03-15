"""Golden and unit tests for prompt_builder.build_messages.

All tests are pure Python — no network, no Docker required.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.agent_gateway.src.config_loader import PromptConfig
from services.agent_gateway.src.context_builder import AgentContext, PersonalityContext
from services.agent_gateway.src.prompt_builder import (
    _RAG_BLOCK_FOOTER,
    _RAG_BLOCK_HEADER,
    build_messages,
)
from services.agent_gateway.src.rag_retrieval import RagMatch
from services.agent_gateway.src.state_machine import ConversationStage, SessionState


def _make_context(
    *,
    token_budget: int = 4096,
    max_history_turns: int = 10,
    max_rag_snippets: int = 5,
) -> AgentContext:
    return AgentContext(
        tenant_id="silver_pine",
        business_name="Silver Pine Wellness",
        business_industry="Healthcare",
        greeting="Thank you for calling Silver Pine Wellness. How can I help you today?",
        rules=(
            "Never give medical advice or diagnosis.",
            "Confirm caller phone number before ending the call.",
        ),
        personality=PersonalityContext(tone="empathetic", pace="calm", formality="professional"),
        rag_collection="silver_pine_docs",
        rag_top_k=5,
        calendar_provider="google",
        email_provider="gmail",
        prompt_config=PromptConfig(
            token_budget=token_budget,
            max_history_turns=max_history_turns,
            max_rag_snippets=max_rag_snippets,
        ),
    )


def _make_state(history: list[dict[str, str]] | None = None) -> SessionState:
    return SessionState(
        session_id="test-session",
        stage=ConversationStage.ANSWER_QUESTION,
        history=history or [],
    )


def _make_match(text: str, index: int = 0) -> RagMatch:
    return RagMatch(
        document=text,
        metadata={"tenant_id": "silver_pine", "source_file": "faq.md", "chunk_index": index},
        distance=0.1 * (index + 1),
    )


class MessageOrderTests(unittest.TestCase):
    def test_system_is_first(self) -> None:
        msgs = build_messages(_make_context(), _make_state(), [], "Hello")
        self.assertEqual(msgs[0]["role"], "system")

    def test_final_user_is_last(self) -> None:
        msgs = build_messages(_make_context(), _make_state(), [], "Hello")
        self.assertEqual(msgs[-1]["role"], "user")
        self.assertEqual(msgs[-1]["content"], "Hello")

    def test_rag_block_comes_before_history(self) -> None:
        history = [{"role": "user", "content": "prior turn"}]
        rag = [_make_match("clinic is open 9-5")]
        msgs = build_messages(_make_context(), _make_state(history), rag, "Hello")
        roles = [m["role"] for m in msgs]
        # system, rag user, history user, final user
        self.assertEqual(roles[0], "system")
        rag_idx = next(i for i, m in enumerate(msgs) if _RAG_BLOCK_HEADER in m.get("content", ""))
        history_idx = next(
            i for i, m in enumerate(msgs) if m.get("content") == "prior turn"
        )
        final_idx = next(i for i, m in enumerate(msgs) if m.get("content") == "Hello")
        self.assertLess(rag_idx, history_idx)
        self.assertLess(history_idx, final_idx)

    def test_no_rag_when_matches_empty(self) -> None:
        msgs = build_messages(_make_context(), _make_state(), [], "Hello")
        for m in msgs:
            self.assertNotIn(_RAG_BLOCK_HEADER, m.get("content", ""))

    def test_history_order_is_chronological(self) -> None:
        history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
        ]
        msgs = build_messages(_make_context(), _make_state(history), [], "Hello")
        history_contents = [m["content"] for m in msgs if m["content"] in {"first", "second", "third"}]
        self.assertEqual(history_contents, ["first", "second", "third"])


class SystemMessageContentTests(unittest.TestCase):
    def _system(self, **kwargs: object) -> str:
        ctx = _make_context(**kwargs)  # type: ignore[arg-type]
        return build_messages(ctx, _make_state(), [], "Hi")[0]["content"]

    def test_contains_business_name(self) -> None:
        self.assertIn("Silver Pine Wellness", self._system())

    def test_contains_industry(self) -> None:
        self.assertIn("Healthcare", self._system())

    def test_contains_personality_fields(self) -> None:
        content = self._system()
        self.assertIn("empathetic", content)
        self.assertIn("calm", content)
        self.assertIn("professional", content)

    def test_contains_all_rules(self) -> None:
        content = self._system()
        self.assertIn("Never give medical advice or diagnosis.", content)
        self.assertIn("Confirm caller phone number before ending the call.", content)

    def test_contains_rag_usage_instructions(self) -> None:
        content = self._system()
        self.assertIn("RETRIEVED CONTEXT", content)

    def test_contains_greeting(self) -> None:
        content = self._system()
        self.assertIn("Thank you for calling Silver Pine Wellness", content)


class RagBlockTests(unittest.TestCase):
    def test_rag_block_has_header_and_footer(self) -> None:
        rag = [_make_match("We are open 9-5")]
        msgs = build_messages(_make_context(), _make_state(), rag, "Hi")
        rag_msg = next(m for m in msgs if _RAG_BLOCK_HEADER in m["content"])
        self.assertIn(_RAG_BLOCK_FOOTER, rag_msg["content"])

    def test_rag_block_contains_snippet_text(self) -> None:
        rag = [_make_match("We are open 9-5")]
        msgs = build_messages(_make_context(), _make_state(), rag, "Hi")
        rag_msg = next(m for m in msgs if _RAG_BLOCK_HEADER in m["content"])
        self.assertIn("We are open 9-5", rag_msg["content"])

    def test_rag_block_role_is_user(self) -> None:
        rag = [_make_match("snippet")]
        msgs = build_messages(_make_context(), _make_state(), rag, "Hi")
        rag_msg = next(m for m in msgs if _RAG_BLOCK_HEADER in m["content"])
        self.assertEqual(rag_msg["role"], "user")

    def test_multiple_snippets_all_present(self) -> None:
        rag = [_make_match(f"snippet {i}", i) for i in range(3)]
        msgs = build_messages(_make_context(), _make_state(), rag, "Hi")
        rag_msg = next(m for m in msgs if _RAG_BLOCK_HEADER in m["content"])
        for i in range(3):
            self.assertIn(f"snippet {i}", rag_msg["content"])


class MaxRagSnippetsTests(unittest.TestCase):
    def test_snippets_capped_at_max_rag_snippets(self) -> None:
        ctx = _make_context(max_rag_snippets=2)
        rag = [_make_match(f"snippet {i}", i) for i in range(5)]
        msgs = build_messages(ctx, _make_state(), rag, "Hi")
        rag_msg = next((m for m in msgs if _RAG_BLOCK_HEADER in m["content"]), None)
        self.assertIsNotNone(rag_msg)
        assert rag_msg is not None
        self.assertIn("snippet 0", rag_msg["content"])
        self.assertIn("snippet 1", rag_msg["content"])
        self.assertNotIn("snippet 2", rag_msg["content"])

    def test_extra_matches_beyond_cap_are_ignored(self) -> None:
        ctx = _make_context(max_rag_snippets=1)
        rag = [_make_match(f"s{i}", i) for i in range(10)]
        msgs = build_messages(ctx, _make_state(), rag, "Hi")
        rag_msg = next((m for m in msgs if _RAG_BLOCK_HEADER in m["content"]), None)
        self.assertIsNotNone(rag_msg)
        assert rag_msg is not None
        self.assertIn("s0", rag_msg["content"])
        for i in range(1, 10):
            self.assertNotIn(f"s{i}", rag_msg["content"])


class MaxHistoryTurnsTests(unittest.TestCase):
    def test_history_capped_at_max_history_turns(self) -> None:
        ctx = _make_context(max_history_turns=2)
        # 5 pairs = 10 messages; only last 2 pairs (4 messages) should appear
        history = []
        for i in range(5):
            history.append({"role": "user", "content": f"user-{i}"})
            history.append({"role": "assistant", "content": f"asst-{i}"})
        msgs = build_messages(ctx, _make_state(history), [], "Hi")
        contents = {m["content"] for m in msgs}
        # last 2 pairs
        self.assertIn("user-3", contents)
        self.assertIn("asst-3", contents)
        self.assertIn("user-4", contents)
        self.assertIn("asst-4", contents)
        # earlier pairs dropped
        self.assertNotIn("user-0", contents)
        self.assertNotIn("user-1", contents)
        self.assertNotIn("user-2", contents)

    def test_history_within_cap_is_fully_included(self) -> None:
        ctx = _make_context(max_history_turns=10)
        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
        ]
        msgs = build_messages(ctx, _make_state(history), [], "Hi")
        contents = {m["content"] for m in msgs}
        self.assertIn("q1", contents)
        self.assertIn("a1", contents)


class TokenBudgetTests(unittest.TestCase):
    def test_oldest_history_dropped_first_under_budget(self) -> None:
        # Very tight budget: forces history trimming
        ctx = _make_context(token_budget=300, max_history_turns=20)
        history = []
        for i in range(10):
            history.append({"role": "user", "content": f"user-message-{i:02d}"})
            history.append({"role": "assistant", "content": f"assistant-reply-{i:02d}"})
        msgs = build_messages(ctx, _make_state(history), [], "Current question?")
        # system and final user must always be present
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["content"], "Current question?")
        # oldest entries (user-message-00, assistant-reply-00) should be gone
        contents = {m["content"] for m in msgs}
        self.assertNotIn("user-message-00", contents)

    def test_rag_trimmed_when_history_cannot_be_reduced_further(self) -> None:
        # Budget so tight that even with no history, RAG must be trimmed
        ctx = _make_context(token_budget=280, max_history_turns=1, max_rag_snippets=5)
        # No history, but 5 large snippets
        rag = [_make_match("A" * 200, i) for i in range(5)]
        msgs = build_messages(ctx, _make_state(), rag, "Hi")
        # system and final user always present
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["content"], "Hi")

    def test_system_and_final_user_always_present(self) -> None:
        ctx = _make_context(token_budget=256)
        rag = [_make_match("X" * 500, i) for i in range(5)]
        history = [{"role": "user", "content": "Y" * 500}]
        msgs = build_messages(ctx, _make_state(history), rag, "Z")
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1]["content"], "Z")


class DeterminismTests(unittest.TestCase):
    def test_same_input_produces_identical_output(self) -> None:
        ctx = _make_context()
        state = _make_state([
            {"role": "user", "content": "What are your hours?"},
            {"role": "assistant", "content": "We are open 9-5."},
        ])
        rag = [_make_match("We are open Monday-Friday 9am-5pm.", 0)]
        transcript = "Can I schedule an appointment?"

        result_a = json.dumps(build_messages(ctx, state, rag, transcript), sort_keys=True)
        result_b = json.dumps(build_messages(ctx, state, rag, transcript), sort_keys=True)
        self.assertEqual(result_a, result_b)

    def test_transcript_is_stripped_in_output(self) -> None:
        msgs = build_messages(_make_context(), _make_state(), [], "  hello world  ")
        self.assertEqual(msgs[-1]["content"], "hello world")


if __name__ == "__main__":
    unittest.main()
