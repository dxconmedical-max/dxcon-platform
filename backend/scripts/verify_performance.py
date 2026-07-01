import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.cache import cache, cache_set
from app.core.db_pool import review_pool_config
from app.core.performance_metrics import performance_metrics


def main():
    print("\n=== DXCON PERFORMANCE VERIFY ===\n")
    errors = 0

    try:
        app = create_app()
        print("OK: app creates successfully")
    except Exception as exc:
        print("FAIL: app create", exc)
        sys.exit(1)

    review = review_pool_config(app)
    if review.get("engine_options"):
        print("OK: connection pool configuration reviewed", review["engine_options"])
    else:
        print("FAIL: pool configuration missing")
        errors += 1

    client = app.test_client()

    health = client.get("/api/v1/system/health")
    if health.status_code != 200:
        print("FAIL: health endpoint", health.status_code)
        errors += 1

    performance = client.get("/api/v1/system/performance")
    payload = performance.get_json() or {}
    required = {
        "query_count",
        "query_time_ms",
        "cache_hits",
        "cache_misses",
        "background_tasks",
        "database_pool",
    }
    if performance.status_code == 200 and required.issubset(payload.keys()):
        print("OK: /api/v1/system/performance", payload)
    else:
        print("FAIL: performance endpoint", performance.status_code, payload)
        errors += 1

    cache_set("perf-verify", {"ok": True}, ttl_seconds=10)
    if cache.get("perf-verify"):
        print("OK: cache abstraction works")
    else:
        print("FAIL: cache abstraction")
        errors += 1

    health = client.get("/api/v1/system/health")
    if health.status_code == 200 and performance_metrics.query_count >= 1:
        print("OK: SQLAlchemy query metrics recorded", performance_metrics.query_count)
    else:
        print("FAIL: query metrics", performance_metrics.query_count, health.status_code)
        errors += 1

    if errors:
        print("\nPERFORMANCE VERIFY FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nPERFORMANCE VERIFY PASSED\n")


if __name__ == "__main__":
    main()
