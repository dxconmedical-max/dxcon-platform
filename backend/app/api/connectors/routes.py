from flask import Blueprint, request

from app.integrations.connector_health import ConnectorHealthService
from app.integrations.connector_registry import ConnectorRegistry
from app.services.integration_platform_service import IntegrationError


connectors_bp = Blueprint("connectors", __name__, url_prefix="/api/v1/connectors")


def _error(message, status_code=400):
    return {"error": message}, status_code


@connectors_bp.route("", methods=["GET"])
def list_connectors():
    return ConnectorRegistry.list_connectors()


@connectors_bp.route("", methods=["POST"])
def register_connector():
    data = request.get_json(silent=True) or {}
    try:
        return ConnectorRegistry.register(data), 201
    except ValueError as exc:
        return _error(str(exc), 400)


@connectors_bp.route("/<connector_id>/health", methods=["GET"])
def connector_health(connector_id):
    try:
        return ConnectorHealthService.check(connector_id)
    except KeyError:
        return _error("Connector not found", 404)
