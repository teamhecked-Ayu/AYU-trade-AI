from __future__ import annotations
from openai import AsyncOpenAI
from .common import EnvProvider
from .base import ProviderResponse

class CompatibleProvider(EnvProvider):
    base_url: str
    model: str

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        client = AsyncOpenAI(api_key=self._key(), base_url=self.base_url)
        messages = ([{"role":"system","content":system_prompt}] if system_prompt else []) + [{"role":"user","content":prompt}]
        response = await client.chat.completions.create(model=self.model, messages=messages)
        return ProviderResponse(self.name, self.model, response.choices[0].message.content or "")

class DeepSeekProvider(CompatibleProvider):
    name="deepseek"; env_key="DEEPSEEK_API_KEY"; base_url="https://api.deepseek.com"; model="deepseek-chat"

class PerplexityProvider(CompatibleProvider):
    name="perplexity"; env_key="PERPLEXITY_API_KEY"; base_url="https://api.perplexity.ai"; model="sonar"
