"""
RELIEFOS Lite — OpenAI / OpenAI-Compatible REST API Provider Adapter
Supports OpenAI, Ollama, vLLM, Azure, and OpenRouter endpoints.
"""

import time
import json
import logging
import httpx
from typing import Optional

from app.services.ai.providers.base import BaseAIProvider, RawAIResponse
from app.services.ai.exceptions import (
    AIProviderError, AIAuthenticationError, AIRateLimitError
)

logger = logging.getLogger("reliefos.ai.openai")


class OpenAIProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1"
    ):
        self.api_key = api_key.strip() if api_key else ""
        self._model = model.strip() if model else "gpt-4o-mini"
        self._base_url = base_url.rstrip("/") if base_url else "https://api.openai.com/v1"

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        temperature: float = 0.2,
        timeout_seconds: float = 15.0
    ) -> RawAIResponse:
        if not self.api_key:
            raise AIAuthenticationError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in backend/.env"
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(url, json=payload, headers=headers)
                latency_ms = round((time.time() - start_time) * 1000, 1)

                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise AIProviderError("OpenAI returned an empty choice list.")

                    text = choices[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})

                    return RawAIResponse(
                        provider=self.name,
                        model=self._model,
                        content=text,
                        latency_ms=latency_ms,
                        input_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                        is_mock=False
                    )

                elif resp.status_code == 401:
                    raise AIAuthenticationError("OpenAI authentication failed: Invalid API key.")
                elif resp.status_code == 429:
                    raise AIRateLimitError("OpenAI rate limit or credit quota exceeded.")
                else:
                    err_msg = resp.text[:200]
                    raise AIProviderError(f"OpenAI API error (HTTP {resp.status_code}): {err_msg}")

        except httpx.TimeoutException:
            raise
        except (AIAuthenticationError, AIRateLimitError, AIProviderError):
            raise
        except Exception as exc:
            raise AIProviderError(f"Network error communicating with OpenAI API: {str(exc)}") from exc

    async def health_check(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)
