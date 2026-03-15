from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from services.agent_gateway.src.context_builder import (
    AgentContext,
    build_context_snapshot,
    load_startup_context,
)


VALID_YAML = """\
tenant_id: silver_pine
business_profile:
  name: Silver Pine Wellness
  industry: Healthcare
personality:
  tone: empathetic
  pace: calm
  formality: professional
agent_behavior:
  greeting: Thank you for calling Silver Pine Wellness. How can I help today?
  rules:
    - Never provide medical diagnosis
    - Confirm callback phone number before ending call
rag:
  collection: silver_pine_docs
  top_k: 5
integrations:
  calendar:
    provider: google
  email:
    provider: gmail
prompt:
  token_budget: 4096
  max_history_turns: 10
  max_rag_snippets: 5
"""


class ContextBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        load_startup_context.cache_clear()

    def tearDown(self) -> None:
        load_startup_context.cache_clear()

    def test_build_context_snapshot_returns_immutable_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            (config_dir / "silver_pine.yaml").write_text(VALID_YAML, encoding="utf-8")
            contexts = load_startup_context(str(config_dir))

            self.assertIsInstance(contexts, MappingProxyType)
            self.assertIn("silver_pine", contexts)
            self.assertIsInstance(contexts["silver_pine"], AgentContext)
            self.assertEqual("Silver Pine Wellness", contexts["silver_pine"].business_name)
            self.assertEqual(("Never provide medical diagnosis", "Confirm callback phone number before ending call"), contexts["silver_pine"].rules)

            with self.assertRaises(TypeError):
                contexts["new_tenant"] = contexts["silver_pine"]  # type: ignore[index]
            with self.assertRaises(dataclasses.FrozenInstanceError):
                contexts["silver_pine"].business_name = "Changed Name"  # type: ignore[misc]

    def test_load_startup_context_caches_by_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            tenant_file = config_dir / "silver_pine.yaml"
            tenant_file.write_text(VALID_YAML, encoding="utf-8")

            first = load_startup_context(str(config_dir))
            tenant_file.write_text(
                VALID_YAML.replace("Silver Pine Wellness", "Mutated After Startup"),
                encoding="utf-8",
            )
            second = load_startup_context(str(config_dir))

            self.assertIs(first, second)
            self.assertEqual("Silver Pine Wellness", second["silver_pine"].business_name)

    def test_build_context_snapshot_from_empty_configs(self) -> None:
        snapshot = build_context_snapshot({})
        self.assertIsInstance(snapshot, MappingProxyType)
        self.assertEqual(0, len(snapshot))


if __name__ == "__main__":
    unittest.main()
