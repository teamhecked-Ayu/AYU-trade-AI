from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ProviderResponse:
    provider: str
    model: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

class AIProvider(ABC):
    name: str

    @abstractmethod
    async def analyze(self, prompt: str, *, system_prompt: str | None = None) -> ProviderResponse:
        raise NotImplementedError
