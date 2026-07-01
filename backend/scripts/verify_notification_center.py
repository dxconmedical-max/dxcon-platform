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
from app.notifications.notification_registry import NotificationRegistry
from app.notifications.notification_service import NotificationCenterService, NotificationEventSubscriber
from scripts.seed_notification_center_demo import seed_notification_center_demo


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
        "app.notifications.notification_service",
        "app.notifications.notification_manager",
        "app.notifications.notification_router",
        "app.notifications.notification_registry",
        "app.models.notification_center",
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
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/notifications",
        "/api/v1/notifications/templates",
        "/api/v1/notifications/providers",
        "/api/v1/notifications/statistics",
        "/api/v1/notifications/<notification_id>",
        "/api/v1/notifications/<notification_id>/retry",
        "/notifications",
        "/notifications/history",
        "/notifications/providers",
        "/notifications/templates",
        "/notifications/statistics",
    ]
    missing = [route for route in required if route not in routes]
    for route in required:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
    return check("routes", not missing)


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/notifications", "/notifications")
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes):
            continue
        key = (path, tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})))
        seen[key].append(rule.endpoint)
    duplicates = {key: endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    if duplicates:
        print("DUPLICATE:", duplicates)
        return check("no duplicate routes", False)
    print("OK: no duplicate notification center routes")
    return check("no duplicate routes", True)


def verify_providers():
    NotificationRegistry.initialize()
    channels = ["EMAIL", "SMS", "ZALO", "PUSH", "WEBHOOK", "IN_APP"]
    ok = all(NotificationRegistry.get(channel).health_check() for channel in channels)
    return check("providers", ok)


def verify_templates(client):
    create = client.post(
        "/api/v1/notifications/templates",
        json={"name": "Verify", "body": "Hello {{patient_name}}", "channel": "EMAIL"},
    )
    listing = client.get("/api/v1/notifications/templates")
    return check("templates", create.status_code == 201 and listing.status_code == 200)


def verify_retry_queue(client):
    created = client.post(
        "/api/v1/notifications",
        json={"channel": "IN_APP", "recipient": "user-1", "body": "Retry verify", "dispatch": False},
    )
    if created.status_code != 201:
        return check("retry queue", False)
    body = _payload(created)
    notification_id = body["notification"]["id"]
    retry = client.post(f"/api/v1/notifications/{notification_id}/retry")
    return check("retry queue", retry.status_code == 200)


def verify_event_subscriptions():
    subscribed = NotificationEventSubscriber.register()
    expected = {
        "BookingCreated",
        "SampleCollected",
        "SampleReceived",
        "ResultApproved",
        "CriticalResultDetected",
        "InvoiceCreated",
        "InvoicePaid",
        "CollectorAssigned",
        "PartnerApproved",
    }
    ok = expected.issubset(set(subscribed["subscribed"]))
    return check("event subscriptions", ok)


def verify_statistics(client):
    stats = client.get("/api/v1/notifications/statistics")
    body = _payload(stats)
    ok = stats.status_code == 200 and "delivery_success_rate" in body
    return check("statistics", ok)


def verify_dashboard(client):
    pages = [
        "/notifications",
        "/notifications/history",
        "/notifications/providers",
        "/notifications/templates",
        "/notifications/statistics",
    ]
    ok = all(client.get(page).status_code == 200 for page in pages)
    return check("dashboard", ok)


def verify_seed():
    result = seed_notification_center_demo()
    ok = result["templates"] >= 50 and result["notifications"] >= 200
    return check("demo seed", ok)


def verify_release_isolation():
    if os.environ.get("DXCON_RC2_REGRESSION"):
        return check("release isolation", True)
    script = ROOT / "scripts" / "release_isolation.py"
    proc = subprocess.run(
        [sys.executable, str(script), "check", "--release", "4.4"],
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
        NotificationCenterService.ensure_defaults()
        verify_imports()
        verify_routes(app)
        verify_no_duplicate_routes(app)
        verify_providers()
        verify_event_subscriptions()
        client = app.test_client()
        verify_templates(client)
        verify_retry_queue(client)
        verify_statistics(client)
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
