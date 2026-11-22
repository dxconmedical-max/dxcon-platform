"""Signed, expiring links that let a patient open ONE released result.

Stateless on purpose (no new table): the token is an itsdangerous signed value over
the order code and the result's release timestamp. A re-release changes the
timestamp, so older links stop working. Links expire after MAX_AGE_SECONDS.
"""

from __future__ import annotations

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

MAX_AGE_SECONDS = 30 * 24 * 3600
_SALT = "dxcon-result-link-v1"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def release_stamp(released_at) -> str:
    return released_at.isoformat() if released_at else ""


def make_token(order_code: str, released_at) -> str:
    return _serializer().dumps({"o": order_code, "r": release_stamp(released_at)})


def read_token(token: str) -> dict | None:
    try:
        data = _serializer().loads(token, max_age=MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict) or "o" not in data or "r" not in data:
        return None
    return data
