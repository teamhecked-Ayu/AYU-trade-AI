"""Build the server-side AYUAI intelligence stack from configured providers."""
from __future__ import annotations
from ayuai.providers.provider_manager import ProviderManager


def build_provider_manager() -> ProviderManager:
    # Providers are registered by deployment configuration. Secrets never enter
    # Celery payloads or API responses.
    return ProviderManager()
