import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ayuai.database.connection import Base
from ayuai.database.repositories_credentials import ProviderCredentialRepository
from ayuai.security import CredentialError, KeyVault


@pytest.mark.asyncio
async def test_provider_credentials_are_encrypted_and_user_isolated():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    vault = KeyVault("test-secret")

    async with Session() as session:
        repository = ProviderCredentialRepository(session, vault)
        await repository.store("user-a", "openai", "secret-a")
        await repository.store("user-b", "openai", "secret-b")
        await session.commit()

        assert await repository.get_decrypted("user-a") == {"openai": "secret-a"}
        assert await repository.get_decrypted("user-b") == {"openai": "secret-b"}
        assert await repository.list_providers("user-a") == ["openai"]

        assert await repository.delete("user-a", "openai")
        await session.commit()
        assert await repository.get_decrypted("user-a") == {}
        assert await repository.get_decrypted("user-b") == {"openai": "secret-b"}

    await engine.dispose()


def test_key_vault_rejects_invalid_ciphertext():
    vault = KeyVault("test-secret")
    with pytest.raises(CredentialError):
        vault.decrypt("not-a-valid-ciphertext")


def test_key_vault_requires_master_secret(monkeypatch):
    monkeypatch.delenv("AYUAI_KEY_VAULT_SECRET", raising=False)
    with pytest.raises(CredentialError):
        KeyVault()
