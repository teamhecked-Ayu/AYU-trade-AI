"""Authentication primitives for AYUAI API access."""
from __future__ import annotations
import base64, hashlib, hmac, json, os, secrets, time

class AuthenticationError(RuntimeError):
    pass

def hash_password(password: str, salt: str | None = None) -> str:
    if len(password) < 10:
        raise AuthenticationError("Password must contain at least 10 characters.")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000)
    return salt + "$" + base64.b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        salt, expected = encoded.split("$", 1)
        actual = hash_password(password, salt).split("$", 1)[1]
        return hmac.compare_digest(actual, expected)
    except (ValueError, AuthenticationError):
        return False

def _secret() -> bytes:
    value = os.getenv("AYUAI_AUTH_SECRET")
    if not value:
        raise AuthenticationError("AYUAI_AUTH_SECRET is required.")
    return value.encode()

def issue_token(user_id: str, expires_in: int = 3600) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + expires_in}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), raw.encode(), hashlib.sha256).hexdigest()
    return raw + "." + signature

def verify_token(token: str) -> str:
    try:
        raw, signature = token.split(".", 1)
        expected = hmac.new(_secret(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise AuthenticationError("Invalid token.")
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
        if int(payload["exp"]) < int(time.time()):
            raise AuthenticationError("Token expired.")
        return str(payload["sub"])
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid token.") from exc
