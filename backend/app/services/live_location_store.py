"""Short-lived live positions of field collectors.

Only the *latest* position per user is kept and it expires after TTL_SECONDS,
so no location history is stored. Redis is used when REDIS_URL is set; an
in-process dict is the fallback for tests and local development.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

TTL_SECONDS = 120
_PREFIX = "dxcon:liveloc:"

_lock = threading.Lock()
_memory: dict[str, tuple[float, dict[str, Any]]] = {}


def _redis(app):
    url = (app.config.get("REDIS_URL") or "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
    except Exception:
        return None


def put(app, user_id: str, payload: dict[str, Any]) -> None:
    client = _redis(app)
    if client is not None:
        try:
            client.setex(_PREFIX + user_id, TTL_SECONDS, json.dumps(payload))
            return
        except Exception:
            pass
    with _lock:
        _memory[user_id] = (time.time() + TTL_SECONDS, payload)


def remove(app, user_id: str) -> None:
    client = _redis(app)
    if client is not None:
        try:
            client.delete(_PREFIX + user_id)
        except Exception:
            pass
    with _lock:
        _memory.pop(user_id, None)


def list_all(app) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    client = _redis(app)
    if client is not None:
        try:
            keys = list(client.scan_iter(match=_PREFIX + "*", count=200))
            if keys:
                for raw in client.mget(keys):
                    if raw:
                        items.append(json.loads(raw))
        except Exception:
            pass
    now = time.time()
    with _lock:
        for uid in [k for k, (exp, _) in _memory.items() if exp <= now]:
            _memory.pop(uid, None)
        items.extend(p for _, p in _memory.values())
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        prev = seen.get(item["user_id"])
        if prev is None or item["recorded_at"] > prev["recorded_at"]:
            seen[item["user_id"]] = item
    return sorted(seen.values(), key=lambda i: i["email"])


def clear_memory() -> None:
    with _lock:
        _memory.clear()
