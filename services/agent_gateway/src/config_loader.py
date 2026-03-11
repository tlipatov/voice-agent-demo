from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when tenant YAML configuration is invalid."""


@dataclass(frozen=True)
class BusinessProfile:
    name: str
    industry: str


@dataclass(frozen=True)
class Personality:
    tone: str
    pace: str
    formality: str


@dataclass(frozen=True)
class AgentBehavior:
    greeting: str
    rules: tuple[str, ...]


@dataclass(frozen=True)
class RagConfig:
    collection: str
    top_k: int


@dataclass(frozen=True)
class ProviderConfig:
    provider: str


@dataclass(frozen=True)
class Integrations:
    calendar: ProviderConfig
    email: ProviderConfig


@dataclass(frozen=True)
class TenantAgentConfig:
    tenant_id: str
    business_profile: BusinessProfile
    personality: Personality
    agent_behavior: AgentBehavior
    rag: RagConfig
    integrations: Integrations


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"'{field_name}' must be a mapping")
    return value


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{field_name}' must be a non-empty string")
    return value.strip()


def _build_config(raw: dict[str, Any], source: Path) -> TenantAgentConfig:
    required_sections = (
        "tenant_id",
        "business_profile",
        "personality",
        "agent_behavior",
        "rag",
        "integrations",
    )
    for section in required_sections:
        if section not in raw:
            raise ConfigError(f"Missing required section '{section}' in {source}")

    tenant_id = _require_string(raw["tenant_id"], "tenant_id")

    business_profile = _require_mapping(raw["business_profile"], "business_profile")
    personality = _require_mapping(raw["personality"], "personality")
    agent_behavior = _require_mapping(raw["agent_behavior"], "agent_behavior")
    rag = _require_mapping(raw["rag"], "rag")
    integrations = _require_mapping(raw["integrations"], "integrations")

    rules_raw = agent_behavior.get("rules")
    if not isinstance(rules_raw, list) or not rules_raw:
        raise ConfigError("'agent_behavior.rules' must be a non-empty list")
    rules = tuple(_require_string(item, "agent_behavior.rules[]") for item in rules_raw)

    top_k = rag.get("top_k")
    if not isinstance(top_k, int) or top_k < 1:
        raise ConfigError("'rag.top_k' must be an integer >= 1")

    calendar = _require_mapping(integrations.get("calendar"), "integrations.calendar")
    email = _require_mapping(integrations.get("email"), "integrations.email")

    return TenantAgentConfig(
        tenant_id=tenant_id,
        business_profile=BusinessProfile(
            name=_require_string(business_profile.get("name"), "business_profile.name"),
            industry=_require_string(business_profile.get("industry"), "business_profile.industry"),
        ),
        personality=Personality(
            tone=_require_string(personality.get("tone"), "personality.tone"),
            pace=_require_string(personality.get("pace"), "personality.pace"),
            formality=_require_string(personality.get("formality"), "personality.formality"),
        ),
        agent_behavior=AgentBehavior(
            greeting=_require_string(agent_behavior.get("greeting"), "agent_behavior.greeting"),
            rules=rules,
        ),
        rag=RagConfig(
            collection=_require_string(rag.get("collection"), "rag.collection"),
            top_k=top_k,
        ),
        integrations=Integrations(
            calendar=ProviderConfig(provider=_require_string(calendar.get("provider"), "integrations.calendar.provider")),
            email=ProviderConfig(provider=_require_string(email.get("provider"), "integrations.email.provider")),
        ),
    )


def load_tenant_config(path: Path) -> TenantAgentConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigError(f"Top-level YAML object must be a mapping in {path}")
    config = _build_config(payload, source=path)
    expected_stem = path.stem
    if config.tenant_id != expected_stem:
        raise ConfigError(
            f"tenant_id '{config.tenant_id}' must match filename '{expected_stem}' in {path}"
        )
    return config


def load_all_tenant_configs(config_dir: Path) -> dict[str, TenantAgentConfig]:
    if not config_dir.exists():
        raise ConfigError(f"Config directory does not exist: {config_dir}")
    if not config_dir.is_dir():
        raise ConfigError(f"Config path is not a directory: {config_dir}")

    configs: dict[str, TenantAgentConfig] = {}
    for path in sorted(config_dir.glob("*.yaml")):
        config = load_tenant_config(path)
        if config.tenant_id in configs:
            raise ConfigError(f"Duplicate tenant_id '{config.tenant_id}'")
        configs[config.tenant_id] = config

    if not configs:
        raise ConfigError(f"No tenant YAML files found in {config_dir}")
    return configs


def runtime_snapshot(configs: dict[str, TenantAgentConfig]) -> MappingProxyType[str, TenantAgentConfig]:
    """
    Build an immutable mapping loaded at startup.

    Agent runtime behavior should only change after YAML edits + restart.
    """
    return MappingProxyType(dict(configs))
