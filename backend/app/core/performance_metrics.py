import threading


class PerformanceMetricsService:
    def __init__(self):
        self._lock = threading.Lock()
        self.query_count = 0
        self.query_time_ms_total = 0.0
        self.slow_query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.slow_query_threshold_ms = 100.0

    def set_slow_query_threshold_ms(self, value):
        with self._lock:
            self.slow_query_threshold_ms = float(value or 100.0)

    def record_query(self, duration_ms, label="query"):
        with self._lock:
            self.query_count += 1
            self.query_time_ms_total += float(duration_ms or 0)
            if duration_ms >= self.slow_query_threshold_ms:
                self.slow_query_count += 1

    def record_cache_hit(self):
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self):
        with self._lock:
            self.cache_misses += 1

    def snapshot(self, app=None):
        from app.core.background_tasks import background_tasks
        from app.core.cache import cache
        from app.core.db_pool import pool_status

        with self._lock:
            average_query_ms = (
                round(self.query_time_ms_total / self.query_count, 2)
                if self.query_count
                else 0.0
            )
            cache_total = self.cache_hits + self.cache_misses
            cache_hit_rate = (
                round(self.cache_hits / cache_total, 4)
                if cache_total
                else 0.0
            )
            payload = {
                "query_count": self.query_count,
                "query_time_ms": {
                    "total": round(self.query_time_ms_total, 2),
                    "average": average_query_ms,
                },
                "slow_query_count": self.slow_query_count,
                "slow_query_threshold_ms": self.slow_query_threshold_ms,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": cache_hit_rate,
                "cache_entries": cache.stats()["entries"],
                "background_tasks": background_tasks.snapshot(),
            }

        if app is not None:
            payload["database_pool"] = pool_status(app)

        return payload


performance_metrics = PerformanceMetricsService()
