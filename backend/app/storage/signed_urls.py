"""Signed URL helpers."""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import urlencode


def _sign(secret: str, file_id: str, expires_at: int) -> str:
    payload = f"{file_id}:{expires_at}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def generate_signed_url(file_id: str, *, secret: str, ttl_seconds: int = 3600, base_path: str | None = None) -> dict:
    expires_at = int(time.time()) + max(ttl_seconds, 1)
    token = _sign(secret, file_id, expires_at)
    path = base_path or f"/api/v1/files/{file_id}/download"
    query = urlencode({"token": token, "expires": expires_at})
    return {
        "url": f"{path}?{query}",
        "expires_at": expires_at,
        "token": token,
    }


def verify_signed_url(file_id: str, token: str, expires_at: int, *, secret: str) -> bool:
    if expires_at < int(time.time()):
        return False
    expected = _sign(secret, file_id, expires_at)
    return hmac.compare_digest(expected, token)
