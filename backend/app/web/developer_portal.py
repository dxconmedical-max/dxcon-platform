"""Partner Developer Portal web routes — Phase 4 Sprint 4.5."""

from __future__ import annotations

import json

from flask import Blueprint, current_app, request

from app.services.developer_portal_service import DeveloperPortalError, execute_sandbox, test_webhook
from app.web.developer_portal_lib import (
    build_api_body,
    build_landing_body,
    build_onboarding_body,
    build_sandbox_body,
    build_webhooks_body,
    render_dev_page,
)

developer_portal_web_bp = Blueprint("developer_portal_web", __name__)


@developer_portal_web_bp.route("/developer")
def developer_portal_home():
    return render_dev_page(
        "Partner Developer Portal",
        build_landing_body(current_app._get_current_object()),
    )


@developer_portal_web_bp.route("/developer/api")
def developer_portal_api():
    return render_dev_page("API Documentation", build_api_body())


@developer_portal_web_bp.route("/developer/webhooks", methods=["GET", "POST"])
def developer_portal_webhooks():
    app = current_app._get_current_object()
    result = None
    error = None
    if request.method == "POST":
        webhook_raw = (request.form.get("webhook_id") or "").strip()
        webhook_id = int(webhook_raw) if webhook_raw.isdigit() else None
        payload_raw = request.form.get("payload") or "{}"
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            payload = {"raw": payload_raw}
        data = {
            "event_type": request.form.get("event_type") or "OrderCreated",
            "payload": payload,
        }
        try:
            result = test_webhook(webhook_id, data)
        except DeveloperPortalError as exc:
            error = exc.message
    return render_dev_page(
        "Webhook Test Console",
        build_webhooks_body(app, result=result, error=error),
    )


@developer_portal_web_bp.route("/developer/sandbox", methods=["GET", "POST"])
def developer_portal_sandbox():
    app = current_app._get_current_object()
    result = None
    error = None
    if request.method == "POST" and request.form.get("mode") == "api":
        headers_raw = request.form.get("headers") or "{}"
        body_raw = request.form.get("body") or ""
        try:
            headers = json.loads(headers_raw)
        except json.JSONDecodeError:
            headers = {}
        body = None
        if body_raw.strip():
            try:
                body = json.loads(body_raw)
            except json.JSONDecodeError:
                body = {"raw": body_raw}
        data = {
            "method": request.form.get("method") or "GET",
            "path": request.form.get("path") or "/api/v1/api-platform/health",
            "headers": headers,
            "body": body,
        }
        try:
            result = execute_sandbox(app, data)
        except DeveloperPortalError as exc:
            error = exc.message
    return render_dev_page(
        "Developer Sandbox",
        build_sandbox_body(app, result=result, error=error),
    )


@developer_portal_web_bp.route("/developer/onboarding")
def developer_portal_onboarding():
    return render_dev_page("Partner Onboarding", build_onboarding_body())
