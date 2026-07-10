"""Operations Center API — Release 1.0 Operations Excellence."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.extensions.db import db
from app.operations_center.auth import ops_center_api_read, ops_center_api_write
from app.operations_center.service import (
    OpsCenterError,
    create_customer_request,
    create_support_ticket,
    dashboard,
    list_customer_requests,
    list_support_tickets,
    operations_center_report,
    update_customer_request_status,
    update_support_ticket_status,
)

operations_center_bp = Blueprint(
    "operations_center", __name__, url_prefix="/api/v1/operations-center"
)


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor")


@operations_center_bp.route("/dashboard", methods=["GET"])
@ops_center_api_read
def api_dashboard():
    return {"success": True, "data": dashboard()}, 200


@operations_center_bp.route("/report", methods=["GET"])
@ops_center_api_read
def api_report():
    return {"success": True, "data": operations_center_report()}, 200


@operations_center_bp.route("/support-tickets", methods=["GET"])
@ops_center_api_read
def api_list_tickets():
    return {"success": True, "data": list_support_tickets(status=request.args.get("status"))}, 200


@operations_center_bp.route("/support-tickets", methods=["POST"])
@ops_center_api_write
def api_create_ticket():
    try:
        data = create_support_ticket(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except OpsCenterError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@operations_center_bp.route("/support-tickets/<ticket_code>/status", methods=["POST"])
@ops_center_api_write
def api_update_ticket(ticket_code: str):
    try:
        payload = request.get_json(silent=True) or {}
        data = update_support_ticket_status(ticket_code, payload.get("status", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except OpsCenterError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@operations_center_bp.route("/customer-requests", methods=["GET"])
@ops_center_api_read
def api_list_requests():
    return {"success": True, "data": list_customer_requests(status=request.args.get("status"))}, 200


@operations_center_bp.route("/customer-requests", methods=["POST"])
@ops_center_api_write
def api_create_request():
    try:
        data = create_customer_request(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except OpsCenterError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@operations_center_bp.route("/customer-requests/<request_code>/status", methods=["POST"])
@ops_center_api_write
def api_update_request(request_code: str):
    try:
        payload = request.get_json(silent=True) or {}
        data = update_customer_request_status(request_code, payload.get("status", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except OpsCenterError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400
