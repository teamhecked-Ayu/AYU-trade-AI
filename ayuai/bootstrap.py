"""Build AYUAI providers from server or per-user credentials."""
from __future__ import annotations
import os
from ayuai.providers.provider_manager import ProviderManager

def _provider_classes():
    from ayuai.providers.openai_provider import OpenAIProvider
    from ayuai.providers.compatible_provider import DeepSeekProvider, PerplexityProvider
    from ayuai.providers.anthropic_provider import AnthropicProvider
    from ayuai.providers.gemini_provider import GeminiProvider
    return {"openai":OpenAIProvider,"anthropic":AnthropicProvider,"deepseek":DeepSeekProvider,"perplexity":PerplexityProvider,"gemini":GeminiProvider}

def build_provider_manager(api_keys: dict[str,str] | None=None) -> ProviderManager:
    manager=ProviderManager()
    for name, provider in _provider_classes().items():
        key=(api_keys or {}).get(name) or os.getenv(f"{name.upper()}_API_KEY")
        if key:
            instance=provider()
            # Providers read their key through _key(); attach only to this worker instance.
            instance._user_api_key=key
            original=instance._key
            instance._key=lambda value=key: value
            manager.register(instance)
    if not manager.providers: raise RuntimeError("No AI provider credentials are configured.")
    return manager
