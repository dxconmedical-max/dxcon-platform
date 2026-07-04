"""User Guides API routes — Phase 5 Sprint 5.8."""

from __future__ import annotations

from flask import Blueprint

from app.services.user_guides_service import (
    admin_guide,
    collector_guide,
    dashboard_payload,
    doctor_guide,
    lab_guide,
    reception_guide,
    user_guides_checklist,
    user_guides_dashboard,
    user_guides_faq,
    user_guides_readiness_report,
    video_links,
)

user_guides_bp = Blueprint(
    "user_guides_api",
    __name__,
    url_prefix="/api/v1/user-guides",
)


@user_guides_bp.route("/dashboard", methods=["GET"])
def user_guides_dashboard_api():
    return dashboard_payload()


@user_guides_bp.route("/reception", methods=["GET"])
def user_guides_reception_api():
    return reception_guide()


@user_guides_bp.route("/collector", methods=["GET"])
def user_guides_collector_api():
    return collector_guide()


@user_guides_bp.route("/lab", methods=["GET"])
def user_guides_lab_api():
    return lab_guide()


@user_guides_bp.route("/doctor", methods=["GET"])
def user_guides_doctor_api():
    return doctor_guide()


@user_guides_bp.route("/admin", methods=["GET"])
def user_guides_admin_api():
    return admin_guide()


@user_guides_bp.route("/video", methods=["GET"])
def user_guides_video_api():
    return video_links()


@user_guides_bp.route("/faq", methods=["GET"])
def user_guides_faq_api():
    return user_guides_faq()


@user_guides_bp.route("/checklist", methods=["GET"])
def user_guides_checklist_api():
    return user_guides_checklist()


@user_guides_bp.route("/inventory", methods=["GET"])
def user_guides_inventory_api():
    return user_guides_dashboard()


@user_guides_bp.route("/readiness", methods=["GET"])
def user_guides_readiness_api():
    return user_guides_readiness_report()
