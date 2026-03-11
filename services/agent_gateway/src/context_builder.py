from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from services.agent_gateway.src.config_loader import TenantAgentConfig, load_all_tenant_configs


@dataclass(frozen=True)
class PersonalityContext:
    tone: str
    pace: str
    formality: str


@dataclass(frozen=True)
class AgentContext:
    tenant_id: str
    business_name: str
    business_industry: str
    greeting: str
    rules: tuple[str, ...]
    personality: PersonalityContext
    rag_collection: str
    rag_top_k: int
    calendar_provider: str
    email_provider: str


def build_agent_context(config: TenantAgentConfig) -> AgentContext:
    return AgentContext(
        tenant_id=config.tenant_id,
        business_name=config.business_profile.name,
        business_industry=config.business_profile.industry,
        greeting=config.agent_behavior.greeting,
        rules=config.agent_behavior.rules,
        personality=PersonalityContext(
            tone=config.personality.tone,
            pace=config.personality.pace,
            formality=config.personality.formality,
        ),
        rag_collection=config.rag.collection,
        rag_top_k=config.rag.top_k,
        calendar_provider=config.integrations.calendar.provider,
        email_provider=config.integrations.email.provider,
    )


def build_context_snapshot(configs: dict[str, TenantAgentConfig]) -> MappingProxyType[str, AgentContext]:
    contexts = {tenant_id: build_agent_context(config) for tenant_id, config in configs.items()}
    return MappingProxyType(contexts)


@lru_cache(maxsize=1)
def load_startup_context(config_dir: str) -> MappingProxyType[str, AgentContext]:
    """
    Load and cache tenant runtime context once per service process.

    Startup path should call this one time and then reuse the returned immutable mapping.
    """
    configs = load_all_tenant_configs(Path(config_dir))
    return build_context_snapshot(configs)
