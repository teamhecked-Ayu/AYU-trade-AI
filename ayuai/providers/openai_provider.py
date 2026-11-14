from __future__ import annotations
from openai import AsyncOpenAI
from .common import EnvProvider
from .base import ProviderResponse

class OpenAIProvider(EnvProvider):
    name = "openai"
    env_key = "OPENAI_API_KEY"
    model = "gpt-4.1-mini"

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        client = AsyncOpenAI(api_key=self._key())
        messages = ([{"role":"system","content":system_prompt}] if system_prompt else []) + [{"role":"user","content":prompt}]
        response = await client.chat.completions.create(model=self.model, messages=messages)
        return ProviderResponse(self.name, self.model, response.choices[0].message.content or "")
