from __future__ import annotations
import os
from .base import AIProvider, ProviderResponse

class MissingProviderKey(RuntimeError):
    pass

class EnvProvider(AIProvider):
    env_key: str

    def _key(self) -> str:
        value = os.getenv(self.env_key)
        if not value:
            raise MissingProviderKey(f"{self.env_key} is not configured")
        return value
