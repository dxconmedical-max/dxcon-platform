"""Executive platform REST API — Sprint 010."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.executive_platform.auth import audit_api_read, crm_api_read, executive_api_read, finance_api_read, monitoring_api_read, pilot_api_read
from app.executive_platform.service import (
    ExecutivePlatformError,
    admin_settings,
    audit_center,
    backup_dashboard,
    crm_dashboard,
    crm_report,
    deployment_report,
    executive_dashboard,
    executive_report,
    finance_dashboard,
    finance_report,
    launch_checklist,
    operational_monitoring,
    pilot_ready_report,
    pilot_wizard,
    release_1_complete,
    security_report,
    verify_checklist_item,
)
from app.extensions.db import db

executive_platform_bp = Blueprint("executive_platform", __name__, url_prefix="/api/v1/executive-platform")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor")


@executive_platform_bp.route("/dashboard", methods=["GET"])
@executive_api_read
def api_dashboard():
    return {"success": True, "data": executive_dashboard()}, 200


@executive_platform_bp.route("/crm", methods=["GET"])
@crm_api_read
def api_crm():
    return {"success": True, "data": crm_dashboard()}, 200


@executive_platform_bp.route("/finance", methods=["GET"])
@finance_api_read
def api_finance():
    return {"success": True, "data": finance_dashboard()}, 200


@executive_platform_bp.route("/monitoring", methods=["GET"])
@monitoring_api_read
def api_monitoring():
    return {"success": True, "data": operational_monitoring()}, 200


@executive_platform_bp.route("/audit", methods=["GET"])
@audit_api_read
def api_audit():
    return {"success": True, **audit_center(
        q=request.args.get("q"),
        user=request.args.get("user"),
        page=int(request.args.get("page", 1)),
        per_page=int(request.args.get("per_page", 50)),
    )}, 200


@executive_platform_bp.route("/admin/settings", methods=["GET"])
@executive_api_read
def api_admin():
    return {"success": True, "data": admin_settings()}, 200


@executive_platform_bp.route("/backup", methods=["GET"])
@executive_api_read
def api_backup():
    return {"success": True, "data": backup_dashboard()}, 200


@executive_platform_bp.route("/security", methods=["GET"])
@executive_api_read
def api_security():
    return {"success": True, "data": security_report()}, 200


@executive_platform_bp.route("/pilot/wizard", methods=["GET", "POST"])
@pilot_api_read
def api_pilot_wizard():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        data = pilot_wizard(organization_name=payload.get("organization_name"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    return {"success": True, "data": pilot_wizard(actor=_actor())}, 200


@executive_platform_bp.route("/launch-checklist", methods=["GET"])
@executive_api_read
def api_launch_checklist():
    return {"success": True, "data": launch_checklist(actor=_actor())}, 200


@executive_platform_bp.route("/launch-checklist/<item_key>/verify", methods=["POST"])
@executive_api_read
def api_verify_checklist(item_key: str):
    try:
        data = verify_checklist_item(item_key, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except ExecutivePlatformError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@executive_platform_bp.route("/report/executive", methods=["GET"])
@executive_api_read
def api_executive_report():
    return {"success": True, "data": executive_report()}, 200


@executive_platform_bp.route("/report/crm", methods=["GET"])
@crm_api_read
def api_crm_report():
    return {"success": True, "data": crm_report()}, 200


@executive_platform_bp.route("/report/finance", methods=["GET"])
@finance_api_read
def api_finance_report():
    return {"success": True, "data": finance_report()}, 200


@executive_platform_bp.route("/report/deployment", methods=["GET"])
@executive_api_read
def api_deployment_report():
    return {"success": True, "data": deployment_report()}, 200


@executive_platform_bp.route("/report/pilot-ready", methods=["GET"])
@executive_api_read
def api_pilot_ready():
    return {"success": True, "data": pilot_ready_report()}, 200


@executive_platform_bp.route("/report/release-1", methods=["GET"])
@executive_api_read
def api_release_1():
    return {"success": True, "data": release_1_complete()}, 200
