"""Google Gemini provider adapter. Runtime API key only."""
from __future__ import annotations
import asyncio
import requests
from .base import AIProvider, ProviderResponse

class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        if not api_key:
            raise ValueError("A Gemini API key is required.")
        self.api_key, self.model = api_key, model

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        return await asyncio.to_thread(self._analyze_sync, prompt, system_prompt)

    def _analyze_sync(self, prompt: str, system_prompt: str | None) -> ProviderResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2}}
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        response = requests.post(url, params={"key": self.api_key}, json=body, timeout=60)
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        content = "".join(part.get("text", "") for part in parts)
        return ProviderResponse(provider=self.name, model=self.model, content=content,
                                metadata={"usage": data.get("usageMetadata", {})})
