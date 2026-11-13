"""Perplexity provider adapter. Runtime API key only."""
from __future__ import annotations
import asyncio
import requests
from .base import AIProvider, ProviderResponse

class PerplexityProvider(AIProvider):
    name = "perplexity"
    endpoint = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str, model: str = "sonar") -> None:
        if not api_key:
            raise ValueError("A Perplexity API key is required.")
        self.api_key, self.model = api_key, model

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        return await asyncio.to_thread(self._analyze_sync, prompt, system_prompt)

    def _analyze_sync(self, prompt: str, system_prompt: str | None) -> ProviderResponse:
        messages = ([{"role": "system", "content": system_prompt}] if system_prompt else [])
        messages.append({"role": "user", "content": prompt})
        response = requests.post(self.endpoint, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                                 json={"model": self.model, "messages": messages, "temperature": 0.2}, timeout=60)
        response.raise_for_status()
        data = response.json()
        return ProviderResponse(provider=self.name, model=self.model,
                                content=data["choices"][0]["message"].get("content", ""),
                                metadata={"id": data.get("id"), "citations": data.get("citations", [])})
