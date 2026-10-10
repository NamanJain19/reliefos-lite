"""
RELIEFOS Lite — Base AI Provider Abstract Interface
Defines the contract for interchangeable LLM backends (Gemini, OpenAI, Mock).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RawAIResponse(BaseModel):
    provider: str
    model: str
    content: str
    latency_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    is_mock: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAIProvider(ABC):
    """Abstract interface for all RELIEFOS Lite LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider code: 'gemini', 'openai', 'mock'."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Active model string."""
        pass

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """True if calling a live remote external API."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.2,
        timeout_seconds: float = 15.0
    ) -> RawAIResponse:
        """
        Executes inference and returns RawAIResponse.
        Must raise typed AI exceptions (AIAuthenticationError, AITimeoutError, AIProviderError).
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifies provider connectivity or credentials."""
        pass
