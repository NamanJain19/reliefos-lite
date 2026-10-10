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


def get_configured_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """
    Factory function returning the active AI provider based on settings or explicit override.
    Safely resolves credentials and defaults to MockAIProvider if live keys are absent.
    """
    settings = get_settings()
    target_provider = (provider_name or getattr(settings, "AI_PROVIDER", "mock")).lower().strip()

    gemini_key = getattr(settings, "GEMINI_API_KEY", "")
    openai_key = getattr(settings, "OPENAI_API_KEY", "")

    if target_provider == "gemini":
        if gemini_key:
            return GeminiProvider(
                api_key=gemini_key,
                model=getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
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

    else:
        return MockAIProvider(model_name="reliefos-deterministic-v1")
