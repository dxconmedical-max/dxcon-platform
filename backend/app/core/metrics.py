import threading


class MetricsService:
    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = 0
        self.error_count = 0
        self.total_latency_ms = 0.0
        self.route_count = 0
        self.health_status = "UNKNOWN"

    def record_request(self, latency_ms):
        with self._lock:
            self.request_count += 1
            self.total_latency_ms += float(latency_ms or 0)

    def record_error(self):
        with self._lock:
            self.error_count += 1

    def set_route_count(self, count):
        with self._lock:
            self.route_count = int(count or 0)

    def set_health_status(self, status):
        with self._lock:
            self.health_status = status or "UNKNOWN"

    def snapshot(self):
        with self._lock:
            average_latency_ms = (
                round(self.total_latency_ms / self.request_count, 2)
                if self.request_count
                else 0.0
            )
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "latency_ms": {
                    "total": round(self.total_latency_ms, 2),
                    "average": average_latency_ms,
                },
                "route_count": self.route_count,
                "health_status": self.health_status,
            }


metrics = MetricsService()
