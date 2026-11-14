from ayuai.security.key_vault import KeyVault

def test_vault_encrypt_decrypt():
    vault=KeyVault("test-secret")
    ciphertext=vault.encrypt("secret-key")
    assert ciphertext!="secret-key"
    assert vault.decrypt(ciphertext)=="secret-key"
