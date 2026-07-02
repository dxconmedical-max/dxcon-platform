from flask import Blueprint, request

from app.integrations.audit_trail import IntegrationAuditTrail
from app.integrations.sandbox_tokens import SandboxTokenService
from app.services.integration_service import (
    HISPatientService,
    IntegrationError,
    IntegrationGatewayService,
    IntegrationMessageRouter,
    LISOrderService,
    LISResultService,
)


integrations_bp = Blueprint(
    "integrations",
    __name__,
    url_prefix="/api/v1/integrations",
)


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


def _connection_id(data):
    return data.get("connection_id") or request.args.get("connection_id")


@integrations_bp.route("/connections", methods=["GET"])
def list_connections():
    payload = IntegrationGatewayService.list_connections(
        partner_id=request.args.get("partner_id"),
        status=request.args.get("status"),
    )
    return payload


@integrations_bp.route("/connections", methods=["POST"])
def create_connection():
    data = request.get_json(silent=True) or {}
    try:
        connection = IntegrationGatewayService.create_connection(data, actor_email=_actor_email())
    except IntegrationError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Connection created", "connection": connection.to_dict()}, 201


@integrations_bp.route("/lis/orders", methods=["POST"])
def lis_orders():
    data = request.get_json(silent=True) or {}
    connection_id = _connection_id(data)
    if not connection_id:
        return {"error": "connection_id is required"}, 400
    try:
        payload = LISOrderService.process_order(connection_id, data, actor_email=_actor_email())
    except IntegrationError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "LIS order processed", **payload}, 201


@integrations_bp.route("/lis/results", methods=["POST"])
def lis_results():
    data = request.get_json(silent=True) or {}
    connection_id = _connection_id(data)
    if not connection_id:
        return {"error": "connection_id is required"}, 400
    try:
        payload = LISResultService.process_result(connection_id, data, actor_email=_actor_email())
    except IntegrationError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "LIS result processed", **payload}, 201


@integrations_bp.route("/his/patients", methods=["POST"])
def his_patients():
    data = request.get_json(silent=True) or {}
    connection_id = _connection_id(data)
    if not connection_id:
        return {"error": "connection_id is required"}, 400
    try:
        payload = HISPatientService.process_patient(connection_id, data, actor_email=_actor_email())
    except IntegrationError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "HIS patient processed", **payload}, 201


@integrations_bp.route("/messages", methods=["GET"])
def list_messages():
    payload = IntegrationGatewayService.list_messages(
        connection_id=request.args.get("connection_id"),
        message_type=request.args.get("message_type"),
    )
    return payload


@integrations_bp.route("/audit", methods=["GET"])
def list_audit():
    if request.args.get("scope") == "platform":
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 50)), 1), 200)
        return IntegrationAuditTrail.list_entries(
            action=request.args.get("action"),
            resource_type=request.args.get("resource_type"),
            page=page,
            page_size=page_size,
        )
    payload = IntegrationGatewayService.list_audit(connection_id=request.args.get("connection_id"))
    return payload


@integrations_bp.route("/sandbox-token", methods=["POST"])
def issue_sandbox_token():
    data = request.get_json(silent=True) or {}
    partner_id = data.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    return SandboxTokenService.issue(
        partner_id=partner_id,
        scopes=data.get("scopes"),
        ttl_seconds=data.get("ttl_seconds"),
    ), 201
