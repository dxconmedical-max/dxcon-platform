import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.logging_config import configure_logging, sanitize_path


def _route_key(rule):
    methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
    return rule.rule, tuple(methods)


def main():
    print("\n=== DXCON OBSERVABILITY VERIFY ===\n")
    errors = 0

    try:
        app = create_app()
        print("OK: app creates successfully")
    except Exception as exc:
        print("FAIL: app create", exc)
        sys.exit(1)

    configure_logging(app)
    sanitized = sanitize_path("/api/v1/auth?token=abc&mode=test")
    if "token=[REDACTED]" in sanitized and "mode=test" in sanitized:
        print("OK: logging config imports and sanitizes secrets")
    else:
        print("FAIL: logging sanitize", sanitized)
        errors += 1

    client = app.test_client()

    health = client.get("/api/v1/system/health")
    request_id = health.headers.get("X-Request-ID")
    if health.status_code == 200 and request_id:
        print("OK: request_id present on response", request_id)
    else:
        print("FAIL: request_id missing")
        errors += 1

    not_found = client.get("/api/v1/system/verify-missing-route")
    payload = not_found.get_json() or {}
    if (
        not_found.status_code == 404
        and payload.get("success") is False
        and payload.get("error", {}).get("code") == "NOT_FOUND"
        and payload.get("request_id")
        and payload.get("timestamp")
    ):
        print("OK: standardized API error response")
    else:
        print("FAIL: error handler format", not_found.status_code, payload)
        errors += 1

    metrics = client.get("/api/v1/system/metrics")
    metrics_payload = metrics.get_json() or {}
    metrics_data = metrics_payload.get("data") if metrics_payload.get("success") is True else metrics_payload
    required = {
        "request_count",
        "error_count",
        "latency_ms",
        "route_count",
        "health_status",
    }
    if metrics.status_code == 200 and required.issubset(metrics_data.keys()):
        print("OK: /api/v1/system/metrics", metrics_data)
    else:
        print("FAIL: metrics endpoint", metrics.status_code, metrics_payload)
        errors += 1

    route_map = defaultdict(list)
    for rule in app.url_map.iter_rules():
        route_map[_route_key(rule)].append(rule.endpoint)

    duplicates = [endpoints for endpoints in route_map.values() if len(endpoints) > 1]
    if duplicates:
        print("FAIL: duplicate routes detected", duplicates[:5])
        errors += 1
    else:
        print("OK: no duplicate routes introduced")

    if errors:
        print("\nOBSERVABILITY VERIFY FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nOBSERVABILITY VERIFY PASSED\n")


if __name__ == "__main__":
    main()
