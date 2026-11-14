"""Encrypted per-user provider credential repository."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ayuai.database.models import ProviderCredentialModel
from ayuai.security.key_vault import KeyVault

ALLOWED_PROVIDERS = {"openai", "anthropic", "deepseek", "perplexity", "gemini"}

class ProviderCredentialRepository:
    def __init__(self, session: AsyncSession, vault: KeyVault) -> None:
        self.session = session
        self.vault = vault

    async def store(self, user_id: str, provider: str, api_key: str) -> None:
        provider = provider.strip().lower()
        if provider not in ALLOWED_PROVIDERS:
            raise ValueError("Unsupported provider.")
        self.vault.store(user_id, provider, api_key)
        ciphertext = self.vault._store[(user_id, provider)].ciphertext
        row = (await self.session.execute(select(ProviderCredentialModel).where(
            ProviderCredentialModel.user_id == user_id,
            ProviderCredentialModel.provider == provider,
        ))).scalar_one_or_none()
        if row:
            row.ciphertext = ciphertext
        else:
            self.session.add(ProviderCredentialModel(user_id=user_id, provider=provider, ciphertext=ciphertext))

    async def list_providers(self, user_id: str) -> list[str]:
        rows = (await self.session.execute(select(ProviderCredentialModel.provider).where(
            ProviderCredentialModel.user_id == user_id
        ))).scalars().all()
        return sorted(rows)

    async def delete(self, user_id: str, provider: str) -> bool:
        provider = provider.strip().lower()
        row = (await self.session.execute(select(ProviderCredentialModel).where(
            ProviderCredentialModel.user_id == user_id,
            ProviderCredentialModel.provider == provider,
        ))).scalar_one_or_none()
        if not row:
            return False
        await self.session.delete(row)
        self.vault.delete(user_id, provider)
        return True
