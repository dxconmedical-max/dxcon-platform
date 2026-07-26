"""Pilot Toolkit API routes — Phase 5 Sprint 5.13."""

from __future__ import annotations

from flask import Blueprint, current_app, request

from app.infrastructure.production_readiness import is_production
from app.services.pilot_toolkit_service import (
    dashboard_payload,
    demo_accounts,
    demo_data,
    pdf_toolkit,
    pilot_toolkit_readiness_report,
    postman_toolkit,
    qr_toolkit,
    reports_toolkit,
    swagger_toolkit,
    workflow_toolkit,
)

pilot_toolkit_bp = Blueprint(
    "pilot_toolkit_api",
    __name__,
    url_prefix="/api/v1/pilot-toolkit",
)


def _pilot_toolkit_allowed():
    if is_production(current_app) and not current_app.config.get("DEMO_MODE"):
        return False
    return True


def _deny():
    return {"error": "Pilot toolkit disabled in production"}, 403


@pilot_toolkit_bp.route("/dashboard", methods=["GET"])
def pilot_toolkit_dashboard_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return dashboard_payload()


@pilot_toolkit_bp.route("/demo-accounts", methods=["GET"])
def pilot_toolkit_demo_accounts_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return demo_accounts()


@pilot_toolkit_bp.route("/demo-data", methods=["GET"])
def pilot_toolkit_demo_data_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return demo_data()


@pilot_toolkit_bp.route("/postman", methods=["GET"])
def pilot_toolkit_postman_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return postman_toolkit()


@pilot_toolkit_bp.route("/swagger", methods=["GET"])
def pilot_toolkit_swagger_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return swagger_toolkit()


@pilot_toolkit_bp.route("/workflow", methods=["GET"])
def pilot_toolkit_workflow_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return workflow_toolkit()


@pilot_toolkit_bp.route("/pdf", methods=["GET"])
def pilot_toolkit_pdf_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    limit = min(max(int(request.args.get("limit", 10)), 1), 50)
    return pdf_toolkit(limit=limit)


@pilot_toolkit_bp.route("/qr", methods=["GET"])
def pilot_toolkit_qr_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    limit = min(max(int(request.args.get("limit", 10)), 1), 50)
    return qr_toolkit(limit=limit)


@pilot_toolkit_bp.route("/reports", methods=["GET"])
def pilot_toolkit_reports_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return reports_toolkit()


@pilot_toolkit_bp.route("/readiness", methods=["GET"])
def pilot_toolkit_readiness_api():
    if not _pilot_toolkit_allowed():
        return _deny()
    return pilot_toolkit_readiness_report()
