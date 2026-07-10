"""Integration platform REST API — Epic 3.5."""

from __future__ import annotations

from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required

from app.integration.audit import write_integration_audit
from app.integration.mappings.engine import preview_mapping, upsert_mapping_rule
from app.integration.parsers.fhir_foundation import map_fhir_resource
from app.integration.parsers.hl7_foundation import parse_hl7_message
from app.integration.security import enforce_organization_access, require_integration_permission
from app.integration.service import (
    IntegrationError,
    create_api_credential,
    get_connector,
    ignore_message,
    import_csv_via_connector,
    import_json_via_connector,
    integration_health,
    list_connectors,
    list_exceptions,
    list_messages,
    receive_message,
    retry_message,
    revoke_api_credential,
    set_connector_status,
    test_connection,
    upsert_connector,
)
from app.integration.webhooks.engine import create_subscription, queue_delivery, simulate_delivery
from app.extensions.db import db
from app.integration.models import IntgDeliveryAttempt, IntgWebhookSubscription
from app.models.user import User
from app.partner_foundation.service import ensure_default_organization

integration_platform_bp = Blueprint("integration_platform", __name__, url_prefix="/api/v1/integration")


def _actor() -> str:
    return getattr(g, "user_email", None) or request.headers.get("X-User-Email") or "api"


def _org_id(user: User) -> str:
    org = request.args.get("organization_id") or user.organization_id
    if not org:
        org = ensure_default_organization().id
    return org


@integration_platform_bp.route("/connectors", methods=["GET"])
@jwt_required()
def api_list_connectors():
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    org_id = _org_id(user)
    if not enforce_organization_access(user, org_id):
        return {"error": "Forbidden"}, 403
    page = int(request.args.get("page", 1))
    return {"success": True, "data": list_connectors(organization_id=org_id, page=page)}, 200


@integration_platform_bp.route("/connectors", methods=["POST"])
@jwt_required()
def api_create_connector():
    user, err = require_integration_permission("CONNECTOR_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = upsert_connector(request.get_json(silent=True) or {}, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 201


@integration_platform_bp.route("/connectors/<connector_id>", methods=["GET"])
@jwt_required()
def api_get_connector(connector_id: str):
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = get_connector(connector_id, organization_id=org_id)
    except IntegrationError as exc:
        return {"error": str(exc)}, 404
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/connectors/<connector_id>/status", methods=["POST"])
@jwt_required()
def api_connector_status(connector_id: str):
    user, err = require_integration_permission("CONNECTOR_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    status = (request.get_json(silent=True) or {}).get("status", "ACTIVE")
    try:
        data = set_connector_status(connector_id, status, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/connectors/<connector_id>/test", methods=["POST"])
@jwt_required()
def api_test_connector(connector_id: str):
    user, err = require_integration_permission("CONNECTOR_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = test_connection(connector_id, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/connectors/<connector_id>/import/csv", methods=["POST"])
@jwt_required()
def api_import_csv(connector_id: str):
    user, err = require_integration_permission("INTEGRATION_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    file = request.files.get("file")
    if not file:
        return {"error": "file required"}, 400
    try:
        data = import_csv_via_connector(connector_id, file.read(), organization_id=org_id, actor=_actor(), file_name=file.filename or "import.csv")
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/connectors/<connector_id>/import/json", methods=["POST"])
@jwt_required()
def api_import_json(connector_id: str):
    user, err = require_integration_permission("INTEGRATION_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = import_json_via_connector(connector_id, request.get_json(silent=True) or {}, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/messages", methods=["GET"])
@jwt_required()
def api_list_messages():
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    org_id = _org_id(user)
    return {"success": True, "data": list_messages(organization_id=org_id, status=request.args.get("status"))}, 200


@integration_platform_bp.route("/exceptions", methods=["GET"])
@jwt_required()
def api_list_exceptions():
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    org_id = _org_id(user)
    return {"success": True, "data": list_exceptions(organization_id=org_id)}, 200


@integration_platform_bp.route("/messages/<message_id>/retry", methods=["POST"])
@jwt_required()
def api_retry_message(message_id: str):
    user, err = require_integration_permission("MESSAGE_RETRY")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = retry_message(message_id, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/messages/<message_id>/ignore", methods=["POST"])
@jwt_required()
def api_ignore_message(message_id: str):
    user, err = require_integration_permission("MESSAGE_RETRY")
    if err:
        return err
    org_id = _org_id(user)
    reason = (request.get_json(silent=True) or {}).get("reason", "manual ignore")
    try:
        data = ignore_message(message_id, reason, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/mappings", methods=["POST"])
@jwt_required()
def api_upsert_mapping():
    user, err = require_integration_permission("MAPPING_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = upsert_mapping_rule(request.get_json(silent=True) or {}, organization_id=org_id)
        write_integration_audit(action="mapping_updated", actor=_actor(), organization_id=org_id)
        db.session.commit()
    except ValueError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 200


@integration_platform_bp.route("/mappings/preview", methods=["POST"])
@jwt_required()
def api_mapping_preview():
    user, err = require_integration_permission("MAPPING_MANAGE")
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    connector_id = payload.get("connector_id")
    sample = payload.get("sample") or {}
    if not connector_id:
        return {"error": "connector_id required"}, 400
    return {"success": True, "data": preview_mapping(connector_id, sample)}, 200


@integration_platform_bp.route("/webhooks", methods=["POST"])
@jwt_required()
def api_create_webhook():
    user, err = require_integration_permission("WEBHOOK_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = create_subscription(request.get_json(silent=True) or {}, organization_id=org_id, actor=_actor())
        db.session.commit()
    except ValueError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 201


@integration_platform_bp.route("/webhooks/<subscription_id>/deliveries", methods=["GET"])
@jwt_required()
def api_webhook_deliveries(subscription_id: str):
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    org_id = _org_id(user)
    rows = IntgDeliveryAttempt.query.filter_by(subscription_id=subscription_id, organization_id=org_id).limit(50).all()
    return {"success": True, "data": [r.to_dict() for r in rows]}, 200


@integration_platform_bp.route("/credentials", methods=["POST"])
@jwt_required()
def api_create_credential():
    user, err = require_integration_permission("API_CREDENTIAL_MANAGE")
    if err:
        return err
    org_id = _org_id(user)
    try:
        data = create_api_credential(request.get_json(silent=True) or {}, organization_id=org_id, actor=_actor())
        db.session.commit()
    except IntegrationError as exc:
        return {"error": str(exc)}, 400
    return {"success": True, "data": data}, 201


@integration_platform_bp.route("/health", methods=["GET"])
@jwt_required()
def api_integration_health():
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    org_id = _org_id(user)
    return {"success": True, "data": integration_health(organization_id=org_id)}, 200


@integration_platform_bp.route("/hl7/parse", methods=["POST"])
@jwt_required()
def api_hl7_parse():
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    raw = (request.get_json(silent=True) or {}).get("message", "")
    return {"success": True, "data": parse_hl7_message(raw)}, 200


@integration_platform_bp.route("/fhir/map", methods=["POST"])
@jwt_required()
def api_fhir_map():
    user, err = require_integration_permission("INTEGRATION_VIEW")
    if err:
        return err
    resource = (request.get_json(silent=True) or {}).get("resource") or {}
    return {"success": True, "data": map_fhir_resource(resource)}, 200
