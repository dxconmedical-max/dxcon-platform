"""Integration hardening validation helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

INTEGRATION_FILES = (
    "app/webhooks/idempotency.py",
    "app/webhooks/replay.py",
    "app/webhooks/signatures.py",
    "app/webhooks/dead_letter.py",
    "app/integrations/connector_registry.py",
    "app/integrations/connector_health.py",
    "app/integrations/outbound_signing.py",
    "app/integrations/audit_trail.py",
    "app/integrations/sandbox_tokens.py",
    "app/events/deduplication.py",
    "app/api/connectors/routes.py",
)

INTEGRATION_ENDPOINTS = (
    "/api/v1/connectors",
    "/api/v1/webhooks/replay",
    "/api/v1/integrations/audit",
    "/api/v1/integrations/sandbox-token",
)


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def verify_integration_modules() -> dict:
    missing = [path for path in INTEGRATION_FILES if not (ROOT / path).exists()]
    return {"ok": not missing, "missing": missing}


def verify_integration_endpoints(app) -> dict:
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    missing = [path for path in INTEGRATION_ENDPOINTS if path not in routes]
    dynamic = any("/api/v1/connectors/<connector_id>/health" in route for route in routes)
    return {"ok": not missing and dynamic, "missing": missing, "dynamic_routes": dynamic}


def verify_idempotency(app) -> dict:
    from app.services.integration_platform_service import IntegrationPlatformService, WebhookEngineService

    IntegrationPlatformService.ensure_defaults()
    webhook = __import__("app.models.integration_platform", fromlist=["WebhookEndpoint"]).WebhookEndpoint.query.first()
    key = "idem-test-key"
    first = WebhookEngineService.deliver(webhook.id, "OrderCreated", {"order_id": "O-1"}, idempotency_key=key)
    second = WebhookEngineService.deliver(webhook.id, "OrderCreated", {"order_id": "O-1"}, idempotency_key=key)
    return {
        "ok": first.get("delivery", {}).get("id") == second.get("delivery", {}).get("id"),
        "first_delivery_id": first.get("delivery", {}).get("id"),
        "second_delivery_id": second.get("delivery", {}).get("id"),
    }


def verify_signatures(app) -> dict:
    from app.integrations.outbound_signing import OutboundSigningService
    from app.webhooks.signatures import verify_inbound_signature

    payload = {"event_type": "OrderCreated", "order_id": "O-2"}
    secret = app.config.get("INTEGRATION_SIGNING_SECRET", "dxcon-integration-secret")
    signed = OutboundSigningService.sign_payload(payload, secret=secret)
    payload_text = signed["payload"]
    ok = verify_inbound_signature(secret, payload_text, signed["signature"])
    return {"ok": ok, "algorithm": signed["algorithm"]}


def verify_connectors(app) -> dict:
    from app.integrations.connector_registry import ConnectorRegistry

    listed = ConnectorRegistry.list_connectors()
    return {"ok": listed.get("count", 0) >= 1, "count": listed.get("count", 0)}


def run_integration_hardening_smoke(app) -> dict:
    client = app.test_client()
    steps = {}

    connectors = client.get("/api/v1/connectors")
    steps["connectors_list"] = connectors.status_code == 200 and connectors.get_json().get("count", 0) >= 1

    created = client.post(
        "/api/v1/connectors",
        json={"name": "Smoke HIS", "adapter_type": "HIS", "connector_code": "CONN-SMOKE"},
    )
    steps["connector_register"] = created.status_code == 201
    connector_id = (created.get_json() or {}).get("id")
    health = client.get(f"/api/v1/connectors/{connector_id}/health")
    steps["connector_health"] = health.status_code == 200 and "healthy" in (health.get_json() or {})

    token = client.post("/api/v1/integrations/sandbox-token", json={"partner_id": "PARTNER-SMOKE"})
    steps["sandbox_token"] = token.status_code == 201 and "token" in (token.get_json() or {})

    audit = client.get("/api/v1/integrations/audit?scope=platform")
    audit_payload = audit.get_json() or {}
    steps["audit_trail"] = audit.status_code == 200 and audit_payload.get("count", 0) >= 1

    webhook = client.post(
        "/api/v1/webhooks",
        json={"name": "Replay Hook", "target_url": "https://example.com/hook", "event_types": ["OrderCreated"]},
    )
    webhook_id = (webhook.get_json() or {}).get("id")
    delivery = client.post(f"/api/v1/webhooks/{webhook_id}/test", json={"event_type": "OrderCreated"})
    delivery_id = (delivery.get_json() or {}).get("delivery", {}).get("id")
    replay = client.post("/api/v1/webhooks/replay", json={"delivery_id": delivery_id})
    replay_payload = replay.get_json() or {}
    steps["webhook_replay"] = replay.status_code == 200 and replay_payload.get("replay_safe") is True

    duplicate_replay = client.post(
        "/api/v1/webhooks/replay",
        json={"delivery_id": delivery_id, "replay_token": replay_payload.get("replay_token")},
    )
    steps["replay_safe"] = duplicate_replay.status_code == 200 and duplicate_replay.get_json().get("duplicate") is True

    event = client.post("/api/v1/events/test", json={"event_type": "OrderCreated", "payload": {"dedup": True}})
    event2 = client.post("/api/v1/events/test", json={"event_type": "OrderCreated", "payload": {"dedup": True}})
    steps["event_deduplication"] = event2.get_json().get("event", {}).get("deduplicated") is True

    return {
        "ok": all(steps.values()),
        "passed": sum(1 for ok in steps.values() if ok),
        "total": len(steps),
        "steps": steps,
    }


def run_integration_hardening_verification() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        checks = {
            "integration_modules": verify_integration_modules(),
            "integration_endpoints": verify_integration_endpoints(app),
            "route_inventory": {"ok": not find_duplicate_routes(app), "count": len(find_duplicate_routes(app))},
            "idempotency": verify_idempotency(app),
            "signatures": verify_signatures(app),
            "connectors": verify_connectors(app),
            "integration_smoke": run_integration_hardening_smoke(app),
        }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {"ok": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
