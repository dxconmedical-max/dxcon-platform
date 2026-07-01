import threading
import time


class RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._requests = {}

    def allow(self, key, limit, window_seconds):
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = [
                ts for ts in self._requests.get(key, [])
                if ts >= window_start
            ]

            if len(timestamps) >= limit:
                self._requests[key] = timestamps
                return False

            timestamps.append(now)
            self._requests[key] = timestamps
            return True

    def reset(self):
        with self._lock:
            self._requests = {}


rate_limiter = RateLimiter()


def check_rate_limit(app, key):
    limit = app.config.get("RATE_LIMIT_MAX", 120)
    window = app.config.get("RATE_LIMIT_WINDOW_SECONDS", 60)
    return rate_limiter.allow(key, limit, window)
