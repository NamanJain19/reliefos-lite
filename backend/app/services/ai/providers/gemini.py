"""
RELIEFOS Lite — Google Gemini REST API Provider Adapter
Direct, asynchronous client for Google Generative Language v1beta API.
Requires zero external heavyweight SDKs; uses high-performance httpx.AsyncClient.
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

logger = logging.getLogger("reliefos.ai.gemini")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key.strip() if api_key else ""
        self._model = model.strip() if model else "gemini-1.5-flash"

    @property
    def name(self) -> str:
        return "gemini"

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
                "Gemini API key is not configured. Set GEMINI_API_KEY in backend/.env"
            )

        models_to_try = [self._model]
        for alt in ("gemini-3.8-flash", "gemini-flash-lite-latest", "gemini-flash-latest", "gemini-1.5-flash"):
            if alt not in models_to_try:
                models_to_try.append(alt)

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "response_mime_type": "application/json"
            }
        }
        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        start_time = time.time()
        last_error = None

        for model_candidate in models_to_try:
            url = f"{GEMINI_BASE_URL}/{model_candidate}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    resp = await client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    latency_ms = round((time.time() - start_time) * 1000, 1)

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise AIProviderError("Gemini returned empty candidate list (content safety filtered).")

                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        usage = data.get("usageMetadata", {})

                        return RawAIResponse(
                            provider=self.name,
                            model=model_candidate,
                            content=text,
                            latency_ms=latency_ms,
                            input_tokens=usage.get("promptTokenCount"),
                            output_tokens=usage.get("candidatesTokenCount"),
                            is_mock=False
                        )

                    elif resp.status_code in (401, 403):
                        raise AIAuthenticationError(
                            f"Gemini API authentication failed (HTTP {resp.status_code}): Invalid or unauthorized API key."
                        )
                    elif resp.status_code == 429:
                        raise AIRateLimitError("Gemini quota or rate limit exceeded.")
                    elif resp.status_code in (503, 404) and model_candidate != models_to_try[-1]:
                        # Transient model spike or deprecated model name: try next fallback model
                        logger.warning(
                            f"Gemini model '{model_candidate}' returned HTTP {resp.status_code}. Attempting fallback model."
                        )
                        last_error = resp.text[:200]
                        continue
                    else:
                        err_msg = resp.text[:200]
                        raise AIProviderError(f"Gemini API error (HTTP {resp.status_code}): {err_msg}")

            except httpx.TimeoutException:
                raise
            except (AIAuthenticationError, AIRateLimitError, AIProviderError):
                raise
            except Exception as exc:
                if model_candidate == models_to_try[-1]:
                    raise AIProviderError(f"Network error communicating with Gemini API: {str(exc)}") from exc
                logger.warning(f"Error calling {model_candidate}: {exc}. Trying fallback model.")

        raise AIProviderError(f"All Gemini models exhausted. Last error: {last_error}")

    async def health_check(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)
