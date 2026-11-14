"""OpenAI provider adapter. API keys are supplied at runtime and are never stored here."""
from __future__ import annotations
import asyncio
from .base import AIProvider, ProviderResponse

class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4.1-mini") -> None:
        if not api_key:
            raise ValueError("An OpenAI API key is required.")
        self.api_key = api_key
        self.model = model

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        return await asyncio.to_thread(self._analyze_sync, prompt, system_prompt)

    def _analyze_sync(self, prompt: str, system_prompt: str | None) -> ProviderResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("OpenAI support requires: pip install openai") from exc

        client = OpenAI(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        return ProviderResponse(
            provider=self.name,
            model=self.model,
            content=response.choices[0].message.content or "",
            metadata={"id": getattr(response, "id", None)},
        )
