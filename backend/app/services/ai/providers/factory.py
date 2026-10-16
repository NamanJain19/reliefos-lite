"""
RELIEFOS Lite — AI Provider Factory
Manages provider instantiation, configuration resolution, and graceful failover.
"""

from typing import Optional, Dict, Any
import logging

from app.core.config import get_settings
from app.services.ai.providers.base import BaseAIProvider
from app.services.ai.providers.gemini import GeminiProvider
from app.services.ai.providers.openai import OpenAIProvider
from app.services.ai.providers.mock import MockAIProvider

logger = logging.getLogger("reliefos.ai.factory")

_PROVIDER_CACHE: Dict[str, BaseAIProvider] = {}


def get_provider_by_name(provider_name: str) -> BaseAIProvider:
    """
    Instantiates an AI provider instance given its canonical name.
    If credentials are missing, returns MockAIProvider with appropriate identifier.
    """
    settings = get_settings()
    target_provider = (provider_name or "").lower().strip()

    gemini_key = getattr(settings, "GEMINI_API_KEY", "")
    openai_key = getattr(settings, "OPENAI_API_KEY", "")

    if target_provider == "gemini":
        if gemini_key:
            return GeminiProvider(
                api_key=gemini_key,
                model=getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")
            )
        logger.info("GEMINI_API_KEY is not configured; using high-fidelity MockAIProvider")
        return MockAIProvider(model_name="mock-gemini-fallback")

    elif target_provider == "openai":
        if openai_key:
            return OpenAIProvider(
                api_key=openai_key,
                model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                base_url=getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
        logger.info("OPENAI_API_KEY is not configured; using high-fidelity MockAIProvider")
        return MockAIProvider(model_name="mock-openai-fallback")

    elif target_provider in ("mock", "deterministic"):
        return MockAIProvider(model_name="reliefos-deterministic-v1")

    else:
        logger.warning(f"Unrecognized AI provider '{provider_name}'. Defaulting to deterministic mock.")
        return MockAIProvider(model_name="reliefos-deterministic-v1")


def get_primary_ai_provider() -> BaseAIProvider:
    """Returns the primary AI provider as configured via AI_PROVIDER in settings."""
    settings = get_settings()
    primary_name = getattr(settings, "AI_PROVIDER", "gemini")
    return get_provider_by_name(primary_name)


def get_fallback_ai_provider() -> Optional[BaseAIProvider]:
    """
    Returns the secondary/fallback AI provider as configured via AI_FALLBACK_PROVIDER.
    Returns None if no fallback provider is configured or if it matches primary.
    """
    settings = get_settings()
    primary_name = (getattr(settings, "AI_PROVIDER", "gemini") or "").lower().strip()
    fallback_name = getattr(settings, "AI_FALLBACK_PROVIDER", None)

    if not fallback_name:
        return None

    clean_fallback = fallback_name.lower().strip()
    if clean_fallback in ("none", "disabled", "false", "", primary_name):
        return None

    return get_provider_by_name(clean_fallback)


def get_configured_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """
    Backward-compatible factory entrypoint.
    Returns the primary configured AI provider unless an explicit name is passed.
    """
    if provider_name:
        return get_provider_by_name(provider_name)
    return get_primary_ai_provider()
