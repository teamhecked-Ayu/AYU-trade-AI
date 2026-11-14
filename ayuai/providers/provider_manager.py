"""Runs independent providers concurrently with timeouts and failure isolation."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from .base import AIProvider, ProviderResponse
from .resilience import analyze_with_retry, classify_provider_error

@dataclass
class ProviderFailure:
    provider: str
    error: str
    category: str = "unavailable"
    retryable: bool = True

@dataclass
class ProviderRun:
    responses: list[ProviderResponse]
    failures: list[ProviderFailure]

class ProviderManager:
    def __init__(self, timeout_seconds: float = 30.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self.timeout_seconds = timeout_seconds
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(self._providers)

    @staticmethod
    def _safe_error(error: BaseException) -> str:
        if isinstance(error, asyncio.TimeoutError):
            return "Provider request timed out."
        # Do not expose raw exception details, which can contain credentials or internals.
        return f"{type(error).__name__}: provider request failed."

    async def _run_provider(self, provider: AIProvider, prompt: str, system_prompt: str | None):
        return await asyncio.wait_for(
            analyze_with_retry(provider, prompt, system_prompt=system_prompt),
            timeout=self.timeout_seconds,
        )

    async def analyze_all_detailed(self, prompt: str, *, system_prompt: str | None = None) -> ProviderRun:
        if not self._providers:
            raise RuntimeError("No AI providers are registered.")
        names = list(self._providers)
        tasks = [
            self._run_provider(self._providers[name], prompt, system_prompt)
            for name in names
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses: list[ProviderResponse] = []
        failures: list[ProviderFailure] = []
        for name, result in zip(names, results):
            if isinstance(result, BaseException):
                failure = classify_provider_error(name, result)
                failures.append(ProviderFailure(provider=name, error=self._safe_error(result), category=failure.category, retryable=failure.retryable))
            else:
                responses.append(result)
        return ProviderRun(responses=responses, failures=failures)

    async def analyze_all(self, prompt: str, *, system_prompt: str | None = None) -> list[ProviderResponse]:
        run = await self.analyze_all_detailed(prompt, system_prompt=system_prompt)
        if not run.responses:
            raise RuntimeError("All AI providers failed.")
        return run.responses
