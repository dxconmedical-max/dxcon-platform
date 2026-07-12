"""Clinical governance REST API — Release 8.0 Sprint 6."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.clinical_governance.service import (
    ClinicalGovernanceError,
    acknowledge_critical,
    create_critical_policy,
    get_result_item,
    promote_preliminary_to_result,
    reject_result_item,
    release_report_governed,
    request_rerun,
    technician_queue,
    validate_result_item,
    verify_report_token,
)
from app.clinical_governance import service as clinical
from app.extensions.db import db
from app.lab_workspace.auth import lab_api_read, lab_api_write
from app.reporting_engine.auth import report_api_approve, report_api_read, report_api_release

clinical_bp = Blueprint("clinical_governance", __name__, url_prefix="/api/v1/clinical")
verify_bp = Blueprint("report_verify", __name__, url_prefix="/api/v1/verify-report")


def _org() -> str:
    return request.headers.get("X-Organization-ID") or session.get("organization_id") or "default-org"


def _actor() -> str:
    return session.get("email") or request.headers.get("X-Actor") or "system"


@clinical_bp.route("/technician/queue", methods=["GET"])
@lab_api_read
def technician_queue_api():
    return {"success": True, "data": technician_queue(organization_id=_org())}


@clinical_bp.route("/technician/results/<item_id>", methods=["GET"])
@lab_api_read
def technician_result_detail(item_id):
    try:
        return {"success": True, "data": get_result_item(item_id, organization_id=_org())}
    except ClinicalGovernanceError as exc:
        return {"error": str(exc)}, 404


@clinical_bp.route("/technician/results/<item_id>/validate", methods=["POST"])
@lab_api_write
def technician_validate(item_id):
    data = request.get_json(silent=True) or {}
    try:
        payload = validate_result_item(item_id, organization_id=_org(), actor=_actor(), note=data.get("note"))
        db.session.commit()
        return {"success": True, "data": payload}
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/technician/results/<item_id>/reject", methods=["POST"])
@lab_api_write
def technician_reject(item_id):
    data = request.get_json(silent=True) or {}
    try:
        payload = reject_result_item(item_id, organization_id=_org(), actor=_actor(), reason=data.get("reason", "rejected"))
        db.session.commit()
        return {"success": True, "data": payload}
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/technician/results/<item_id>/rerun", methods=["POST"])
@lab_api_write
def technician_rerun(item_id):
    data = request.get_json(silent=True) or {}
    try:
        payload = request_rerun(item_id, organization_id=_org(), actor=_actor(), reason=data.get("reason", "rerun"))
        db.session.commit()
        return {"success": True, "data": payload}
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/technician/promote", methods=["POST"])
@lab_api_write
def technician_promote():
    data = request.get_json(silent=True) or {}
    try:
        payload = promote_preliminary_to_result(
            data["preliminary_id"],
            organization_id=_org(),
            order_id=data["order_id"],
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/doctor/queue", methods=["GET"])
@report_api_read
def doctor_queue_api():
    return {"success": True, "data": clinical.doctor_queue(
        patient=request.args.get("patient"),
        order_code=request.args.get("order_code"),
        page=int(request.args.get("page", 1)),
    )}


@clinical_bp.route("/release/<order_ref>", methods=["POST"])
@report_api_release
def governed_release(order_ref):
    try:
        payload = release_report_governed(order_ref, organization_id=_org(), actor=_actor())
        db.session.commit()
        return {"success": True, "data": payload}
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/critical/policies", methods=["POST"])
@lab_api_write
def critical_policy_create():
    data = request.get_json(silent=True) or {}
    try:
        payload = create_critical_policy(data, organization_id=_org(), actor=_actor())
        db.session.commit()
        return {"success": True, "data": payload}, 201
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/critical/<alert_id>/acknowledge", methods=["POST"])
@lab_api_write
def critical_ack(alert_id):
    data = request.get_json(silent=True) or {}
    try:
        payload = acknowledge_critical(alert_id, organization_id=_org(), actor=_actor(), method=data.get("method", "in_app"))
        db.session.commit()
        return {"success": True, "data": payload}
    except ClinicalGovernanceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@clinical_bp.route("/timeline/<aggregate_type>/<aggregate_id>", methods=["GET"])
@lab_api_read
def audit_timeline(aggregate_type, aggregate_id):
    from app.clinical_governance.workflow import timeline
    return {"success": True, "data": timeline(organization_id=_org(), aggregate_type=aggregate_type, aggregate_id=aggregate_id)}


@verify_bp.route("/<token>", methods=["GET"])
def verify_report(token):
    return {"success": True, "data": verify_report_token(token)}
