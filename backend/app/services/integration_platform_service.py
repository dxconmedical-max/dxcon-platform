import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime

from app.core.statuses import (
    INTEGRATION_JOB_DEAD_LETTER,
    INTEGRATION_JOB_FAILED,
    INTEGRATION_JOB_PENDING,
    INTEGRATION_JOB_PROCESSING,
    INTEGRATION_JOB_SUCCESS,
    INTEGRATION_PLUGIN_ENABLED,
    INTEGRATION_WEBHOOK_ACTIVE,
    INTEGRATION_WEBHOOK_DELIVERY_DELIVERED,
    INTEGRATION_WEBHOOK_DELIVERY_FAILED,
    INTEGRATION_WEBHOOK_DELIVERY_PENDING,
    INTEGRATION_WEBHOOK_DELIVERY_RETRYING,
    VALID_DOMAIN_EVENTS,
)
from app.events.domain_event import DomainEvent
from app.events.event_bus import EventBus
from app.events.event_registry import EventRegistry
from app.extensions.db import db
from app.integrations.adapter_manager import AdapterManager
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
from app.plugins.plugin_manager import PluginManager


class IntegrationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class IntegrationPlatformService:
    @staticmethod
    def ensure_defaults():
        AdapterManager.initialize()
        PluginManager.ensure_defaults()
        if WebhookEndpoint.query.first():
            return {"seeded": False}

        endpoint = WebhookEndpoint(
            endpoint_code="WH-DEMO",
            name="Demo Integration Webhook",
            target_url="https://sandbox.example.com/webhooks/dxcon",
            event_types_json=json.dumps(VALID_DOMAIN_EVENTS[:3]),
            status=INTEGRATION_WEBHOOK_ACTIVE,
        )
        db.session.add(endpoint)
        db.session.flush()
        db.session.add(
            WebhookSecret(
                webhook_id=endpoint.id,
                secret_value=secrets.token_hex(16),
                algorithm="HMAC-SHA256",
                is_active=True,
            )
        )
        db.session.commit()
        return {"seeded": True}


def _page(page, page_size):
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 50), 1), 200)
    return page, page_size


def _sign_payload(secret: str, payload_text: str) -> str:
    return hmac.new(secret.encode(), payload_text.encode(), hashlib.sha256).hexdigest()


class EventPlatformService:
    @staticmethod
    def list_events(event_type=None, page=1, page_size=50):
        page, page_size = _page(page, page_size)
        query = IntegrationDomainEvent.query
        if event_type:
            query = query.filter_by(event_type=event_type)
        rows = query.order_by(IntegrationDomainEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"count": query.count(), "events": [row.to_dict() for row in rows]}

    @staticmethod
    def get_event(event_id):
        row = IntegrationDomainEvent.query.filter_by(id=event_id).first()
        if row is None:
            raise IntegrationError("Event not found", 404)
        return row.to_dict()

    @staticmethod
    def publish(data):
        event_type = data.get("event_type")
        if event_type not in VALID_DOMAIN_EVENTS:
            raise IntegrationError(f"Unsupported event_type: {event_type}")
        event = DomainEvent(
            event_type=event_type,
            payload=data.get("payload") or {},
            source=data.get("source") or "dxcon",
            correlation_id=data.get("correlation_id"),
        )
        return EventBus.publish(event)

    @staticmethod
    def test_event(data=None):
        data = data or {}
        event_type = data.get("event_type") or VALID_DOMAIN_EVENTS[0]
        return EventPlatformService.publish(
            {
                "event_type": event_type,
                "payload": data.get("payload") or {"test": True},
                "source": "sandbox",
            }
        )

    @staticmethod
    def register_default_subscriber():
        def _log_handler(event: DomainEvent):
            return {"received": event.event_type}

        for event_type in VALID_DOMAIN_EVENTS[:3]:
            EventBus.subscribe(event_type, _log_handler)
        return {"subscribed": VALID_DOMAIN_EVENTS[:3]}


