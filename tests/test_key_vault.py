import os
from ayuai.security.key_vault import KeyVault

def test_vault_encrypts_and_retrieves():
    vault = KeyVault("test-secret")
    vault.store("user-1", "openai", "secret-api-key")
    assert vault.retrieve("user-1", "openai") == "secret-api-key"
    assert "secret-api-key" not in vault._store[("user-1", "openai")].ciphertext
