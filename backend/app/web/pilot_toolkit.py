"""Pilot Toolkit web routes — Phase 5 Sprint 5.13."""

from __future__ import annotations

from flask import Blueprint

from app.services.pilot_toolkit_service import PILOT_TOOLKIT_ROLES
from app.utils.auth import role_required
from app.web.pilot_toolkit_lib import (
    build_dashboard_body,
    build_demo_accounts_body,
    build_demo_data_body,
    build_pdf_body,
    build_postman_body,
    build_qr_body,
    build_reports_body,
    build_swagger_body,
    build_workflow_body,
    render_toolkit_page,
)

pilot_toolkit_web_bp = Blueprint("pilot_toolkit_web", __name__)


@pilot_toolkit_web_bp.route("/pilot-toolkit")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_dashboard():
    return render_toolkit_page("Pilot Toolkit", build_dashboard_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/demo-accounts")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_demo_accounts():
    return render_toolkit_page("Demo Accounts", build_demo_accounts_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/demo-data")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_demo_data():
    return render_toolkit_page("Demo Data", build_demo_data_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/postman")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_postman():
    return render_toolkit_page("Postman", build_postman_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/swagger")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_swagger():
    return render_toolkit_page("Swagger", build_swagger_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/workflow")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_workflow():
    return render_toolkit_page("Workflow", build_workflow_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/pdf")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_pdf():
    return render_toolkit_page("PDF", build_pdf_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/qr")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_qr():
    return render_toolkit_page("QR", build_qr_body())


@pilot_toolkit_web_bp.route("/pilot-toolkit/reports")
@role_required(*PILOT_TOOLKIT_ROLES)
def pilot_toolkit_reports():
    return render_toolkit_page("Reports", build_reports_body())