class WebhookEngineService:
    @staticmethod
    def list_webhooks():
        rows = WebhookEndpoint.query.order_by(WebhookEndpoint.created_at.desc()).all()
        return {"count": len(rows), "webhooks": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        name = data.get("name")
        target_url = data.get("target_url")
        if not name or not target_url:
            raise IntegrationError("name and target_url are required")
        endpoint = WebhookEndpoint(
            endpoint_code=data.get("endpoint_code") or f"WH-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            target_url=target_url,
            event_types_json=json.dumps(data.get("event_types") or []),
            status=INTEGRATION_WEBHOOK_ACTIVE,
        )
        db.session.add(endpoint)
        db.session.flush()
        secret = WebhookSecret(
            webhook_id=endpoint.id,
            secret_value=data.get("secret") or secrets.token_hex(16),
            algorithm="HMAC-SHA256",
            is_active=True,
        )
        db.session.add(secret)
        db.session.commit()
        return endpoint.to_dict()

    @staticmethod
    def get(webhook_id):
        row = WebhookEndpoint.query.filter_by(id=webhook_id).first()
        if row is None:
            raise IntegrationError("Webhook not found", 404)
        return row.to_dict()

    @staticmethod
    def _active_secret(webhook_id):
        return WebhookSecret.query.filter_by(webhook_id=webhook_id, is_active=True).first()

    @staticmethod
    def deliver(webhook_id, event_type, payload=None, simulate_failure=False, idempotency_key=None):
        from app.webhooks.idempotency import WebhookIdempotencyService
        from app.webhooks.models import WebhookIdempotencyKey

        if idempotency_key:
            existing = WebhookIdempotencyKey.query.filter_by(idempotency_key=idempotency_key).first()
            if existing:
                return json.loads(existing.response_json or "{}")

        endpoint = WebhookEndpoint.query.filter_by(id=webhook_id).first()
        if endpoint is None:
            raise IntegrationError("Webhook not found", 404)
        secret_row = WebhookEngineService._active_secret(webhook_id)
        if secret_row is None:
            raise IntegrationError("Webhook secret not configured", 400)
        payload = payload or {"event_type": event_type, "test": True}
        payload_text = json.dumps(payload, sort_keys=True)
        signature = _sign_payload(secret_row.secret_value, payload_text)
        event = WebhookEvent(
            event_code=f"WHE-{uuid.uuid4().hex[:8].upper()}",
            webhook_id=webhook_id,
            event_type=event_type,
            payload_json=payload_text,
        )
        db.session.add(event)
        db.session.flush()
        status = INTEGRATION_WEBHOOK_DELIVERY_FAILED if simulate_failure else INTEGRATION_WEBHOOK_DELIVERY_DELIVERED
        delivery = WebhookDelivery(
            delivery_code=f"WHD-{uuid.uuid4().hex[:8].upper()}",
            webhook_id=webhook_id,
            webhook_event_id=event.id,
            event_type=event_type,
            payload_json=payload_text,
            signature=signature,
            status=status,
            response_code=502 if simulate_failure else 202,
            failure_reason="Simulated failure" if simulate_failure else None,
            attempt_count=1,
            delivered_at=datetime.utcnow() if not simulate_failure else None,
        )
        db.session.add(delivery)
        db.session.commit()
        result = {
            "webhook": endpoint.to_dict(),
            "event": event.to_dict(),
            "delivery": delivery.to_dict(),
            "signature": signature,
        }
        if idempotency_key:
            idem = WebhookIdempotencyService.check_or_store(idempotency_key, webhook_id, delivery.id, result)
            if idem.get("duplicate"):
                return idem.get("response") or result
        return result

    @staticmethod
    def test(webhook_id, data=None):
        data = data or {}
        return WebhookEngineService.deliver(
            webhook_id,
            data.get("event_type") or VALID_DOMAIN_EVENTS[0],
            data.get("payload"),
            simulate_failure=bool(data.get("simulate_failure")),
        )

    @staticmethod
    def list_deliveries(webhook_id=None):
        query = WebhookDelivery.query
        if webhook_id:
            query = query.filter_by(webhook_id=webhook_id)
        rows = query.order_by(WebhookDelivery.created_at.desc()).all()
        return {"count": len(rows), "deliveries": [row.to_dict() for row in rows]}

    @staticmethod
    def retry_delivery(delivery_id):
        delivery = WebhookDelivery.query.filter_by(id=delivery_id).first()
        if delivery is None:
            raise IntegrationError("Delivery not found", 404)
        if delivery.attempt_count >= delivery.max_retries:
            raise IntegrationError("Maximum retries exceeded", 409)
        secret_row = WebhookEngineService._active_secret(delivery.webhook_id)
        signature = _sign_payload(secret_row.secret_value, delivery.payload_json)
        delivery.attempt_count += 1
        delivery.status = INTEGRATION_WEBHOOK_DELIVERY_RETRYING
        delivery.signature = signature
        delivery.status = INTEGRATION_WEBHOOK_DELIVERY_DELIVERED
        delivery.response_code = 202
        delivery.failure_reason = None
        delivery.delivered_at = datetime.utcnow()
        db.session.commit()
        return delivery.to_dict()

    @staticmethod
    def replay_delivery(delivery_id):
        delivery = WebhookDelivery.query.filter_by(id=delivery_id).first()
        if delivery is None:
            raise IntegrationError("Delivery not found", 404)
        return WebhookEngineService.deliver(
            delivery.webhook_id,
            delivery.event_type,
            json.loads(delivery.payload_json or "{}"),
        )


class IntegrationQueueService:
    @staticmethod
    def list_jobs(status=None):
        query = IntegrationJob.query
        if status:
            query = query.filter_by(status=status)
        rows = query.order_by(IntegrationJob.created_at.desc()).all()
        return {"count": len(rows), "jobs": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        from app.integrations.adapter_registry import AdapterRegistry

        AdapterManager.initialize()
        adapter_type = (data.get("adapter_type") or "HIS").upper()
        if adapter_type not in AdapterRegistry.list_types():
            raise IntegrationError(f"Unknown adapter_type: {adapter_type}")
        job = IntegrationJob(
            job_code=data.get("job_code") or f"JOB-{uuid.uuid4().hex[:8].upper()}",
            adapter_type=adapter_type or "HIS",
            direction=data.get("direction") or "OUTBOUND",
            payload_json=json.dumps(data.get("payload") or {}),
            status=INTEGRATION_JOB_PENDING,
            max_retries=int(data.get("max_retries") or 3),
        )
        db.session.add(job)
        db.session.commit()
        return job.to_dict()

    @staticmethod
    def process_job(job_id, force_fail=False):
        job = IntegrationJob.query.filter_by(id=job_id).first()
        if job is None:
            raise IntegrationError("Job not found", 404)
        job.status = INTEGRATION_JOB_PROCESSING
        db.session.add(
            IntegrationJobAttempt(
                job_id=job.id,
                attempt_number=job.retry_count + 1,
                status=INTEGRATION_JOB_PROCESSING,
            )
        )
        payload = json.loads(job.payload_json or "{}")
        try:
            if force_fail:
                raise RuntimeError("Forced job failure")
            AdapterManager.connect(job.adapter_type)
            result = AdapterManager.send(job.adapter_type, payload)
            job.status = INTEGRATION_JOB_SUCCESS
            job.processed_at = datetime.utcnow()
            job.last_error = None
            detail = {"result": result}
            status = INTEGRATION_JOB_SUCCESS
        except Exception as exc:
            job.retry_count += 1
            job.last_error = str(exc)
            if job.retry_count >= job.max_retries:
                job.status = INTEGRATION_JOB_DEAD_LETTER
                db.session.add(
                    IntegrationDeadLetter(
                        job_id=job.id,
                        reason=str(exc),
                        payload_json=job.payload_json,
                    )
                )
                status = INTEGRATION_JOB_DEAD_LETTER
            else:
                job.status = INTEGRATION_JOB_FAILED
                status = INTEGRATION_JOB_FAILED
            detail = {"error": str(exc)}
        db.session.add(
            IntegrationJobAttempt(
                job_id=job.id,
                attempt_number=job.retry_count,
                status=status,
                detail_json=json.dumps(detail),
            )
        )
        db.session.commit()
        return job.to_dict()

    @staticmethod
    def retry_job(job_id):
        job = IntegrationJob.query.filter_by(id=job_id).first()
        if job is None:
            raise IntegrationError("Job not found", 404)
        if job.status == INTEGRATION_JOB_DEAD_LETTER:
            raise IntegrationError("Job is in dead letter queue", 409)
        job.status = INTEGRATION_JOB_PENDING
        db.session.commit()
        return IntegrationQueueService.process_job(job_id)

    @staticmethod
    def list_dead_letters():
        rows = IntegrationDeadLetter.query.order_by(IntegrationDeadLetter.created_at.desc()).all()
        return {"count": len(rows), "dead_letters": [row.to_dict() for row in rows]}

    @staticmethod
    def replay_dead_letter(dead_letter_id):
        row = IntegrationDeadLetter.query.filter_by(id=dead_letter_id).first()
        if row is None:
            raise IntegrationError("Dead letter not found", 404)
        job = IntegrationJob.query.filter_by(id=row.job_id).first()
        if job is None:
            raise IntegrationError("Job not found", 404)
        job.status = INTEGRATION_JOB_PENDING
        job.retry_count = 0
        row.replayed = True
        db.session.commit()
        return IntegrationQueueService.process_job(job.id)


class SandboxService:
    @staticmethod
    def status():
        adapters = AdapterManager.list_adapters()
        plugins = PluginManager.list_plugins()
        return {
            "status": "OK",
            "sandbox": True,
            "adapters": adapters["count"],
            "plugins": plugins["count"],
            "supported_events": EventRegistry.list_event_types(),
        }

    @staticmethod
    def lis_result(data):
        AdapterManager.initialize()
        AdapterManager.connect("LIS")
        payload = data or {"result_id": "SANDBOX-RESULT", "status": "FINAL"}
        return AdapterManager.receive("LIS", payload)

    @staticmethod
    def his_patient(data):
        AdapterManager.initialize()
        AdapterManager.connect("HIS")
        payload = data or {"patient_id": "SANDBOX-PATIENT", "name": "Sandbox Patient"}
        return AdapterManager.receive("HIS", payload)

    @staticmethod
    def payment_callback(data):
        AdapterManager.initialize()
        AdapterManager.connect("PAYMENT")
        payload = data or {"transaction_id": "SANDBOX-TXN", "status": "PAID"}
        return AdapterManager.receive("PAYMENT", payload)

    @staticmethod
    def webhook_test(data):
        IntegrationPlatformService.ensure_defaults()
        webhook = WebhookEndpoint.query.first()
        if webhook is None:
            raise IntegrationError("No webhook configured", 400)
        return WebhookEngineService.test(webhook.id, data or {})
