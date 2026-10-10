"""
RELIEFOS Lite — AI Resilience, Rate Limiting & Circuit Breaker Module
Manages request throttling, exponential backoff retries, and provider circuit-breaking.
"""

import time
import asyncio
from typing import Callable, Any, Optional
import logging

from app.services.ai.exceptions import (
    AIRateLimitError, AITimeoutError, AIProviderError, AIAuthenticationError
)

logger = logging.getLogger("reliefos.ai.resilience")


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter per minute."""
    def __init__(self, max_requests_per_minute: int = 30):
        self.max_requests = max_requests_per_minute
        self.timestamps = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquires a rate limit token or raises AIRateLimitError."""
        async with self._lock:
            now = time.time()
            cutoff = now - 60.0
            # Evict timestamps older than 60 seconds
            self.timestamps = [t for t in self.timestamps if t > cutoff]

            if len(self.timestamps) >= self.max_requests:
                oldest = self.timestamps[0]
                wait_seconds = round(60.0 - (now - oldest), 1)
                raise AIRateLimitError(
                    f"AI request rate limit reached ({self.max_requests} req/min). Please wait {wait_seconds}s before retrying.",
                    details={"retry_after_seconds": max(wait_seconds, 1.0)}
                )

            self.timestamps.append(now)

    def current_load(self) -> int:
        now = time.time()
        cutoff = now - 60.0
        return len([t for t in self.timestamps if t > cutoff])


class CircuitBreaker:
    """
    Prevents repeated calls to failing upstream providers.
    Transitions: CLOSED -> OPEN (after max_failures) -> HALF_OPEN (after recovery_timeout).
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = asyncio.Lock()

    @property
    def recovery_timeout_seconds(self) -> float:
        return self.recovery_timeout

    def reset(self):
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0

    async def check(self):
        async with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if (now - self.last_failure_time) > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioned to HALF_OPEN (probing provider)")
                else:
                    remaining = round(self.recovery_timeout - (now - self.last_failure_time), 1)
                    raise AIProviderError(
                        f"AI provider circuit breaker is OPEN due to repeated failures. Cooldown: {remaining}s.",
                        details={"state": "OPEN", "cooldown_remaining_seconds": remaining}
                    )

    async def record_success(self):
        async with self._lock:
            self.failure_count = 0
            self.state = "CLOSED"

    async def record_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(
                    f"Circuit breaker tripped to OPEN after {self.failure_count} consecutive failures."
                )


async def execute_with_retry(
    operation: Callable[[], Any],
    max_retries: int = 2,
    base_delay: float = 0.5,
    timeout_seconds: float = 15.0
) -> Any:
    """
    Executes an async operation with strict timeout and exponential backoff retry.
    Safe against non-retryable errors (e.g. 401 auth failures).
    """
    attempt = 0
    while True:
        try:
            return await asyncio.wait_for(operation(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            attempt += 1
            logger.warning(f"AI operation timed out after {timeout_seconds}s (attempt {attempt}/{max_retries + 1})")
            if attempt > max_retries:
                raise AITimeoutError(
                    f"AI provider timed out after {timeout_seconds} seconds across {max_retries + 1} attempts."
                )
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))

        except AIAuthenticationError:
            # Never retry auth errors
            raise

        except Exception as exc:
            attempt += 1
            logger.warning(f"AI operation encountered error: {str(exc)} (attempt {attempt}/{max_retries + 1})")
            if attempt > max_retries:
                raise AIProviderError(f"AI provider call failed: {str(exc)}") from exc
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
