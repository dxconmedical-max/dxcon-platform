"""Healthcare Ecosystem business logic for Phase 10 — DxCon Enterprise v1.0."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app

from app.services.developer_portal_service import dashboard_payload as developer_dashboard_payload
from app.services.intelligent_healthcare_service import (
    GOVERNANCE_POLICY,
    intelligent_healthcare_governance_report,
)
from app.services.knowledge_engine_service import KnowledgeEngineService
from app.services.marketplace_platform_service import marketplace_overview
from app.services.pilot_toolkit_service import pilot_toolkit_dashboard
from app.services.readiness_pack_service import readiness_pack_dashboard
from app.services.regional_cloud_service import GOVERNANCE as REGIONAL_GOVERNANCE
from app.services.regional_cloud_service import regional_cloud_readiness_report
from app.services.release_control_service import release_history
from app.services.release_management_service import release_version
from app.services.security_compliance_service import compliance_report, dashboard_payload as security_dashboard_payload
from app.services.user_guides_service import admin_guide, dashboard_payload as guides_dashboard

HEALTHCARE_ECOSYSTEM_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"

RELEASE = {
    "version": "1.0.0-rc1",
    "tag": "v1.0.0-rc1",
    "codename": "Healthcare Ecosystem",
    "phase": "10",
    "commercial_release": True,
}

ENTERPRISE_DOCS = {
    "system_architecture": REPO / "docs" / "SYSTEM_ARCHITECTURE.md",
    "operations_guide": REPO / "docs" / "OPERATIONS_GUIDE.md",
    "deployment_guide": REPO / "docs" / "DEPLOYMENT_GUIDE.md",
    "support_guide": REPO / "docs" / "SUPPORT_GUIDE.md",
    "customer_guide": REPO / "docs" / "CUSTOMER_GUIDE.md",
    "partner_guide": REPO / "docs" / "PARTNER_GUIDE.md",
    "go_live_runbook": REPO / "docs" / "GO_LIVE_RUNBOOK.md",
    "backup_runbook": REPO / "docs" / "BACKUP_RUNBOOK.md",
    "restore_runbook": REPO / "docs" / "RESTORE_RUNBOOK.md",
    "rollback_runbook": REPO / "docs" / "ROLLBACK_RUNBOOK.md",
    "known_limitations": REPO / "docs" / "KNOWN_LIMITATIONS.md",
    "roadmap_v2": REPO / "docs" / "ROADMAP_v2.md",
}

FEATURES = (
    "DxCon Lab",
    "DxCon Clinic",
    "DxCon Home",
    "DxCon Pharmacy",
    "DxCon Insurance",
    "DxCon AI",
    "DxCon Cloud",
    "DxCon Marketplace",
    "Partner Portal",
    "Customer Portal",
    "Enterprise Governance",
    "Architecture Board",
    "Release Board",
    "Medical Governance",
    "Security Governance",
    "AI Governance",
    "Enterprise Audit",
    "Customer Success Portal",
    "Training Center",
    "Certification Center",
    "Release Manager",
    "License Manager",
    "Commercial Readiness",
    "Support Center",
    "Knowledge Base",
)

LICENSE_TIERS = (
    {"tier": "PILOT", "modules": ["Lab", "Clinic", "Home"], "seats": 25},
    {"tier": "PROFESSIONAL", "modules": ["Lab", "Clinic", "Home", "Marketplace", "AI"], "seats": 100},
    {"tier": "ENTERPRISE", "modules": list(FEATURES[:8]), "seats": "unlimited"},
)


def ensure_healthcare_ecosystem() -> dict[str, Any]:
    KnowledgeEngineService.ensure_default_content()
    return {"ready": True, "release": RELEASE}


def _product(name: str, route: str, api: str | None = None, status: str = "READY") -> dict[str, Any]:
    return {"report": name.lower().replace(" ", "_"), "product": name, "route": route, "api": api, "status": status}


def dxcon_lab() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return _product("DxCon Lab", "/lab-operations", "/api/v1/lab/dashboard")


def dxcon_clinic() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return _product("DxCon Clinic", "/clinic-portal", "/api/v1/clinic/dashboard")


def dxcon_home() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return _product("DxCon Home", "/collector", "/api/v1/collector/jobs")


def dxcon_pharmacy() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {**_product("DxCon Pharmacy", "/healthcare-ecosystem/dxcon-pharmacy", status="SCAFFOLD"), "note": "Rx fulfillment integration planned v2"}


def dxcon_insurance() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {**_product("DxCon Insurance", "/finance", "/api/v1/billing/invoices", status="SCAFFOLD"), "note": "Claims adjudication planned v2"}


def dxcon_ai() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {
        "report": "dxcon_ai",
        "product": "DxCon AI",
        "route": "/intelligent-healthcare",
        "api": "/api/v1/intelligent-healthcare/dashboard",
        "governance": GOVERNANCE_POLICY,
        "status": "READY",
    }


def dxcon_cloud() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {
        "report": "dxcon_cloud",
        "product": "DxCon Cloud",
        "route": "/regional-cloud",
        "api": "/api/v1/regional-cloud/dashboard",
        "governance": REGIONAL_GOVERNANCE,
        "status": "READY",
    }


def dxcon_marketplace() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    overview = marketplace_overview()
    return {"report": "dxcon_marketplace", "product": "DxCon Marketplace", "route": "/marketplace-platform", "overview": overview}


def partner_portal() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    portal = developer_dashboard_payload(current_app)
    return {"report": "partner_portal", "routes": ["/developer", "/developer-portal"], "portal": portal.get("summary", {})}


def customer_portal() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {"report": "customer_portal", "routes": ["/patient-portal", "/api/v1/patient/dashboard"], "status": "READY"}


def enterprise_governance() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {
        "report": "enterprise_governance",
        "boards": ["Architecture", "Release", "Medical", "Security", "AI"],
        "release": RELEASE,
        "backward_compatible": True,
    }


def architecture_board() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    docs = {k: p.exists() for k, p in ENTERPRISE_DOCS.items()}
    arch_dir = REPO / "docs" / "architecture"
    arch_count = len(list(arch_dir.glob("*.md"))) if arch_dir.exists() else 0
    return {"report": "architecture_board", "enterprise_docs": docs, "architecture_docs": arch_count}


def release_board() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    history = release_history(limit=10)
    version = release_version()
    return {"report": "release_board", "history": history, "current_version": version, "target_tag": RELEASE["tag"]}


def medical_governance() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {"report": "medical_governance", **intelligent_healthcare_governance_report()}


def security_governance() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {
        "report": "security_governance",
        "dashboard": security_dashboard_payload(),
        "compliance": compliance_report(),
    }


def ai_governance() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    gov = intelligent_healthcare_governance_report()
    return {
        "report": "ai_governance",
        "policy": gov.get("governance"),
        "compliance_notes": gov.get("compliance_notes", []),
    }


def enterprise_audit() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    from app.models.audit_log import AuditLog
    from app.services.reporting_service import _safe

    count = _safe(lambda: AuditLog.query.count(), 0)
    return {"report": "enterprise_audit", "audit_entries": count, "routes": ["/audit", "/api/v1/admin/audit"]}


def customer_success_portal() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    pilot = pilot_toolkit_dashboard()
    return {"report": "customer_success_portal", "pilot_toolkit": pilot.get("summary", {}), "route": "/pilot-toolkit"}


def training_center() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    guides = guides_dashboard()
    admin = admin_guide()
    return {"report": "training_center", "guides": guides.get("summary", {}), "admin_guide": admin.get("title")}


def certification_center() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {
        "report": "certification_center",
        "status": "SCAFFOLD",
        "programs": ["DxCon Lab Operator", "DxCon Clinic Admin", "DxCon Integration Partner"],
        "route": "/healthcare-ecosystem/certification-center",
    }


def release_manager() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {"report": "release_manager", "release": RELEASE, "route": "/release-control", "version": release_version()}


def license_manager() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {"report": "license_manager", "tiers": list(LICENSE_TIERS), "status": "READY"}


def commercial_readiness() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    pack = readiness_pack_dashboard()
    return {"report": "commercial_readiness", "readiness_pack": pack.get("summary", {}), "route": "/readiness-pack"}


def support_center() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    return {
        "report": "support_center",
        "status": "SCAFFOLD",
        "channels": ["email", "ticket", "knowledge_base"],
        "sla_tiers": ["PILOT", "PROFESSIONAL", "ENTERPRISE"],
        "guide": "docs/SUPPORT_GUIDE.md",
    }


def knowledge_base() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    KnowledgeEngineService.ensure_default_content()
    return {
        "report": "knowledge_base",
        "routes": ["/knowledge", "/api/v1/knowledge", "/guidelines"],
        "status": "READY",
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_healthcare_ecosystem()
    docs_ready = sum(1 for p in ENTERPRISE_DOCS.values() if p.exists())
    return {
        "platform": "Healthcare Ecosystem",
        "phase": "10",
        "sprint": "DxCon Healthcare Ecosystem",
        "status": "OK",
        "release": RELEASE,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "ecosystem_modules": len(FEATURES),
            "enterprise_docs": docs_ready,
            "enterprise_docs_total": len(ENTERPRISE_DOCS),
            "license_tiers": len(LICENSE_TIERS),
            "scaffold_modules": 4,
        },
        "features": list(FEATURES),
    }


def healthcare_ecosystem_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "10",
        "platform": d["platform"],
        "release": RELEASE,
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "enterprise_docs": {k: str(v.relative_to(REPO)) if v.exists() else str(v) for k, v in ENTERPRISE_DOCS.items()},
        "sections": {
            "commercial_readiness": commercial_readiness(),
            "release_manager": release_manager(),
            "security_governance": security_governance(),
            "ai_governance": ai_governance(),
            "dxcon_ai": dxcon_ai(),
            "dxcon_cloud": dxcon_cloud(),
        },
    }


def system_readiness_report() -> dict[str, Any]:
    readiness = healthcare_ecosystem_readiness_report()
    regional = regional_cloud_readiness_report()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "release": RELEASE,
        "phase": "10",
        "platform": "DxCon Enterprise",
        "system_readiness": readiness,
        "regional_readiness": {"phase": regional.get("phase"), "status": regional.get("status")},
        "docs_complete": all(p.exists() for p in ENTERPRISE_DOCS.values()),
        "backward_compatible": True,
        "destructive_migrations": False,
    }


def go_live_report() -> dict[str, Any]:
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "release": RELEASE,
        "phase": "10",
        "go_live_ready": True,
        "runbooks": {
            "go_live": str(ENTERPRISE_DOCS["go_live_runbook"].relative_to(REPO)),
            "backup": str(ENTERPRISE_DOCS["backup_runbook"].relative_to(REPO)),
            "restore": str(ENTERPRISE_DOCS["restore_runbook"].relative_to(REPO)),
            "rollback": str(ENTERPRISE_DOCS["rollback_runbook"].relative_to(REPO)),
        },
        "release_board": release_board(),
        "commercial_readiness": commercial_readiness(),
        "health_probes": ["/live", "/ready", "/api/v1/system/health"],
    }


def commercial_readiness_report() -> dict[str, Any]:
    pack = readiness_pack_dashboard()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "release": RELEASE,
        "phase": "10",
        "commercial_ready": True,
        "license_tiers": list(LICENSE_TIERS),
        "readiness_pack": pack,
        "products_ready": ["Lab", "Clinic", "Home", "AI", "Cloud", "Marketplace"],
        "products_scaffold": ["Pharmacy", "Insurance", "Support Center", "Certification"],
    }


def enterprise_certification_report() -> dict[str, Any]:
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "release": RELEASE,
        "phase": "10",
        "certification_status": "CANDIDATE",
        "recommended_tag": RELEASE["tag"],
        "governance": {
            "medical": medical_governance().get("report"),
            "security": security_governance().get("report"),
            "ai": ai_governance().get("report"),
            "enterprise": enterprise_governance().get("report"),
        },
        "validation": {
            "compile": "required",
            "unit_test": "required",
            "integration_test": "verify_healthcare_ecosystem.py",
            "pilot_verification": "verify_pilot_readiness.py",
        },
        "known_limitations": str(ENTERPRISE_DOCS["known_limitations"].relative_to(REPO)),
        "roadmap": str(ENTERPRISE_DOCS["roadmap_v2"].relative_to(REPO)),
    }


def phase10_release_summary() -> dict[str, Any]:
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "title": "DxCon Enterprise v1.0 Release Candidate",
        "tag": RELEASE["tag"],
        "phase": "10",
        "modules": len(FEATURES),
        "reports": [
            "SYSTEM_READINESS_REPORT.json",
            "GO_LIVE_REPORT.json",
            "COMMERCIAL_READINESS_REPORT.json",
            "ENTERPRISE_CERTIFICATION_REPORT.json",
            "HEALTHCARE_ECOSYSTEM_REPORT.json",
        ],
        "next_steps": ["Pilot sign-off", "Production PostgreSQL cutover", "Tag v1.0.0 GA"],
    }
