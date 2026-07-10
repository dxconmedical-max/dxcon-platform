"""Pilot readiness service — Release 2.0 Epic 8."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from flask import current_app

from app.extensions.db import db
from app.pilot_readiness.audit import run_production_readiness_audit
from app.pilot_readiness.models import (
    ONBOARDING_STEPS,
    ORG_SETUP_STEPS,
    KnowledgeArticle,
    OnboardingSession,
    OrgSetupSession,
    PartnerRegistration,
    PilotScorecardRun,
    TrainingGuide,
)
from app.partner_foundation.service import PartnerFoundationError, upsert_organization


class PilotReadinessError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _load_payload(row) -> dict:
    if not row or not row.payload_json:
        return {}
    try:
        return json.loads(row.payload_json)
    except json.JSONDecodeError:
        return {}


def _save_payload(row, payload: dict) -> None:
    row.payload_json = json.dumps(payload, default=str)
    row.updated_at = _utcnow()


def _next_step(steps: tuple[str, ...], current: str) -> str | None:
    try:
        idx = steps.index(current)
        return steps[idx + 1] if idx + 1 < len(steps) else None
    except ValueError:
        return steps[0] if steps else None


# --- Onboarding ---


def start_onboarding(onboarding_type: str, requester_email: str = "") -> dict:
    if onboarding_type not in {
        "LABORATORY",
        "CLINIC",
        "HOSPITAL",
        "DOCTOR",
        "COLLECTOR_COMPANY",
        "CORPORATE",
    }:
        raise PilotReadinessError("invalid onboarding_type")
    row = OnboardingSession(
        session_code=_code("ONB"),
        onboarding_type=onboarding_type,
        current_step="organization",
        requester_email=requester_email,
    )
    db.session.add(row)
    return row.to_dict()


def advance_onboarding(session_code: str, step: str, data: dict) -> dict:
    row = OnboardingSession.query.filter_by(session_code=session_code).first()
    if not row:
        raise PilotReadinessError("session not found")
    if row.status not in ("IN_PROGRESS",):
        raise PilotReadinessError("session not active")
    payload = _load_payload(row)
    payload[step] = data
    _save_payload(row, payload)
    if step == row.current_step:
        nxt = _next_step(ONBOARDING_STEPS, step)
        if nxt:
            row.current_step = nxt
        else:
            row.status = "COMPLETED"
            row.completed_at = _utcnow()
    if step == "activation" and data.get("activate"):
        row.status = "ACTIVATED"
        row.completed_at = _utcnow()
    return {**row.to_dict(), "payload": payload}


def complete_onboarding_organization(session_code: str, org_data: dict, actor: str = "") -> dict:
    row = OnboardingSession.query.filter_by(session_code=session_code).first()
    if not row:
        raise PilotReadinessError("session not found")
    org_type_map = {
        "LABORATORY": "LABORATORY",
        "CLINIC": "CLINIC",
        "HOSPITAL": "HOSPITAL",
        "DOCTOR": "CLINIC",
        "COLLECTOR_COMPANY": "LOGISTICS",
        "CORPORATE": "CORPORATE",
    }
    org_payload = {
        "organization_name": org_data.get("organization_name") or org_data.get("name"),
        "organization_type": org_type_map.get(row.onboarding_type, "CLINIC"),
        "status": "PENDING",
        **org_data,
    }
    try:
        org = upsert_organization(org_payload, actor=actor or row.requester_email)
    except PartnerFoundationError as exc:
        raise PilotReadinessError(str(exc)) from exc
    row.organization_id = org.get("id")
    payload = _load_payload(row)
    payload["organization"] = org
    _save_payload(row, payload)
    return {**row.to_dict(), "organization": org}


def get_onboarding(session_code: str) -> dict:
    row = OnboardingSession.query.filter_by(session_code=session_code).first()
    if not row:
        raise PilotReadinessError("session not found")
    return {**row.to_dict(), "payload": _load_payload(row), "steps": list(ONBOARDING_STEPS)}


# --- Partner self-registration ---


def register_partner(data: dict) -> dict:
    partner_type = (data.get("partner_type") or "").upper()
    if partner_type not in ("CLINIC", "LAB", "HOSPITAL", "LABORATORY"):
        raise PilotReadinessError("partner_type must be CLINIC, LAB, or HOSPITAL")
    if not data.get("organization_name") or not data.get("contact_email"):
        raise PilotReadinessError("organization_name and contact_email required")
    row = PartnerRegistration(
        registration_code=_code("REG"),
        partner_type=partner_type,
        organization_name=data["organization_name"],
        contact_email=data["contact_email"],
        contact_phone=data.get("contact_phone"),
        domain=data.get("domain"),
        address=data.get("address"),
        status="PENDING",
    )
    db.session.add(row)
    return row.to_dict()


def review_partner_registration(registration_code: str, action: str, actor: str, note: str = "") -> dict:
    row = PartnerRegistration.query.filter_by(registration_code=registration_code).first()
    if not row:
        raise PilotReadinessError("registration not found")
    action = action.upper()
    if action == "APPROVE":
        row.status = "APPROVED"
        row.reviewed_by = actor
        row.review_note = note
    elif action == "REJECT":
        row.status = "REJECTED"
        row.reviewed_by = actor
        row.review_note = note or "rejected"
    elif action == "ACTIVATE":
        if row.status != "APPROVED":
            raise PilotReadinessError("must be approved before activation")
        org = upsert_organization(
            {
                "organization_name": row.organization_name,
                "organization_type": row.partner_type,
                "status": "ACTIVE",
                "contact_email": row.contact_email,
            },
            actor=actor,
        )
        row.organization_id = org.get("id")
        row.status = "ACTIVATED"
        row.activated_at = _utcnow()
        row.reviewed_by = actor
    else:
        raise PilotReadinessError("action must be APPROVE, REJECT, or ACTIVATE")
    row.updated_at = _utcnow()
    return row.to_dict()


def list_partner_registrations(status: str | None = None) -> list[dict]:
    q = PartnerRegistration.query
    if status:
        q = q.filter_by(status=status.upper())
    return [r.to_dict() for r in q.order_by(PartnerRegistration.created_at.desc()).limit(100)]


# --- Organization setup wizard ---


def start_org_setup(organization_id: str) -> dict:
    existing = OrgSetupSession.query.filter_by(
        organization_id=organization_id, status="IN_PROGRESS"
    ).first()
    if existing:
        return {**existing.to_dict(), "payload": _load_payload(existing), "steps": list(ORG_SETUP_STEPS)}
    row = OrgSetupSession(organization_id=organization_id, current_step="organization")
    db.session.add(row)
    return {**row.to_dict(), "payload": {}, "steps": list(ORG_SETUP_STEPS)}


def advance_org_setup(organization_id: str, step: str, data: dict) -> dict:
    row = OrgSetupSession.query.filter_by(organization_id=organization_id, status="IN_PROGRESS").first()
    if not row:
        raise PilotReadinessError("setup session not found")
    payload = _load_payload(row)
    payload[step] = data
    _save_payload(row, payload)
    if step == row.current_step:
        nxt = _next_step(ORG_SETUP_STEPS, step)
        if nxt:
            row.current_step = nxt
        else:
            row.status = "COMPLETED"
            row.completed_at = _utcnow()
    if step == "finish":
        row.status = "COMPLETED"
        row.completed_at = _utcnow()
    return {**row.to_dict(), "payload": payload}


# --- Knowledge base & training ---


def list_knowledge_articles(category: str | None = None, q: str | None = None) -> list[dict]:
    query = KnowledgeArticle.query.filter_by(published=True)
    if category:
        query = query.filter_by(category=category.upper())
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(KnowledgeArticle.title.ilike(like), KnowledgeArticle.body.ilike(like))
        )
    return [a.to_dict() for a in query.order_by(KnowledgeArticle.updated_at.desc()).limit(50)]


def list_training_guides(audience: str | None = None) -> list[dict]:
    query = TrainingGuide.query.filter_by(published=True)
    if audience:
        query = query.filter_by(audience=audience.upper())
    return [g.to_dict() for g in query.order_by(TrainingGuide.sort_order).all()]


def seed_knowledge_and_training() -> dict:
    if KnowledgeArticle.query.count() == 0:
        articles = [
            ("FAQ-001", "FAQ", "How do I reset my password?", "Use Forgot Password on the login page."),
            ("REL-001", "RELEASE_NOTES", "Release 2.0", "Patient marketplace, mobile MVP, pilot readiness."),
            ("OPS-001", "ARTICLE", "Production health dashboard", "Monitor API, database, and queue status."),
        ]
        for code, cat, title, body in articles:
            db.session.add(KnowledgeArticle(article_code=code, category=cat, title=title, body=body))
    if TrainingGuide.query.count() == 0:
        guides = [
            ("PATIENT", "Patient Guide", "Book tests, pay by QR, view released results."),
            ("COLLECTOR", "Collector Guide", "Accept jobs, check in, scan samples, handover."),
            ("DOCTOR", "Doctor Guide", "Review and release clinical reports."),
            ("CLINIC", "Clinic Guide", "Register patients and manage orders."),
            ("LAB", "Lab Guide", "Accession samples and enter results."),
            ("ADMIN", "Admin Guide", "Onboard organizations and manage subscriptions."),
        ]
        for i, (aud, title, body) in enumerate(guides):
            db.session.add(
                TrainingGuide(guide_code=f"TRN-{aud}", audience=aud, title=title, body=body, sort_order=i)
            )
    return {"articles": KnowledgeArticle.query.count(), "guides": TrainingGuide.query.count()}


# --- Health & operations dashboards ---


def production_health_dashboard() -> dict:
    from app.observability.health_service import HealthPlatformService

    app = current_app._get_current_object()
    health = HealthPlatformService.evaluate()
    audit = run_production_readiness_audit(app)
    by_name = {c["component"]: c for c in health.get("components", [])}
    return {
        "api": {"status": health.get("status", "OK")},
        "database": by_name.get("database", {}),
        "redis": by_name.get("redis", {}),
        "queue": by_name.get("queue", {}),
        "storage": by_name.get("storage", {}),
        "mail": by_name.get("smtp", {}),
        "production_score": audit["production_readiness_score"],
        "components": health.get("components", []),
    }


def operations_realtime_dashboard() -> dict:
    from app.operations_center.service import dashboard as ops_dashboard

    data = ops_dashboard()
    return {
        "widgets": data.get("widgets", {}),
        "recent_incidents": data.get("recent_incidents", []),
        "recent_tickets": data.get("recent_tickets", []),
        "note": "Realtime metrics aggregated from operations center",
    }


# --- Pilot scorecard ---


def compute_pilot_scorecard() -> dict:
    from app.models.biz_order import BizOrder
    from app.models.operations_center import SupportTicket
    from app.patient_marketplace.models import MpBooking

    metrics = {
        "activations": PartnerRegistration.query.filter_by(status="ACTIVATED").count(),
        "orders": BizOrder.query.count(),
        "bookings": MpBooking.query.count(),
        "open_tickets": SupportTicket.query.filter(SupportTicket.status.in_(("OPEN", "IN_PROGRESS"))).count(),
        "onboarding_in_progress": OnboardingSession.query.filter_by(status="IN_PROGRESS").count(),
    }
    weights = {"activations": 20, "orders": 25, "bookings": 25, "open_tickets": -10, "onboarding_in_progress": 10}
    raw = (
        min(metrics["activations"], 5) * weights["activations"]
        + min(metrics["orders"], 10) * 2.5
        + min(metrics["bookings"], 10) * 2.5
        + max(0, 10 - metrics["open_tickets"]) * 2
        + min(metrics["onboarding_in_progress"], 3) * 3
    )
    score = min(100, round(raw))
    run = PilotScorecardRun(
        run_code=_code("PSC"),
        score_pct=score,
        metrics_json=json.dumps(metrics),
    )
    db.session.add(run)
    return {"score_pct": score, "metrics": metrics, "run_code": run.run_code}


# --- Production certificate ---


def generate_production_certificate() -> dict:
    app = current_app._get_current_object()
    audit = run_production_readiness_audit(app)
    pilot = compute_pilot_scorecard()
    score = audit["production_readiness_score"]
    critical = audit["summary"].get("critical_blockers", [])
    if critical:
        status = "FAIL"
    elif score >= 85 and pilot["score_pct"] >= 60:
        status = "PASS"
    else:
        status = "WARNING"
    return {
        "status": status,
        "production_readiness_score": score,
        "pilot_score": pilot["score_pct"],
        "critical_blockers": critical,
        "customer_pilot_ready": status != "FAIL" and pilot["score_pct"] >= 50,
        "commercial_ready": status == "PASS" and pilot["score_pct"] >= 70,
        "go_live_recommendation": "PROCEED" if status == "PASS" else "REMEDIATE" if status == "FAIL" else "PILOT_ONLY",
    }


def system_configuration_summary() -> dict:
    app = current_app._get_current_object()
    return {
        "timezone": app.config.get("DEFAULT_TIMEZONE", "Asia/Ho_Chi_Minh"),
        "currency": app.config.get("DEFAULT_CURRENCY", "VND"),
        "country": app.config.get("DEFAULT_COUNTRY", "VN"),
        "language": app.config.get("DEFAULT_LANGUAGE", "vi"),
        "smtp": {
            "host": bool(app.config.get("SMTP_HOST")),
            "from": app.config.get("SMTP_FROM", ""),
        },
        "notification_channels": ["email", "push", "webhook", "sms"],
    }


def subscription_plans() -> list[dict]:
    return [
        {
            "plan_code": "STARTER",
            "name": "Starter",
            "features": ["patient_portal", "basic_reporting"],
            "quota_users": 10,
            "quota_storage_gb": 5,
            "api_calls_monthly": 10000,
        },
        {
            "plan_code": "PROFESSIONAL",
            "name": "Professional",
            "features": ["marketplace", "collector_ops", "integrations"],
            "quota_users": 50,
            "quota_storage_gb": 50,
            "api_calls_monthly": 100000,
        },
        {
            "plan_code": "ENTERPRISE",
            "name": "Enterprise",
            "features": ["white_label", "advanced_analytics", "sla"],
            "quota_users": 500,
            "quota_storage_gb": 500,
            "api_calls_monthly": 1000000,
        },
        {
            "plan_code": "WHITE_LABEL",
            "name": "White Label",
            "features": ["custom_branding", "dedicated_support"],
            "quota_users": -1,
            "quota_storage_gb": -1,
            "api_calls_monthly": -1,
        },
    ]
