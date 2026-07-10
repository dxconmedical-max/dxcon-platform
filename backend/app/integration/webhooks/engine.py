"""Webhook engine with HMAC signing — Epic 3.5."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.extensions.db import db
from app.integration.audit import write_integration_audit
from app.integration.models import IntgDeliveryAttempt, IntgWebhookSubscription
from app.integration.security import validate_endpoint_url


def sign_webhook_payload(secret: str, payload: bytes, timestamp: int) -> str:
    message = f"{timestamp}.".encode() + payload
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_webhook_signature(secret: str, payload: bytes, timestamp: int, signature: str, *, max_age_seconds: int = 300) -> bool:
    if abs(int(time.time()) - timestamp) > max_age_seconds:
        return False
    expected = sign_webhook_payload(secret, payload, timestamp)
    return hmac.compare_digest(expected, signature)


def create_subscription(data: dict[str, Any], *, organization_id: str, actor: str | None) -> dict:
    url = data.get("endpoint_url", "")
    ok, reason = validate_endpoint_url(url)
    if not ok:
        raise ValueError(reason)
    row = IntgWebhookSubscription(
        organization_id=organization_id,
        connector_id=data.get("connector_id"),
        event_type=data.get("event_type", ""),
        endpoint_url=url,
        secret_reference=data.get("secret_reference") or f"whsec_{uuid.uuid4().hex[:16]}",
        status=data.get("status", "ACTIVE"),
        retry_policy=data.get("retry_policy", "EXPONENTIAL_BACKOFF"),
    )
    db.session.add(row)
    db.session.flush()
    write_integration_audit(
        action="webhook_created",
        actor=actor,
        organization_id=organization_id,
        connector_id=row.connector_id,
        outcome="SUCCESS",
    )
    return row.to_dict()


def queue_delivery(subscription_id: str, event_type: str, payload: dict[str, Any], *, organization_id: str) -> dict:
    sub = IntgWebhookSubscription.query.get(subscription_id)
    if not sub or sub.status != "ACTIVE":
        raise ValueError("subscription not active")
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    delivery = IntgDeliveryAttempt(
        subscription_id=subscription_id,
        organization_id=organization_id,
        delivery_id=f"dlv_{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        payload_hash=hashlib.sha256(payload_bytes).hexdigest(),
        status="PENDING",
        attempt_number=1,
    )
    db.session.add(delivery)
    db.session.flush()
    return delivery.to_dict()


def simulate_delivery(delivery_id: str, *, success: bool = True) -> dict:
    row = IntgDeliveryAttempt.query.filter_by(delivery_id=delivery_id).first()
    if not row:
        raise ValueError("delivery not found")
    if success:
        row.status = "DELIVERED"
        write_integration_audit(action="webhook_delivered", message_id=row.id, outcome="SUCCESS")
    else:
        row.status = "FAILED"
        row.last_error = "simulated failure"
        row.attempt_number += 1
        row.next_retry_at = datetime.utcnow() + timedelta(minutes=2 ** min(row.attempt_number, 5))
        write_integration_audit(action="webhook_failed", message_id=row.id, outcome="FAILURE")
    db.session.flush()
    return row.to_dict()
