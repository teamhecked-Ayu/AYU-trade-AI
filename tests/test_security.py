import pytest
from ayuai.security import CredentialError, KeyVault

def test_keys_are_encrypted_and_user_isolated():
    vault = KeyVault("test-secret")
    vault.store("user-a", "openai", "secret-a")
    vault.store("user-b", "openai", "secret-b")
    assert vault.retrieve("user-a", "openai") == "secret-a"
    assert vault.retrieve("user-b", "openai") == "secret-b"
    assert vault.delete("user-a", "openai")
    with pytest.raises(CredentialError):
        vault.retrieve("user-a", "openai")
