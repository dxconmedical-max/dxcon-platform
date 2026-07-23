"""Reception operational workspace REST API — Sprint 006."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.reception_workspace.auth import reception_api_read, reception_api_write
from app.reception_workspace.service import (
    ReceptionWorkspaceError,
    collect_payment,
    create_collection_after_payment,
    create_reception_order,
    fast_search_patients,
    generate_barcodes,
    get_patient_profile,
    payment_report,
    queue_report,
    reception_workspace_report,
    register_patient,
    render_request_form,
    search_tests,
    workspace_dashboard,
)

reception_workspace_bp = Blueprint("reception_workspace", __name__, url_prefix="/api/v1/reception/workspace")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor") or request.headers.get("X-User-Email")


@reception_workspace_bp.route("/dashboard", methods=["GET"])
@reception_api_read
def dashboard():
    return {"success": True, "data": workspace_dashboard()}, 200


@reception_workspace_bp.route("/search", methods=["GET"])
@reception_api_read
def search():
    result = fast_search_patients(
        request.args.get("q") or request.args.get("query") or "",
        limit=int(request.args.get("limit", request.args.get("per_page", 20))),
        page=int(request.args.get("page", 1)),
    )
    return {"success": True, **result}, 200


@reception_workspace_bp.route("/patients/register", methods=["POST"])
@reception_api_write
def patients_register():
    payload = request.get_json(silent=True) or {}
    try:
        result = register_patient(payload, actor=_actor(), force=bool(payload.get("force")))
        if result.get("duplicate") and not result.get("ok"):
            return {"success": False, "duplicate": True, "warnings": result.get("warnings", [])}, 409
        db.session.commit()
        return {"success": True, "data": result}, 201
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/patients/<patient_code>", methods=["GET"])
@reception_api_read
def patient_profile(patient_code: str):
    try:
        return {"success": True, "data": get_patient_profile(patient_code)}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/tests", methods=["GET"])
@reception_api_read
def tests_search():
    result = search_tests(
        query=request.args.get("q"),
        category=request.args.get("category"),
        department=request.args.get("department"),
        limit=int(request.args.get("limit", 50)),
        page=int(request.args.get("page", 1)),
    )
    return {"success": True, **result}, 200


@reception_workspace_bp.route("/orders", methods=["POST"])
@reception_api_write
def orders_create():
    payload = request.get_json(silent=True) or {}
    try:
        result = create_reception_order(
            patient_code=payload.get("patient_code", ""),
            test_catalog_ids=payload.get("test_catalog_ids") or payload.get("tests") or [],
            discount=float(payload.get("discount") or 0),
            note=payload.get("note"),
            queue_entry_id=payload.get("queue_entry_id"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 201
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>", methods=["GET"])
@reception_api_read
def orders_get(order_ref: str):
    """Milestone 1 — reopen/refresh persisted order (no payment/barcode)."""
    from app.business_engine import service as biz

    try:
        detail = biz.order_to_detail(order_ref)
        return {
            "success": True,
            "data": {
                "order": detail,
                "pricing": {
                    "subtotal": detail.get("subtotal") or 0,
                    "discount": detail.get("discount") or 0,
                    "total": detail.get("total_amount") or detail.get("total") or 0,
                },
            },
        }, 200
    except BusinessEngineError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/orders/<order_ref>/payment", methods=["POST"])
@reception_api_write
def orders_payment(order_ref: str):
    payload = request.get_json(silent=True) or {}
    try:
        result = collect_payment(
            order_ref,
            payment_method=payload.get("payment_method", "cash"),
            receipt_number=payload.get("receipt_number"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 200
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/collection", methods=["POST"])
@reception_api_write
def orders_collection(order_ref: str):
    payload = request.get_json(silent=True) or {}
    try:
        result = create_collection_after_payment(
            order_ref,
            collector_name=payload.get("collector_name", "Walk-in Collector"),
            pickup_address=payload.get("pickup_address", "Reception Desk"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": result}, 201
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@reception_workspace_bp.route("/orders/<order_ref>/barcode", methods=["GET"])
@reception_api_read
def orders_barcode(order_ref: str):
    try:
        return {"success": True, "data": generate_barcodes(order_ref)}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/orders/<order_ref>/request-form", methods=["GET"])
@reception_api_read
def orders_request_form(order_ref: str):
    try:
        html = render_request_form(order_ref)
        return {"success": True, "data": {"html": html}}, 200
    except ReceptionWorkspaceError as exc:
        return {"success": False, "error": str(exc)}, 404


@reception_workspace_bp.route("/queue", methods=["GET"])
@reception_api_read
def queue():
    dash = workspace_dashboard()
    return {"success": True, "data": dash.get("workflow_queue", []), "kpis": dash.get("kpis", {})}, 200


@reception_workspace_bp.route("/report", methods=["GET"])
@reception_api_read
def report():
    return {"success": True, "data": reception_workspace_report()}, 200


@reception_workspace_bp.route("/payment-report", methods=["GET"])
@reception_api_read
def payment_report_route():
    return {"success": True, "data": payment_report()}, 200


@reception_workspace_bp.route("/queue-report", methods=["GET"])
@reception_api_read
def queue_report_route():
    return {"success": True, "data": queue_report()}, 200
