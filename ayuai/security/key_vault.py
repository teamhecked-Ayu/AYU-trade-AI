"""Security primitives for encrypted per-user provider credentials."""
from __future__ import annotations
import base64
import hashlib
import os
from dataclasses import dataclass
from cryptography.fernet import Fernet, InvalidToken

class CredentialError(RuntimeError):
    pass

def _fernet_from_secret(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))

@dataclass
class EncryptedCredential:
    user_id: str
    provider: str
    ciphertext: str

class KeyVault:
    """In-memory vault interface.

    The encryption key must come from server-only configuration. Browser code
    must never receive it. Persistence can replace the backing dictionary later.
    """
    def __init__(self, master_secret: str | None = None) -> None:
        secret = master_secret or os.getenv("AYUAI_KEY_VAULT_SECRET")
        if not secret:
            raise CredentialError("AYUAI_KEY_VAULT_SECRET is required.")
        self._cipher = _fernet_from_secret(secret)
        self._store: dict[tuple[str, str], EncryptedCredential] = {}

    def store(self, user_id: str, provider: str, api_key: str) -> None:
        if not user_id or not provider or not api_key:
            raise CredentialError("user_id, provider and api_key are required.")
        ciphertext = self._cipher.encrypt(api_key.encode()).decode()
        self._store[(user_id, provider)] = EncryptedCredential(user_id, provider, ciphertext)

    def retrieve(self, user_id: str, provider: str) -> str:
        record = self._store.get((user_id, provider))
        if not record:
            raise CredentialError("Credential not found.")
        try:
            return self._cipher.decrypt(record.ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise CredentialError("Credential cannot be decrypted.") from exc

    def delete(self, user_id: str, provider: str) -> bool:
        return self._store.pop((user_id, provider), None) is not None

    def list_providers(self, user_id: str) -> list[str]:
        return sorted(provider for uid, provider in self._store if uid == user_id)
