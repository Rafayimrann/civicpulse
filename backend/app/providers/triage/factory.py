"""
Selects the active TriageProvider from settings.triage_provider
(TRIAGE_PROVIDER env var). This is the only place in the codebase that
knows all four provider classes exist - everything downstream depends only
on the TriageProvider Protocol.
"""
from __future__ import annotations

from app.config import Settings
from app.providers.cache_provider import CacheProvider
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def build_triage_provider(settings: Settings, cache: CacheProvider) -> TriageProvider:
    match settings.triage_provider:
        case "llm":
            return LLMTriage(
                api_key=settings.groq_api_key,
                base_url=settings.groq_base_url,
                model=settings.groq_model,
                cache=cache,
                timeout_seconds=settings.llm_timeout_seconds,
                cache_ttl_seconds=settings.triage_cache_ttl_seconds,
            )
        case "ollama":
            return OllamaTriage(base_url=settings.ollama_base_url, model=settings.ollama_model)
        case "rules":
            return RuleBasedTriage()
        case "simulated":
            return SimulatedTriage(force_failure=settings.simulated_force_failure)
        case other:
            raise ValueError(f"Unknown TRIAGE_PROVIDER: {other!r}")
