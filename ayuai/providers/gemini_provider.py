from __future__ import annotations
from google import genai
from .common import EnvProvider
from .base import ProviderResponse

class GeminiProvider(EnvProvider):
    name="gemini"; env_key="GEMINI_API_KEY"; model="gemini-2.5-flash"

    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        client = genai.Client(api_key=self._key())
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = await client.aio.models.generate_content(model=self.model, contents=full_prompt)
        return ProviderResponse(self.name, self.model, response.text or "")
