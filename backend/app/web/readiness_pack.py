"""Readiness Pack web routes — Phase 5 Sprint 5.14."""

from __future__ import annotations

from flask import Blueprint

from app.services.readiness_pack_service import READINESS_PACK_ROLES
from app.utils.auth import role_required
from app.web.readiness_pack_lib import (
    build_dashboard_body,
    build_go_live_checklist_body,
    build_limitations_body,
    build_pilot_body,
    build_roadmap_body,
    build_security_body,
    build_system_body,
    render_pack_page,
)

readiness_pack_web_bp = Blueprint("readiness_pack_web", __name__)


@readiness_pack_web_bp.route("/readiness-pack")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_dashboard():
    return render_pack_page("Readiness Pack", build_dashboard_body())


@readiness_pack_web_bp.route("/readiness-pack/system")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_system():
    return render_pack_page("System Readiness", build_system_body())


@readiness_pack_web_bp.route("/readiness-pack/security")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_security():
    return render_pack_page("Security Readiness", build_security_body())


@readiness_pack_web_bp.route("/readiness-pack/pilot")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_pilot():
    return render_pack_page("Pilot Readiness", build_pilot_body())


@readiness_pack_web_bp.route("/readiness-pack/go-live-checklist")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_go_live_checklist():
    return render_pack_page("Go-Live Checklist", build_go_live_checklist_body())


@readiness_pack_web_bp.route("/readiness-pack/limitations")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_limitations():
    return render_pack_page("Known Limitations", build_limitations_body())


@readiness_pack_web_bp.route("/readiness-pack/roadmap")
@role_required(*READINESS_PACK_ROLES)
def readiness_pack_roadmap():
    return render_pack_page("Roadmap v2", build_roadmap_body())
