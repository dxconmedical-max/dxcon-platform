"""Focused P0 tests: durable claim/ack queue semantics (no job loss before success)."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.infrastructure.queue_provider import (
    DEFAULT_QUEUE_KEY,
    MemoryQueue,
    RedisQueue,
    get_queue,
    processing_key_for,
)
from app.operations.process_runtime import _drain_broker, run_worker_cycle


class _FakeRedisListClient:
    """Minimal Redis list client for claim/ack unit tests (no real Redis)."""

    def __init__(self):
        self.lists = {}

    def _list(self, key):
        return self.lists.setdefault(key, [])

    def ping(self):
        return True

    def lpush(self, key, value):
        self._list(key).insert(0, value)
        return len(self._list(key))

    def rpop(self, key):
        items = self._list(key)
        if not items:
            return None
        return items.pop()

    def rpoplpush(self, source, destination):
        raw = self.rpop(source)
        if raw is None:
            return None
        self._list(destination).insert(0, raw)
        return raw

    def brpoplpush(self, source, destination, timeout=0):
        return self.rpoplpush(source, destination)

    def lrem(self, key, count, value):
        items = self._list(key)
        removed = 0
        if count == 0:
            while value in items:
                items.remove(value)
                removed += 1
            return removed
        direction = 1 if count > 0 else -1
        remaining = abs(count)
        if direction > 0:
            idxs = list(range(len(items)))
        else:
            idxs = list(range(len(items) - 1, -1, -1))
        to_delete = []
        for i in idxs:
            if items[i] == value and remaining > 0:
                to_delete.append(i)
                remaining -= 1
        for i in sorted(to_delete, reverse=True):
            del items[i]
            removed += 1
        return removed

    def llen(self, key):
        return len(self._list(key))


class MemoryClaimAckTestCase(unittest.TestCase):
    def test_ack_removes_only_after_success(self):
        q = MemoryQueue()
        q.enqueue({"type": "noop", "id": 1})
        claimed = q.claim()
        self.assertIsNotNone(claimed)
        payload, token = claimed
        self.assertEqual(payload["id"], 1)
        self.assertEqual(q.depth, 0)
        self.assertEqual(q.inflight_count, 1)
        self.assertTrue(q.ack(token))
        self.assertEqual(q.inflight_count, 0)
        self.assertEqual(q.depth, 0)
        self.assertIsNone(q.claim())

    def test_failure_without_ack_keeps_job_inflight(self):
        q = MemoryQueue()
        q.enqueue({"type": "noop", "id": "keep"})
        payload, token = q.claim()
        self.assertEqual(payload["id"], "keep")
        # Simulate crash: no ack/nack
        self.assertEqual(q.inflight_count, 1)
        self.assertEqual(q.depth, 0)
        # Job is not lost — still in inflight
        self.assertIn(token, q._inflight)

    def test_nack_requeues_for_retry(self):
        q = MemoryQueue()
        q.enqueue({"type": "noop", "id": "retry-me"})
        _, token = q.claim()
        self.assertTrue(q.nack(token, requeue=True))
        self.assertEqual(q.inflight_count, 0)
        self.assertEqual(q.depth, 1)
        payload, token2 = q.claim()
        self.assertEqual(payload["id"], "retry-me")
        q.ack(token2)

    def test_recover_inflight_after_crash(self):
        q = MemoryQueue()
        q.enqueue({"type": "noop", "id": "orphan"})
        q.claim()  # crash before ack
        recovered = q.recover_inflight()
        self.assertEqual(recovered, 1)
        self.assertEqual(q.inflight_count, 0)
        payload, token = q.claim()
        self.assertEqual(payload["id"], "orphan")
        q.ack(token)

    def test_duplicate_claim_controlled(self):
        q = MemoryQueue()
        q.enqueue({"type": "noop", "id": "once"})
        first = q.claim()
        second = q.claim()
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        q.ack(first[1])


class RedisClaimAckTestCase(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeRedisListClient()
        self.queue = RedisQueue.__new__(RedisQueue)
        self.queue.client = self.fake
        self.queue.key = DEFAULT_QUEUE_KEY
        self.queue.processing_key = processing_key_for(DEFAULT_QUEUE_KEY)

    def test_claim_uses_processing_list_ack_removes(self):
        self.queue.enqueue({"type": "noop", "n": 1})
        self.assertEqual(self.fake.llen(self.queue.key), 1)
        payload, token = self.queue.claim()
        self.assertEqual(payload["n"], 1)
        self.assertEqual(self.fake.llen(self.queue.key), 0)
        self.assertEqual(self.fake.llen(self.queue.processing_key), 1)
        self.assertTrue(self.queue.ack(token))
        self.assertEqual(self.fake.llen(self.queue.processing_key), 0)

    def test_crash_leaves_job_in_processing_recoverable(self):
        self.queue.enqueue({"type": "noop", "n": 2})
        self.queue.claim()
        self.assertEqual(self.fake.llen(self.queue.key), 0)
        self.assertEqual(self.fake.llen(self.queue.processing_key), 1)
        recovered = self.queue.recover_inflight()
        self.assertEqual(recovered, 1)
        payload, token = self.queue.claim()
        self.assertEqual(payload["n"], 2)
        self.queue.ack(token)

    def test_nack_requeues(self):
        self.queue.enqueue({"type": "noop", "n": 3})
        _, token = self.queue.claim()
        self.assertTrue(self.queue.nack(token, requeue=True))
        self.assertEqual(self.fake.llen(self.queue.processing_key), 0)
        self.assertEqual(self.fake.llen(self.queue.key), 1)
        payload, token2 = self.queue.claim()
        self.assertEqual(payload["n"], 3)
        self.queue.ack(token2)


class WorkerDrainClaimAckTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["QUEUE_PROVIDER"] = "memory"
        self.app.extensions.pop("dxcon_queue", None)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_drain_acks_successful_noop(self):
        queue = get_queue(self.app)
        queue.enqueue({"type": "noop", "marker": "ok"})
        result = _drain_broker(self.app, limit=5)
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(queue.depth, 0)
        self.assertEqual(queue.inflight_count, 0)

    def test_drain_requeues_on_handler_failure(self):
        queue = get_queue(self.app)
        queue.enqueue({"type": "unknown-will-fail", "marker": "x"})
        result = _drain_broker(self.app, limit=1)
        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["requeued"], 1)
        self.assertEqual(queue.inflight_count, 0)
        self.assertEqual(queue.depth, 1)
        # Retry path: claim again still has the job
        payload, token = queue.claim()
        self.assertEqual(payload["marker"], "x")
        queue.nack(token, requeue=False)

    def test_worker_cycle_still_processes_seeded_item(self):
        self.app.config["QUEUE_PROVIDER"] = "memory"
        self.app.extensions.pop("dxcon_queue", None)
        queue = get_queue(self.app)
        queue.enqueue({"type": "noop", "marker": "p0-queue"})
        with mock.patch(
            "app.operations.process_runtime._require_runtime_dependencies",
            return_value=None,
        ):
            result = run_worker_cycle(self.app)
        self.assertGreaterEqual(result["broker"]["processed"], 1)


if __name__ == "__main__":
    unittest.main()
