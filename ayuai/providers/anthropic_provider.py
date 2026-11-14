from __future__ import annotations
import anthropic
from .common import EnvProvider
from .base import ProviderResponse

class AnthropicProvider(EnvProvider):
    name="anthropic"; env_key="ANTHROPIC_API_KEY"; model="claude-sonnet-4-5"

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        client = anthropic.AsyncAnthropic(api_key=self._key())
        response = await client.messages.create(model=self.model, max_tokens=2048, system=system_prompt or "", messages=[{"role":"user","content":prompt}])
        content = "".join(block.text for block in response.content if hasattr(block, "text"))
        return ProviderResponse(self.name, self.model, content)
