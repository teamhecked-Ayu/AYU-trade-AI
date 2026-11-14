"""Build AYUAI providers from server-only environment configuration."""
from __future__ import annotations
import os
from ayuai.providers.provider_manager import ProviderManager

def build_provider_manager() -> ProviderManager:
    manager = ProviderManager()
    from ayuai.providers.openai_provider import OpenAIProvider
    from ayuai.providers.compatible_provider import DeepSeekProvider, PerplexityProvider
    from ayuai.providers.anthropic_provider import AnthropicProvider
    from ayuai.providers.gemini_provider import GeminiProvider

    for env, provider in [
        ("OPENAI_API_KEY", OpenAIProvider),
        ("ANTHROPIC_API_KEY", AnthropicProvider),
        ("DEEPSEEK_API_KEY", DeepSeekProvider),
        ("PERPLEXITY_API_KEY", PerplexityProvider),
        ("GEMINI_API_KEY", GeminiProvider),
    ]:
        if os.getenv(env):
            manager.register(provider())
    if not manager.providers:
        raise RuntimeError("No AI provider API keys are configured on the server.")
    return manager
