from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from services.agent_gateway.src.config_loader import ConfigError, load_all_tenant_configs, runtime_snapshot


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


class ConfigLoaderTests(unittest.TestCase):
    def test_load_all_tenant_configs_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            (config_dir / "silver_pine.yaml").write_text(VALID_YAML, encoding="utf-8")
            (config_dir / "smith_law.yaml").write_text(
                VALID_YAML.replace("silver_pine", "smith_law").replace(
                    "Silver Pine Wellness", "Smith and Howard Law"
                ),
                encoding="utf-8",
            )

            configs = load_all_tenant_configs(config_dir)
            self.assertEqual({"silver_pine", "smith_law"}, set(configs))
            self.assertEqual("silver_pine_docs", configs["silver_pine"].rag.collection)
            self.assertEqual(2, len(configs["silver_pine"].agent_behavior.rules))

    def test_filename_must_match_tenant_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            (config_dir / "silver_pine.yaml").write_text(
                VALID_YAML.replace("tenant_id: silver_pine", "tenant_id: wrong_id"),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_all_tenant_configs(config_dir)

    def test_missing_required_section_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            (config_dir / "silver_pine.yaml").write_text(
                VALID_YAML.replace("agent_behavior:\n", ""),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_all_tenant_configs(config_dir)

    def test_runtime_snapshot_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            (config_dir / "silver_pine.yaml").write_text(VALID_YAML, encoding="utf-8")
            configs = load_all_tenant_configs(config_dir)

            snapshot = runtime_snapshot(configs)
            self.assertIsInstance(snapshot, MappingProxyType)
            with self.assertRaises(TypeError):
                snapshot["new_tenant"] = configs["silver_pine"]  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
