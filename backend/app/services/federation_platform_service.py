"""Federation Platform business logic for Phase 7.10."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.federation_core import FederatedLab, FederationEvent, FederationProvider
from app.services.federation_service import FederationService
from app.services.reporting_service import _safe

FEDERATION_PLATFORM_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Regional Hub",
    "National Hub",
    "Clinic Federation",
    "Laboratory Federation",
    "Cross Organization Exchange",
    "Sync Queue",
    "Federation Audit",
)


def ensure_federation_platform() -> dict[str, Any]:
    return {"ready": True}


def regional_hub() -> dict[str, Any]:
    labs = FederationService.list_labs(page_size=100)
    return {"report": "regional_hub", "labs": labs.get("count", 0), "scope": "regional"}


def national_hub() -> dict[str, Any]:
    providers = _safe(lambda: FederationProvider.query.count(), 0)
    return {"report": "national_hub", "providers": providers, "scope": "national"}


def clinic_federation() -> dict[str, Any]:
    return {"report": "clinic_federation", "status": "READY", "route": "/federation"}


def laboratory_federation() -> dict[str, Any]:
    labs = FederationService.list_labs(page_size=50)
    return {"report": "laboratory_federation", "labs": labs.get("count", 0), "items": labs.get("labs", [])[:10]}


def cross_organization_exchange() -> dict[str, Any]:
    return {"report": "cross_organization_exchange", "protocol": "federation_event_bus", "status": "READY"}


def sync_queue() -> dict[str, Any]:
    pending = _safe(lambda: FederationEvent.query.filter(FederationEvent.severity == "WARNING").count(), 0)
    return {"report": "sync_queue", "pending_events": pending}


def federation_audit() -> dict[str, Any]:
    events = _safe(lambda: FederationEvent.query.order_by(FederationEvent.created_at.desc()).limit(25).all(), [])
    return {"report": "federation_audit", "count": len(events), "events": [e.to_dict() for e in events]}


def dashboard_payload() -> dict[str, Any]:
    labs = laboratory_federation()
    return {
        "platform": "Federation Platform",
        "phase": "7.10",
        "sprint": "Federation",
        "status": "OK",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {"federated_labs": labs.get("labs", 0), "providers": national_hub().get("providers", 0)},
        "features": list(FEATURES),
    }


def federation_platform_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.10",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "regional_hub": regional_hub(),
            "national_hub": national_hub(),
            "clinic_federation": clinic_federation(),
            "laboratory_federation": laboratory_federation(),
            "cross_organization_exchange": cross_organization_exchange(),
            "sync_queue": sync_queue(),
            "federation_audit": federation_audit(),
        },
        "legacy_routes": ["/api/v1/federation", "/federation"],
        "architecture_doc": "docs/architecture/FEDERATION_ARCHITECTURE.md",
    }
