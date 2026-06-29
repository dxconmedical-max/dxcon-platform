import threading
import time


class InMemoryCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._store = {}

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None

            expires_at, value = entry
            if expires_at is not None and expires_at <= time.time():
                del self._store[key]
                return None

            return value

    def set(self, key, value, ttl_seconds=None):
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + float(ttl_seconds)

        with self._lock:
            self._store[key] = (expires_at, value)

    def delete(self, key):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store = {}

    def stats(self):
        with self._lock:
            return {"entries": len(self._store)}


cache = InMemoryCache()


def cache_get(key):
    from app.core.performance_metrics import performance_metrics

    value = cache.get(key)
    if value is None:
        performance_metrics.record_cache_miss()
    else:
        performance_metrics.record_cache_hit()
    return value


def cache_set(key, value, ttl_seconds=None):
    cache.set(key, value, ttl_seconds=ttl_seconds)


def cache_delete(key):
    cache.delete(key)
