"""Pilot readiness API — Release 2.0 Epic 8."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.core.authz import roles_required
from app.extensions.db import db
from app.pilot_readiness.audit import run_production_readiness_audit
from app.pilot_readiness.service import (
    PilotReadinessError,
    advance_onboarding,
    advance_org_setup,
    complete_onboarding_organization,
    compute_pilot_scorecard,
    generate_production_certificate,
    get_onboarding,
    list_knowledge_articles,
    list_partner_registrations,
    list_training_guides,
    operations_realtime_dashboard,
    production_health_dashboard,
    register_partner,
    review_partner_registration,
    seed_knowledge_and_training,
    start_onboarding,
    start_org_setup,
    subscription_plans,
    system_configuration_summary,
)

pilot_readiness_bp = Blueprint("pilot_readiness", __name__, url_prefix="/api/v1/pilot-readiness")


def _actor() -> str:
    return session.get("email") or request.headers.get("X-Actor") or request.headers.get("X-User-Email") or "SYSTEM"


@pilot_readiness_bp.route("/audit", methods=["GET"])
def api_audit():
    from flask import current_app

    data = run_production_readiness_audit(current_app._get_current_object())
    return {"success": True, "data": data}, 200


@pilot_readiness_bp.route("/health-dashboard", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "EXECUTIVE")
def api_health_dashboard():
    return {"success": True, "data": production_health_dashboard()}, 200


@pilot_readiness_bp.route("/operations-dashboard", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "EXECUTIVE", "OPERATIONS")
def api_operations_dashboard():
    return {"success": True, "data": operations_realtime_dashboard()}, 200


@pilot_readiness_bp.route("/certificate", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
def api_certificate():
    try:
        data = generate_production_certificate()
        db.session.commit()
        return {"success": True, "data": data}, 200
    except Exception as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 500


@pilot_readiness_bp.route("/pilot-scorecard", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "EXECUTIVE")
def api_pilot_scorecard():
    try:
        data = compute_pilot_scorecard()
        db.session.commit()
        return {"success": True, "data": data}, 200
    except Exception as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 500


@pilot_readiness_bp.route("/onboarding", methods=["POST"])
def api_start_onboarding():
    payload = request.get_json(silent=True) or {}
    try:
        data = start_onboarding(
            payload.get("onboarding_type", ""),
            requester_email=payload.get("requester_email", ""),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/onboarding/<session_code>", methods=["GET"])
def api_get_onboarding(session_code: str):
    try:
        return {"success": True, "data": get_onboarding(session_code)}, 200
    except PilotReadinessError as exc:
        return {"success": False, "error": str(exc)}, 404


@pilot_readiness_bp.route("/onboarding/<session_code>/step", methods=["POST"])
def api_advance_onboarding(session_code: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = advance_onboarding(session_code, payload.get("step", ""), payload.get("data", {}))
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/onboarding/<session_code>/organization", methods=["POST"])
def api_onboarding_organization(session_code: str):
    try:
        data = complete_onboarding_organization(session_code, request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/partner-registration", methods=["POST"])
def api_partner_register():
    try:
        data = register_partner(request.get_json(silent=True) or {})
        db.session.commit()
        return {"success": True, "data": data}, 201
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/partner-registration", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
def api_partner_list():
    return {
        "success": True,
        "data": list_partner_registrations(status=request.args.get("status")),
    }, 200


@pilot_readiness_bp.route("/partner-registration/<registration_code>/review", methods=["POST"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
def api_partner_review(registration_code: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = review_partner_registration(
            registration_code,
            payload.get("action", ""),
            actor=_actor(),
            note=payload.get("note", ""),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/org-setup/<organization_id>", methods=["POST"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "ORG_ADMIN")
def api_org_setup_start(organization_id: str):
    try:
        data = start_org_setup(organization_id)
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/org-setup/<organization_id>/step", methods=["POST"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "ORG_ADMIN")
def api_org_setup_step(organization_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = advance_org_setup(organization_id, payload.get("step", ""), payload.get("data", {}))
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PilotReadinessError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@pilot_readiness_bp.route("/knowledge", methods=["GET"])
def api_knowledge():
    seed_knowledge_and_training()
    db.session.commit()
    return {
        "success": True,
        "data": list_knowledge_articles(
            category=request.args.get("category"),
            q=request.args.get("q"),
        ),
    }, 200


@pilot_readiness_bp.route("/training", methods=["GET"])
def api_training():
    seed_knowledge_and_training()
    db.session.commit()
    return {
        "success": True,
        "data": list_training_guides(audience=request.args.get("audience")),
    }, 200


@pilot_readiness_bp.route("/system-config", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
def api_system_config():
    return {"success": True, "data": system_configuration_summary()}, 200


@pilot_readiness_bp.route("/subscription-plans", methods=["GET"])
def api_subscription_plans():
    return {"success": True, "data": subscription_plans()}, 200


@pilot_readiness_bp.route("/go-live-checklist", methods=["GET"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
def api_go_live_checklist():
    from flask import current_app

    audit = run_production_readiness_audit(current_app._get_current_object())
    items = [
        {"item": "SSL", "status": "PASS" if audit["production_readiness_score"] >= 70 else "WARNING"},
        {"item": "DNS", "status": "MANUAL"},
        {"item": "Cloudflare", "status": "MANUAL"},
        {"item": "SMTP", "status": next((f["status"] for f in audit["findings"] if f["name"] == "smtp"), "WARNING")},
        {"item": "Redis", "status": next((f["status"] for f in audit["findings"] if f["name"] == "redis"), "WARNING")},
        {"item": "Backup", "status": next((f["status"] for f in audit["findings"] if f["name"] == "backup_script"), "WARNING")},
        {"item": "Monitoring", "status": next((f["status"] for f in audit["findings"] if f["name"] == "prometheus_config"), "WARNING")},
        {"item": "Terms", "status": "MANUAL"},
        {"item": "Privacy", "status": "MANUAL"},
    ]
    return {"success": True, "data": {"items": items, "score": audit["production_readiness_score"]}}, 200
