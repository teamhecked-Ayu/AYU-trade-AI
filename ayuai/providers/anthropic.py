"""Anthropic Claude provider adapter. Runtime API key only."""
from __future__ import annotations
import asyncio
import requests
from .base import AIProvider, ProviderResponse

class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest") -> None:
        if not api_key:
            raise ValueError("An Anthropic API key is required.")
        self.api_key, self.model = api_key, model

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        return await asyncio.to_thread(self._analyze_sync, prompt, system_prompt)

    def _analyze_sync(self, prompt: str, system_prompt: str | None) -> ProviderResponse:
        payload = {"model": self.model, "max_tokens": 2048, "temperature": 0.2,
                   "messages": [{"role": "user", "content": prompt}]}
        if system_prompt:
            payload["system"] = system_prompt
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        return ProviderResponse(provider=self.name, model=self.model, content=content,
                                metadata={"id": data.get("id"), "stop_reason": data.get("stop_reason")})
