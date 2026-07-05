"""Readiness Pack API routes — Phase 5 Sprint 5.14."""

from __future__ import annotations

from flask import Blueprint

from app.services.readiness_pack_service import (
    dashboard_payload,
    go_live_checklist_report,
    known_limitations_doc,
    pilot_readiness_report,
    readiness_pack_inventory,
    readiness_pack_readiness_report,
    roadmap_v2_doc,
    security_readiness_report,
    system_readiness_report,
)

readiness_pack_bp = Blueprint(
    "readiness_pack_api",
    __name__,
    url_prefix="/api/v1/readiness-pack",
)


@readiness_pack_bp.route("/dashboard", methods=["GET"])
def readiness_pack_dashboard_api():
    return dashboard_payload()


@readiness_pack_bp.route("/system", methods=["GET"])
def readiness_pack_system_api():
    return system_readiness_report()


@readiness_pack_bp.route("/security", methods=["GET"])
def readiness_pack_security_api():
    return security_readiness_report()


@readiness_pack_bp.route("/pilot", methods=["GET"])
def readiness_pack_pilot_api():
    return pilot_readiness_report()


@readiness_pack_bp.route("/go-live-checklist", methods=["GET"])
def readiness_pack_go_live_checklist_api():
    return go_live_checklist_report()


@readiness_pack_bp.route("/limitations", methods=["GET"])
def readiness_pack_limitations_api():
    return known_limitations_doc()


@readiness_pack_bp.route("/roadmap", methods=["GET"])
def readiness_pack_roadmap_api():
    return roadmap_v2_doc()


@readiness_pack_bp.route("/inventory", methods=["GET"])
def readiness_pack_inventory_api():
    return readiness_pack_inventory()


@readiness_pack_bp.route("/readiness", methods=["GET"])
def readiness_pack_readiness_api():
    return readiness_pack_readiness_report()
