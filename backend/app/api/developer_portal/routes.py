"""Partner Developer Portal API routes — Phase 4 Sprint 4.5."""

from __future__ import annotations

from flask import Blueprint, current_app, request

from app.services.developer_portal_service import (
    DeveloperPortalError,
    api_documentation_links,
    api_key_instructions,
    dashboard_payload,
    execute_sandbox,
    integration_status,
    onboarding_checklist,
    postman_collection_link,
    postman_collection_payload,
    sandbox_payload_examples,
    sdk_download_links,
    sdk_file_content,
    test_webhook,
)

developer_portal_bp = Blueprint(
    "developer_portal_api",
    __name__,
    url_prefix="/api/v1/developer-portal",
)


@developer_portal_bp.route("/dashboard", methods=["GET"])
def developer_portal_dashboard_api():
    return dashboard_payload(current_app._get_current_object())


@developer_portal_bp.route("/status", methods=["GET"])
def developer_portal_status_api():
    return integration_status(current_app._get_current_object())


@developer_portal_bp.route("/docs", methods=["GET"])
def developer_portal_docs_api():
    return {
        "documentation": api_documentation_links(),
        "api_keys": api_key_instructions(),
        "postman": postman_collection_link(),
        "sdk": sdk_download_links(),
    }


@developer_portal_bp.route("/sandbox/examples", methods=["GET"])
def developer_portal_sandbox_examples_api():
    return sandbox_payload_examples()


@developer_portal_bp.route("/sandbox/request", methods=["POST"])
def developer_portal_sandbox_request_api():
    try:
        return execute_sandbox(current_app._get_current_object(), request.get_json(silent=True) or {})
    except DeveloperPortalError as exc:
        return {"error": exc.message}, exc.status_code


@developer_portal_bp.route("/webhooks/test", methods=["POST"])
def developer_portal_webhook_test_api():
    data = request.get_json(silent=True) or {}
    webhook_id = data.get("webhook_id")
    try:
        return test_webhook(int(webhook_id) if webhook_id else None, data)
    except DeveloperPortalError as exc:
        return {"error": exc.message}, exc.status_code


@developer_portal_bp.route("/onboarding", methods=["GET"])
def developer_portal_onboarding_api():
    return onboarding_checklist()


@developer_portal_bp.route("/postman", methods=["GET"])
def developer_portal_postman_api():
    return postman_collection_payload()


@developer_portal_bp.route("/sdk", methods=["GET"])
def developer_portal_sdk_api():
    return sdk_download_links()


@developer_portal_bp.route("/sdk/<language>", methods=["GET"])
def developer_portal_sdk_download_api(language: str):
    try:
        filename, content = sdk_file_content(language)
    except DeveloperPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return content, 200, {"Content-Type": "text/plain; charset=utf-8", "Content-Disposition": f'attachment; filename="{filename}"'}
