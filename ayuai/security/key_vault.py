"""Security primitives for encrypted per-user provider credentials."""
from __future__ import annotations
import base64, hashlib, os
from cryptography.fernet import Fernet, InvalidToken

class CredentialError(RuntimeError): pass

def _fernet_from_secret(secret: str) -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))

class KeyVault:
    def __init__(self, master_secret: str | None = None) -> None:
        secret = master_secret or os.getenv("AYUAI_KEY_VAULT_SECRET")
        if not secret: raise CredentialError("AYUAI_KEY_VAULT_SECRET is required.")
        self._cipher = _fernet_from_secret(secret)

    def encrypt(self, api_key: str) -> str:
        if not api_key: raise CredentialError("API key is required.")
        return self._cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try: return self._cipher.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc: raise CredentialError("Credential cannot be decrypted.") from exc
