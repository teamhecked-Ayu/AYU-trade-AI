"""Provider failure classification and retry policy.

This module keeps provider failures isolated. Secrets are never included in
exceptions, logs, or returned job results.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from .base import AIProvider, ProviderResponse

T = TypeVar("T")

@dataclass(frozen=True)
class ProviderFailure:
    provider: str
    category: str
    retryable: bool

def classify_provider_error(provider: str, exc: Exception) -> ProviderFailure:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()

    if "auth" in name or "permission" in name or "api key" in message or "authentication" in message:
        return ProviderFailure(provider, "authentication", False)
    if "rate" in name or "429" in message or "rate limit" in message:
        return ProviderFailure(provider, "rate_limit", True)
    if isinstance(exc, TimeoutError) or "timeout" in name or "timed out" in message:
        return ProviderFailure(provider, "timeout", True)
    return ProviderFailure(provider, "unavailable", True)

async def analyze_with_retry(
    provider: AIProvider,
    prompt: str,
    *,
    system_prompt: str | None = None,
    attempts: int = 2,
    backoff_seconds: float = 0.25,
) -> ProviderResponse:
    attempts = max(1, attempts)
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return await provider.analyze(prompt, system_prompt=system_prompt)
        except Exception as exc:
            last_error = exc
            failure = classify_provider_error(provider.name, exc)
            if not failure.retryable or attempt == attempts - 1:
                raise
            await asyncio.sleep(backoff_seconds * (attempt + 1))

    raise RuntimeError("Provider analysis failed") from last_error
