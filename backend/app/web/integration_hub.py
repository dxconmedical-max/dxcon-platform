"""Integration Hub web routes — Phase 4 Sprint 4.1."""

from __future__ import annotations

import json

from flask import Blueprint, request, session

from app.services.integration_hub_service import HUB_ROLES, IntegrationHubError, sandbox_test
from app.utils.auth import role_required
from app.web.integration_hub_lib import (
    build_adapters_body,
    build_api_keys_body,
    build_audit_body,
    build_connectors_body,
    build_dashboard_body,
    build_dead_letters_body,
    build_retry_queue_body,
    build_sandbox_body,
    build_webhooks_body,
    render_hub_page,
)

integration_hub_web_bp = Blueprint("integration_hub_web", __name__)


def _actor() -> str | None:
    return session.get("email")


@integration_hub_web_bp.route("/integration-hub")
@role_required(*HUB_ROLES)
def integration_hub_dashboard():
    message = request.args.get("message", "")
    error = request.args.get("error", "")
    return render_hub_page("Integration Center", build_dashboard_body(message=message, error=error))


@integration_hub_web_bp.route("/integration-hub/connectors")
@role_required(*HUB_ROLES)
def integration_hub_connectors():
    return render_hub_page("Connector Registry", build_connectors_body())


@integration_hub_web_bp.route("/integration-hub/adapters")
@role_required(*HUB_ROLES)
def integration_hub_adapters():
    return render_hub_page("Adapters", build_adapters_body())


@integration_hub_web_bp.route("/integration-hub/webhooks")
@role_required(*HUB_ROLES)
def integration_hub_webhooks():
    return render_hub_page("Webhook Manager", build_webhooks_body())


@integration_hub_web_bp.route("/integration-hub/api-keys")
@role_required(*HUB_ROLES)
def integration_hub_api_keys():
    return render_hub_page("API Key Manager", build_api_keys_body())


@integration_hub_web_bp.route("/integration-hub/retry-queue")
@role_required(*HUB_ROLES)
def integration_hub_retry_queue():
    return render_hub_page("Retry Queue", build_retry_queue_body())


@integration_hub_web_bp.route("/integration-hub/dead-letters")
@role_required(*HUB_ROLES)
def integration_hub_dead_letters():
    return render_hub_page("Dead Letter Queue", build_dead_letters_body())


@integration_hub_web_bp.route("/integration-hub/audit")
@role_required(*HUB_ROLES)
def integration_hub_audit():
    return render_hub_page("Integration Audit Log", build_audit_body())


@integration_hub_web_bp.route("/integration-hub/sandbox", methods=["GET", "POST"])
@role_required(*HUB_ROLES)
def integration_hub_sandbox():
    if request.method == "GET":
        return render_hub_page("Sandbox Test", build_sandbox_body())
    payload_raw = request.form.get("payload", "").strip()
    payload = None
    if payload_raw:
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            return render_hub_page(
                "Sandbox Test",
                build_sandbox_body(error="Invalid JSON payload."),
            )
    try:
        result = sandbox_test(
            request.form.get("adapter_type", "HIS"),
            payload,
            actor=_actor(),
        )
        return render_hub_page("Sandbox Test", build_sandbox_body(result=result))
    except IntegrationHubError as exc:
        return render_hub_page("Sandbox Test", build_sandbox_body(error=exc.message))
