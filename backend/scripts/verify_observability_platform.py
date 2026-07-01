import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.observability.alert_engine import AlertEngine
from app.observability.audit_service import AuditTimelineService
from app.observability.logging_service import StructuredLoggingService
from app.observability.trace_service import TraceService
from scripts.seed_observability_demo import seed_observability_demo


CHECKS = []


def _payload(response):
    body = response.get_json() or {}
    if isinstance(body.get("data"), dict) and "success" in body:
        return body["data"]
    return body


def check(name, ok):
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return ok


def verify_imports():
    modules = [
        "app.observability.metrics_service",
        "app.observability.health_service",
        "app.observability.logging_service",
        "app.observability.trace_service",
        "app.observability.alert_engine",
        "app.observability.audit_service",
        "app.observability.prometheus_exporter",
        "app.models.observability_platform",
    ]
    ok = True
    for module in modules:
        try:
            __import__(module)
            print("OK: import", module)
        except Exception as exc:
            print("FAIL: import", module, exc)
            ok = False
    return check("imports", ok)


def verify_routes(app):
    required = [
        "/api/v1/metrics",
        "/api/v1/metrics/system",
        "/api/v1/metrics/business",
        "/metrics/prometheus",
        "/health",
        "/ready",
        "/live",
        "/api/v1/system/health",
        "/api/v1/alerts/test",
        "/system/metrics",
        "/system/health",
        "/system/alerts",
        "/system/audit",
        "/system/traces",
        "/system/logs",
    ]
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    missing = [route for route in required if route not in routes]
    for route in required:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
    return check("routes", not missing)


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/metrics", "/metrics/prometheus", "/system/", "/health", "/ready", "/live")
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path == p or path.startswith(p) for p in prefixes):
            continue
        key = (path, tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})))
        seen[key].append(rule.endpoint)
    duplicates = {key: endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    if duplicates:
        print("DUPLICATE:", duplicates)
        return check("no duplicate routes", False)
    print("OK: no duplicate observability routes")
    return check("no duplicate routes", True)


def verify_metrics(client):
    ok = all(client.get(path).status_code == 200 for path in (
        "/api/v1/metrics",
        "/api/v1/metrics/system",
        "/api/v1/metrics/business",
    ))
    return check("metrics", ok)


def verify_prometheus(client):
    response = client.get("/metrics/prometheus")
    return check("prometheus endpoint", response.status_code == 200 and b"http_requests_total" in response.data)


def verify_health(client):
    ok = all(client.get(path).status_code in (200, 503) for path in ("/health", "/ready", "/live", "/api/v1/system/health"))
    return check("health endpoints", ok)


def verify_logging(app):
    with app.test_request_context("/health", headers={"X-Request-ID": "rid", "X-Trace-ID": "tid", "X-Correlation-ID": "cid"}):
        from flask import g

        g.request_id = "rid"
        g.trace_id = "tid"
        g.correlation_id = "cid"
        record = StructuredLoggingService.format_record("observability", "verify", execution_ms=1.0, extra={"password": "x"})
        ok = record["request_id"] == "rid" and record["context"]["password"] == "[REDACTED]"
    return check("structured logging", ok)


def verify_trace(app):
    with app.test_request_context("/health", headers={"X-Trace-ID": "trace-verify", "X-Span-ID": "span-parent"}):
        ctx = TraceService.start_trace()
        ok = ctx["trace_id"] == "trace-verify" and TraceService.inject_headers({})["X-Trace-ID"] == "trace-verify"
    return check("trace propagation", ok)


def verify_audit():
    event = AuditTimelineService.record("Notification", "sent", actor={"display_name": "System"})
    ok = bool(event.get("event_code"))
    return check("audit timeline", ok)


def verify_alerts(client):
    response = client.post("/api/v1/alerts/test", json={"rule_code": "HIGH_API_LATENCY"})
    return check("alert engine", response.status_code == 201)


def verify_dashboard(client):
    pages = ("/system/metrics", "/system/health", "/system/alerts", "/system/audit", "/system/traces", "/system/logs")
    ok = all(client.get(page).status_code == 200 for page in pages)
    return check("dashboard", ok)


def verify_seed():
    result = seed_observability_demo()
    ok = result["metrics"] >= 12 and result["audit_events"] >= 5
    return check("demo seed", ok)


def verify_release_isolation():
    script = ROOT / "scripts" / "release_isolation.py"
    proc = subprocess.run(
        [sys.executable, str(script), "check", "--release", "4.5"],
        cwd=str(ROOT.parent),
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    return check("release isolation", proc.returncode == 0)


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        verify_imports()
        verify_routes(app)
        verify_no_duplicate_routes(app)
        verify_logging(app)
        verify_trace(app)
        verify_audit()
        client = app.test_client()
        verify_metrics(client)
        verify_prometheus(client)
        verify_health(client)
        verify_alerts(client)
        verify_dashboard(client)
        verify_seed()
    verify_release_isolation()

    failed = [name for name, ok in CHECKS if not ok]
    print("\nSUMMARY:", len(CHECKS) - len(failed), "passed,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
