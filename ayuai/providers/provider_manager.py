"""Runs independent providers concurrently."""
from __future__ import annotations
import asyncio
from .base import AIProvider, ProviderResponse

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

    async def analyze_all(self, prompt: str, *, system_prompt: str | None = None) -> list[ProviderResponse]:
        if not self._providers:
            raise RuntimeError("No AI providers are registered.")
        tasks = [p.analyze(prompt, system_prompt=system_prompt) for p in self._providers.values()]
        return list(await asyncio.gather(*tasks))
