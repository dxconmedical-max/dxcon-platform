"""Durable queue provider selection (memory for dev/test, Redis for production)."""

from __future__ import annotations

import json
import uuid
from collections import deque

SUPPORTED_PROVIDERS = {"memory", "redis"}
PRODUCTION_QUEUE_PROVIDER = "redis"
DEFAULT_QUEUE_KEY = "dxcon:queue:jobs"
DEFAULT_PROCESSING_SUFFIX = ":processing"


def provider_name(app) -> str:
    return (app.config.get("QUEUE_PROVIDER") or "memory").strip().lower() or "memory"


def processing_key_for(queue_key: str) -> str:
    return f"{queue_key}{DEFAULT_PROCESSING_SUFFIX}"


class MemoryQueue:
    """Process-local queue with claim/ack semantics. Allowed in development/tests only."""

    def __init__(self):
        self._items = deque()
        self._inflight = {}  # claim_token -> raw JSON string

    def ping(self):
        return True

    def enqueue(self, payload: dict):
        self._items.appendleft(json.dumps(payload))
        return True

    def claim(self, timeout=0):
        """Move one job into in-flight storage. Returns (payload, claim_token) or None."""
        if not self._items:
            return None
        raw = self._items.pop()
        token = str(uuid.uuid4())
        self._inflight[token] = raw
        return json.loads(raw), token

    def dequeue(self, timeout=0):
        """Compatibility wrapper: claim without ack. Prefer claim()/ack()/nack()."""
        claimed = self.claim(timeout=timeout)
        if claimed is None:
            return None
        payload, token = claimed
        # Leave claimed until ack/nack; expose token for callers that still use dequeue.
        payload = dict(payload)
        payload["__claim_token"] = token
        return payload

    def ack(self, claim_token: str) -> bool:
        if claim_token not in self._inflight:
            return False
        del self._inflight[claim_token]
        return True

    def nack(self, claim_token: str, *, requeue: bool = True) -> bool:
        raw = self._inflight.pop(claim_token, None)
        if raw is None:
            return False
        if requeue:
            # Preserve FIFO with enqueue (LPUSH) + claim (RPOP): requeue to the left end.
            self._items.appendleft(raw)
        return True

    def recover_inflight(self) -> int:
        """Requeue orphaned in-flight jobs (e.g. after worker crash)."""
        recovered = 0
        for token in list(self._inflight.keys()):
            raw = self._inflight.pop(token)
            self._items.appendleft(raw)
            recovered += 1
        return recovered

    @property
    def durable(self):
        return False

    @property
    def inflight_count(self) -> int:
        return len(self._inflight)

    @property
    def depth(self) -> int:
        return len(self._items)


class RedisQueue:
    """Redis list broker with claim/ack via a processing list."""

    def __init__(self, app, key=DEFAULT_QUEUE_KEY, processing_key=None):
        from app.infrastructure.redis_diagnostic import get_redis_client

        self.client = get_redis_client(app)
        self.key = key
        self.processing_key = processing_key or processing_key_for(key)

    def ping(self):
        return bool(self.client.ping())

    def enqueue(self, payload: dict):
        self.client.lpush(self.key, json.dumps(payload))
        return True

    def claim(self, timeout=0):
        """
        Atomically move one job from the main queue into the processing list.

        Uses BRPOPLPUSH / RPOPLPUSH so a crash after claim leaves the job in
        processing (recoverable), not lost.
        """
        if timeout and timeout > 0:
            raw = self.client.brpoplpush(self.key, self.processing_key, timeout=int(timeout))
        else:
            raw = self.client.rpoplpush(self.key, self.processing_key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw), raw

    def dequeue(self, timeout=0):
        """Compatibility wrapper: claim without ack. Prefer claim()/ack()/nack()."""
        claimed = self.claim(timeout=timeout)
        if claimed is None:
            return None
        payload, raw = claimed
        payload = dict(payload)
        payload["__claim_token"] = raw
        return payload

    def ack(self, claim_token: str) -> bool:
        """Remove a successfully processed job from the processing list."""
        removed = self.client.lrem(self.processing_key, 1, claim_token)
        return bool(removed)

    def nack(self, claim_token: str, *, requeue: bool = True) -> bool:
        """Drop the claim; optionally requeue the same payload for retry."""
        removed = self.client.lrem(self.processing_key, 1, claim_token)
        if not removed:
            return False
        if requeue:
            self.client.lpush(self.key, claim_token)
        return True

    def recover_inflight(self) -> int:
        """Move orphaned processing jobs back to the main queue (FIFO-safe)."""
        recovered = 0
        while True:
            raw = self.client.rpoplpush(self.processing_key, self.key)
            if raw is None:
                break
            recovered += 1
        return recovered

    @property
    def durable(self):
        return True


def get_queue(app):
    name = provider_name(app)
    ext = app.extensions.setdefault("dxcon_queue", {})
    cached = ext.get("client")
    if cached is not None and ext.get("provider") == name:
        return cached
    if name == "redis":
        client = RedisQueue(app)
    elif name == "memory":
        client = MemoryQueue()
    else:
        raise RuntimeError(f"Unsupported QUEUE_PROVIDER={name!r}")
    ext["client"] = client
    ext["provider"] = name
    return client
