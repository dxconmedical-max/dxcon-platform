import threading


class PlatformMetricStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {}
        self._gauges = {}
        self._histograms = {}

    def inc(self, name, value=1.0, labels=None):
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + float(value)

    def set_gauge(self, name, value, labels=None):
        key = self._key(name, labels)
        with self._lock:
            self._gauges[key] = float(value)

    def observe(self, name, value, labels=None):
        key = self._key(name, labels)
        with self._lock:
            bucket = self._histograms.setdefault(key, [])
            bucket.append(float(value))
            if len(bucket) > 1000:
                self._histograms[key] = bucket[-1000:]

    @staticmethod
    def _key(name, labels):
        if not labels:
            return name
        label_text = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}|{label_text}"

    def snapshot(self):
        with self._lock:
            histograms = {}
            for key, values in self._histograms.items():
                if not values:
                    continue
                histograms[key] = {
                    "count": len(values),
                    "sum": round(sum(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "max": round(max(values), 2),
                }
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histograms,
            }


platform_metrics = PlatformMetricStore()
