"""Integration Hub API routes — Phase 4 Sprint 4.1."""

from flask import Blueprint, request, session

from app.services.integration_hub_service import (
    IntegrationHubError,
    dashboard_payload,
    hub_health,
    list_adapters,
    list_api_keys,
    list_audit,
    list_connectors,
    list_dead_letters,
    list_retry_queue,
    list_webhooks,
    sandbox_test,
)

integration_hub_bp = Blueprint("integration_hub_api", __name__, url_prefix="/api/v1/integration-hub")


@integration_hub_bp.route("/dashboard", methods=["GET"])
def integration_hub_dashboard_api():
    return dashboard_payload()


@integration_hub_bp.route("/health", methods=["GET"])
def integration_hub_health_api():
    return hub_health()


@integration_hub_bp.route("/connectors", methods=["GET"])
def integration_hub_connectors_api():
    return list_connectors()


@integration_hub_bp.route("/adapters", methods=["GET"])
def integration_hub_adapters_api():
    return list_adapters()


@integration_hub_bp.route("/webhooks", methods=["GET"])
def integration_hub_webhooks_api():
    return list_webhooks()


@integration_hub_bp.route("/api-keys", methods=["GET"])
def integration_hub_api_keys_api():
    return list_api_keys()


@integration_hub_bp.route("/retry-queue", methods=["GET"])
def integration_hub_retry_queue_api():
    return list_retry_queue()


@integration_hub_bp.route("/dead-letters", methods=["GET"])
def integration_hub_dead_letters_api():
    return list_dead_letters()


@integration_hub_bp.route("/audit", methods=["GET"])
def integration_hub_audit_api():
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 50)
    return list_audit(page=page, page_size=page_size)


@integration_hub_bp.route("/sandbox/test", methods=["POST"])
def integration_hub_sandbox_test_api():
    data = request.get_json(silent=True) or {}
    try:
        return sandbox_test(
            data.get("adapter_type", "HIS"),
            data.get("payload"),
            actor=session.get("email"),
        )
    except IntegrationHubError as exc:
        return {"error": exc.message}, exc.status_code
