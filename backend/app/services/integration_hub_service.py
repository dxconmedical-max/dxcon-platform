"""Integration Hub business logic for Phase 4 Sprint 4.1."""

from __future__ import annotations

from typing import Any

from app.core.statuses import INTEGRATION_JOB_FAILED, INTEGRATION_JOB_PENDING
from app.integrations.adapter_manager import AdapterManager
from app.integrations.audit_trail import IntegrationAuditTrail
from app.integrations.connector_registry import ConnectorRegistry
from app.integrations.models import IntegrationPlatformAuditLog
from app.models.integration_platform import IntegrationDeadLetter, IntegrationJob, WebhookEndpoint
from app.services.api_platform_service import ApiClientService, ApiKeyService
from app.services.integration_platform_service import (
    IntegrationPlatformService,
    IntegrationQueueService,
    SandboxService,
    WebhookEngineService,
)

HUB_ROLES = ("SUPER_ADMIN", "ADMIN")

SUPPORTED_ADAPTERS = ("HIS", "LIS", "EMR", "ERP", "INSURANCE", "PAYMENT")

SANDBOX_HANDLERS = {
    "HIS": SandboxService.his_patient,
    "LIS": SandboxService.lis_result,
    "EMR": SandboxService.emr_record,
    "ERP": SandboxService.erp_order,
    "INSURANCE": SandboxService.insurance_claim,
    "PAYMENT": SandboxService.payment_callback,
}


class IntegrationHubError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_hub() -> dict[str, Any]:
    IntegrationPlatformService.ensure_defaults()
    ConnectorRegistry.ensure_defaults()
    ApiClientService.ensure_defaults()
    AdapterManager.initialize()
    return {"ready": True}


def dashboard_payload() -> dict[str, Any]:
    ensure_hub()
    connectors = ConnectorRegistry.list_connectors()
    adapters = AdapterManager.list_adapters()
    webhooks = WebhookEngineService.list_webhooks()
    api_keys = ApiKeyService.list_keys()
    retry_jobs = list_retry_queue()
    dead_letters = IntegrationQueueService.list_dead_letters()
    audit = IntegrationAuditTrail.list_entries(page_size=5)
    return {
        "hub": "Integration Center",
        "phase": "4.1",
        "sprint": "Integration Hub",
        "status": "OK",
        "summary": {
            "connectors": connectors["count"],
            "adapters": adapters["count"],
            "webhooks": webhooks["count"],
            "api_keys": api_keys["count"],
            "retry_queue": retry_jobs["count"],
            "dead_letters": dead_letters["count"],
            "audit_entries": audit["count"],
        },
        "adapters_supported": list(SUPPORTED_ADAPTERS),
        "features": [
            "Integration Center Dashboard",
            "Connector Registry",
            "HIS Adapter",
            "LIS Adapter",
            "EMR Adapter",
            "ERP Adapter",
            "Insurance Adapter",
            "Payment Adapter",
            "Webhook Manager",
            "API Key Manager",
            "Retry Queue",
            "Dead Letter Queue",
            "Integration Audit Log",
            "Sandbox Test Endpoint",
            "Verification Report",
        ],
    }


def list_connectors() -> dict[str, Any]:
    ensure_hub()
    return ConnectorRegistry.list_connectors()


def list_adapters() -> dict[str, Any]:
    ensure_hub()
    payload = AdapterManager.list_adapters()
    types = {item["type"] for item in payload["adapters"]}
    payload["supported"] = sorted(types.intersection(set(SUPPORTED_ADAPTERS)))
    return payload


def list_webhooks() -> dict[str, Any]:
    ensure_hub()
    return WebhookEngineService.list_webhooks()


def list_api_keys() -> dict[str, Any]:
    ensure_hub()
    return ApiKeyService.list_keys()


def list_retry_queue() -> dict[str, Any]:
    ensure_hub()
    rows = (
        IntegrationJob.query.filter(
            IntegrationJob.status.in_((INTEGRATION_JOB_PENDING, INTEGRATION_JOB_FAILED))
        )
        .order_by(IntegrationJob.created_at.desc())
        .all()
    )
    return {"count": len(rows), "jobs": [row.to_dict() for row in rows]}


def list_dead_letters() -> dict[str, Any]:
    ensure_hub()
    return IntegrationQueueService.list_dead_letters()


def list_audit(*, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    ensure_hub()
    return IntegrationAuditTrail.list_entries(page=page, page_size=page_size)


def sandbox_test(
    adapter_type: str,
    payload: dict[str, Any] | None = None,
    *,
    actor: str | None = None,
) -> dict[str, Any]:
    ensure_hub()
    adapter = (adapter_type or "").upper()
    handler = SANDBOX_HANDLERS.get(adapter)
    if handler is None:
        raise IntegrationHubError(
            f"Unsupported adapter_type: {adapter_type}. "
            f"Supported: {', '.join(SUPPORTED_ADAPTERS)}"
        )
    result = handler(payload or {})
    audit = IntegrationAuditTrail.write(
        action="SANDBOX_TEST",
        resource_type="Adapter",
        resource_id=adapter,
        detail={"payload": payload or {}, "result": result},
        actor=actor or "SYSTEM",
    )
    return {
        "adapter_type": adapter,
        "sandbox": True,
        "result": result,
        "audit_id": audit["id"],
    }


def hub_health() -> dict[str, Any]:
    ensure_hub()
    sandbox = SandboxService.status()
    return {
        "status": sandbox["status"],
        "sandbox": sandbox["sandbox"],
        "connectors_active": _count_active_connectors(),
        "webhooks_active": WebhookEndpoint.query.count(),
        "dead_letters": IntegrationDeadLetter.query.count(),
        "audit_entries": IntegrationPlatformAuditLog.query.count(),
    }


def _count_active_connectors() -> int:
    from app.integrations.models import IntegrationConnector

    return IntegrationConnector.query.filter_by(status="ACTIVE").count()
