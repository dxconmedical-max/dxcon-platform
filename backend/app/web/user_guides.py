"""User Guides web routes — Phase 5 Sprint 5.8."""

from __future__ import annotations

from flask import Blueprint

from app.services.user_guides_service import USER_GUIDES_ROLES
from app.utils.auth import role_required
from app.web.user_guides_lib import (
    build_admin_body,
    build_checklist_body,
    build_collector_body,
    build_dashboard_body,
    build_doctor_body,
    build_faq_body,
    build_lab_body,
    build_reception_body,
    build_video_body,
    render_guides_page,
)

user_guides_web_bp = Blueprint("user_guides_web", __name__)


@user_guides_web_bp.route("/user-guides")
@role_required(*USER_GUIDES_ROLES)
def user_guides_dashboard():
    return render_guides_page("User Guides", build_dashboard_body())


@user_guides_web_bp.route("/user-guides/reception")
@role_required(*USER_GUIDES_ROLES)
def user_guides_reception():
    return render_guides_page("Reception Guide", build_reception_body())


@user_guides_web_bp.route("/user-guides/collector")
@role_required(*USER_GUIDES_ROLES)
def user_guides_collector():
    return render_guides_page("Collector Guide", build_collector_body())


@user_guides_web_bp.route("/user-guides/lab")
@role_required(*USER_GUIDES_ROLES)
def user_guides_lab():
    return render_guides_page("Lab Guide", build_lab_body())


@user_guides_web_bp.route("/user-guides/doctor")
@role_required(*USER_GUIDES_ROLES)
def user_guides_doctor():
    return render_guides_page("Doctor Guide", build_doctor_body())


@user_guides_web_bp.route("/user-guides/admin")
@role_required(*USER_GUIDES_ROLES)
def user_guides_admin():
    return render_guides_page("Admin Guide", build_admin_body())


@user_guides_web_bp.route("/user-guides/video")
@role_required(*USER_GUIDES_ROLES)
def user_guides_video():
    return render_guides_page("Video Link", build_video_body())


@user_guides_web_bp.route("/user-guides/faq")
@role_required(*USER_GUIDES_ROLES)
def user_guides_faq_page():
    return render_guides_page("FAQ", build_faq_body())


@user_guides_web_bp.route("/user-guides/checklist")
@role_required(*USER_GUIDES_ROLES)
def user_guides_checklist_page():
    return render_guides_page("Checklist", build_checklist_body())
