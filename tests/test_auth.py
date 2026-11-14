import pytest
from ayuai.security.auth import AuthenticationError, hash_password, issue_token, verify_password, verify_token

def test_password_hash_and_signed_token(monkeypatch):
    monkeypatch.setenv("AYUAI_AUTH_SECRET", "test-secret")
    encoded = hash_password("long-enough-password")
    assert verify_password("long-enough-password", encoded)
    assert not verify_password("wrong-password", encoded)
    assert verify_token(issue_token("user-1")) == "user-1"

def test_tampered_token_is_rejected(monkeypatch):
    monkeypatch.setenv("AYUAI_AUTH_SECRET", "test-secret")
    token = issue_token("user-1")
    with pytest.raises(AuthenticationError):
        verify_token(token + "x")
