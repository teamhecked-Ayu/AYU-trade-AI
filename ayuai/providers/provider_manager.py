"""Runs independent providers concurrently and isolates individual provider failures."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from .base import AIProvider, ProviderResponse

@dataclass
class ProviderFailure:
    provider: str
    error: str

@dataclass
class ProviderRun:
    responses: list[ProviderResponse]
    failures: list[ProviderFailure]

class ProviderManager:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(self._providers)

    async def analyze_all_detailed(self, prompt: str, *, system_prompt: str | None = None) -> ProviderRun:
        if not self._providers:
            raise RuntimeError("No AI providers are registered.")
        names = list(self._providers)
        tasks = [self._providers[name].analyze(prompt, system_prompt=system_prompt) for name in names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses: list[ProviderResponse] = []
        failures: list[ProviderFailure] = []
        for name, result in zip(names, results):
            if isinstance(result, BaseException):
                failures.append(ProviderFailure(provider=name, error=str(result)))
            else:
                responses.append(result)
        return ProviderRun(responses=responses, failures=failures)

    async def analyze_all(self, prompt: str, *, system_prompt: str | None = None) -> list[ProviderResponse]:
        run = await self.analyze_all_detailed(prompt, system_prompt=system_prompt)
        if not run.responses:
            details = "; ".join(f"{item.provider}: {item.error}" for item in run.failures)
            raise RuntimeError(f"All AI providers failed. {details}")
        return run.responses
