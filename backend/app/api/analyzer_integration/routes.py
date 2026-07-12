"""Analyzer Integration REST API — Release 7.0 Sprint 5."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.analyzer_integration.service import (
    AnalyzerIntegrationError,
    analyzer_dashboard,
    analyzer_health,
    create_test_mapping,
    create_worklist_item,
    get_analyzer,
    ingest_result_message,
    list_analyzers,
    list_messages,
    list_preliminary_results,
    list_quarantine,
    list_test_mappings,
    register_analyzer,
    send_worklist,
)
from app.extensions.db import db
from app.lab_workspace.auth import lab_api_admin, lab_api_read, lab_api_write

analyzers_bp = Blueprint("analyzer_registry", __name__, url_prefix="/api/v1/analyzers")
integrations_bp = Blueprint("analyzer_integrations", __name__, url_prefix="/api/v1/integrations/analyzer")
lab_analyzer_bp = Blueprint("lab_analyzer", __name__, url_prefix="/api/v1/lab")


def _org() -> str:
    return request.headers.get("X-Organization-ID") or session.get("organization_id") or "default-org"


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor")


@analyzers_bp.route("", methods=["GET"])
@lab_api_read
def analyzers_list():
    page = int(request.args.get("page", 1))
    return {"success": True, "data": list_analyzers(organization_id=_org(), page=page)}


@analyzers_bp.route("", methods=["POST"])
@lab_api_write
def analyzers_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = register_analyzer(data, organization_id=_org())
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except AnalyzerIntegrationError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@analyzers_bp.route("/<analyzer_id>", methods=["GET"])
@lab_api_read
def analyzers_get(analyzer_id):
    try:
        return {"success": True, "data": get_analyzer(analyzer_id, organization_id=_org())}
    except AnalyzerIntegrationError as exc:
        return {"error": str(exc)}, 404


@analyzers_bp.route("/<analyzer_id>/health", methods=["GET"])
@lab_api_read
def analyzers_health(analyzer_id):
    try:
        payload = analyzer_health(analyzer_id, organization_id=_org())
        db.session.commit()
        return {"success": True, "data": payload}
    except AnalyzerIntegrationError as exc:
        return {"error": str(exc)}, 404


@analyzers_bp.route("/<analyzer_id>/worklist", methods=["GET", "POST"])
@lab_api_write
def analyzers_worklist(analyzer_id):
    if request.method == "GET":
        from app.models.analyzer_integration import AnalyzerWorklistItem
        rows = AnalyzerWorklistItem.query.filter_by(organization_id=_org(), analyzer_id=analyzer_id).all()
        return {"success": True, "data": {"items": [r.to_dict() for r in rows]}}
    data = request.get_json(silent=True) or {}
    if data.get("action") == "send":
        try:
            payload = send_worklist(analyzer_id, organization_id=_org())
            db.session.commit()
            return {"success": True, "data": payload}
        except AnalyzerIntegrationError as exc:
            db.session.rollback()
            return {"error": str(exc)}, 400
    try:
        payload = create_worklist_item({**data, "analyzer_id": analyzer_id}, organization_id=_org())
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except AnalyzerIntegrationError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@integrations_bp.route("/messages", methods=["GET"])
@lab_api_read
def messages_list():
    return {"success": True, "data": list_messages(organization_id=_org(), status=request.args.get("status"))}


@integrations_bp.route("/results", methods=["POST"])
@lab_api_write
def results_ingest():
    data = request.get_json(silent=True) or {}
    analyzer_id = data.get("analyzer_id")
    if not analyzer_id:
        return {"error": "analyzer_id required"}, 400
    try:
        payload = ingest_result_message(
            data.get("payload") or data,
            organization_id=_org(),
            analyzer_id=analyzer_id,
            protocol=data.get("protocol", "SIMULATOR"),
        )
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except AnalyzerIntegrationError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@integrations_bp.route("/quarantine", methods=["GET"])
@lab_api_read
def quarantine_list():
    return {"success": True, "data": list_quarantine(organization_id=_org())}


@integrations_bp.route("/test-mappings", methods=["GET", "POST"])
@lab_api_read
def test_mappings():
    if request.method == "GET":
        return {"success": True, "data": list_test_mappings(organization_id=_org())}
    data = request.get_json(silent=True) or {}
    try:
        payload = create_test_mapping(data, organization_id=_org(), actor=_actor() or "system")
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except AnalyzerIntegrationError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@integrations_bp.route("/retries", methods=["POST"])
@lab_api_write
def retries():
    return {"success": True, "data": {"status": "retry_foundation", "note": "Manual retry queue not yet automated"}}


@lab_analyzer_bp.route("/analyzer-dashboard", methods=["GET"])
@lab_api_read
def lab_analyzer_dashboard():
    return {"success": True, "data": analyzer_dashboard(organization_id=_org())}


@lab_analyzer_bp.route("/result-review", methods=["GET"])
@lab_api_read
def lab_result_review():
    return {
        "success": True,
        "data": list_preliminary_results(organization_id=_org(), review_status=request.args.get("status", "PENDING_REVIEW")),
    }
