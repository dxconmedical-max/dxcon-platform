import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.integrations.adapter_loader import load_adapters
from app.integrations.adapter_registry import AdapterRegistry
from app.models.integration_platform import (
    IntegrationDeadLetter,
    IntegrationDomainEvent,
    IntegrationJob,
    IntegrationJobAttempt,
    IntegrationPluginState,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEvent,
    WebhookSecret,
)
from app.services.integration_platform_service import (
    EventPlatformService,
    IntegrationPlatformService,
    IntegrationQueueService,
    SandboxService,
    WebhookEngineService,
)


def verify_models_import():
    models = [
        IntegrationPluginState,
        IntegrationDomainEvent,
        IntegrationJob,
        IntegrationJobAttempt,
        IntegrationDeadLetter,
        WebhookEndpoint,
        WebhookSecret,
        WebhookEvent,
        WebhookDelivery,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/plugins",
        "/api/v1/plugins/<plugin_id>",
        "/api/v1/plugins/<plugin_id>/enable",
        "/api/v1/plugins/<plugin_id>/disable",
        "/api/v1/plugins/<plugin_id>/health",
        "/api/v1/events",
        "/api/v1/events/<event_id>",
        "/api/v1/events/test",
        "/api/v1/webhooks",
        "/api/v1/webhooks/<webhook_id>",
        "/api/v1/webhooks/<webhook_id>/test",
        "/api/v1/webhooks/deliveries",
        "/api/v1/webhooks/deliveries/<delivery_id>/retry",
        "/api/v1/integration-queue/jobs",
        "/api/v1/integration-queue/jobs/<job_id>/retry",
        "/api/v1/integration-queue/dead-letters",
        "/api/v1/integration-queue/dead-letters/<dead_letter_id>/replay",
        "/api/v1/sandbox/status",
        "/api/v1/sandbox/lis/result",
        "/api/v1/sandbox/his/patient",
        "/api/v1/sandbox/payment/callback",
        "/api/v1/sandbox/webhook/test",
    ]
    required_web = [
        "/integrations/platform",
        "/integrations/adapters",
        "/integrations/plugins",
        "/integrations/events",
        "/integrations/webhooks",
        "/integrations/queue",
        "/integrations/sandbox",
    ]
    missing = [route for route in required_api + required_web if route not in routes]
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
        return False
    return True


def verify_no_duplicate_routes(app):
    prefixes = (
        "/api/v1/plugins",
        "/api/v1/events",
        "/api/v1/webhooks",
        "/api/v1/integration-queue",
        "/api/v1/sandbox",
        "/integrations/",
    )
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path.startswith(prefix) for prefix in prefixes):
            continue
        key = (path, tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})))
        seen[key].append(rule.endpoint)
    duplicates = {key: endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    if duplicates:
        print("DUPLICATE:", duplicates)
        return False
    print("OK: no duplicate integration platform routes")
    return True


def verify_engines():
    AdapterRegistry.reset()
    loaded = load_adapters()
    if loaded["loaded"] != 8:
        print("MISSING: demo adapters")
        return False
    print("OK: demo adapters registered")

    IntegrationPlatformService.ensure_defaults()
    EventPlatformService.register_default_subscriber()
    published = EventPlatformService.test_event({"event_type": "OrderCreated"})
    if not published.get("event"):
        print("MISSING: event publish")
        return False
    print("OK: event publish/subscribe")

    webhook = WebhookEndpoint.query.first()
    delivery = WebhookEngineService.test(webhook.id, {"event_type": "OrderCreated"})
    if not delivery.get("signature"):
        print("MISSING: webhook signing")
        return False
    print("OK: webhook signing")

    job = IntegrationQueueService.create({"adapter_type": "HIS", "payload": {"demo": True}, "max_retries": 1})
    IntegrationQueueService.process_job(job["id"], force_fail=True)
    dead = IntegrationDeadLetter.query.first()
    if dead is None:
        print("MISSING: dead letter")
        return False
    replay = IntegrationQueueService.replay_dead_letter(dead.id)
    if replay["status"] not in {"SUCCESS", "FAILED", "DEAD_LETTER"}:
        print("MISSING: queue replay")
        return False
    print("OK: queue retry/dead-letter/replay")

    status = SandboxService.status()
    if status["status"] != "OK":
        print("MISSING: sandbox status")
        return False
    print("OK: sandbox engine")
    return True


app = create_app()
print("\n=== DXCON INTEGRATION PLATFORM VERIFY ===\n")
errors = 0
with app.app_context():
    db.create_all()
    if not verify_models_import():
        errors += 1
    if not verify_routes(app):
        errors += 1
    if not verify_no_duplicate_routes(app):
        errors += 1
    if not verify_engines():
        errors += 1
if errors:
    print("\nINTEGRATION PLATFORM VERIFY FAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nINTEGRATION PLATFORM VERIFY PASSED\n")
