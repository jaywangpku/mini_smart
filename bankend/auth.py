from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return f"pbkdf2_sha256${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        method, salt_raw, digest_raw = password_hash.split("$", 2)
    except ValueError:
        return False
    if method != "pbkdf2_sha256":
        return False
    salt = base64.urlsafe_b64decode(salt_raw.encode())
    expected = base64.urlsafe_b64decode(digest_raw.encode())
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return hmac.compare_digest(actual, expected)


def create_token(payload: dict[str, Any], secret: str, expire_hours: int) -> str:
    now = int(time.time())
    body = {**payload, "iat": now, "exp": now + max(1, expire_hours) * 3600}
    encoded = _b64(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode())
    signature = _sign(encoded, secret)
    return f"{encoded}.{signature}"


def decode_token(token: str, secret: str) -> dict[str, Any]:
    try:
        encoded, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("token 格式不合法") from exc
    if not hmac.compare_digest(signature, _sign(encoded, secret)):
        raise ValueError("token 签名不合法")
    try:
        payload = json.loads(base64.urlsafe_b64decode(_pad(encoded)).decode("utf-8"))
    except Exception as exc:
        raise ValueError("token 内容不合法") from exc
    if int(payload.get("exp") or 0) < int(time.time()):
        raise ValueError("token 已过期")
    return payload


def _sign(encoded_payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64(digest)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode()
