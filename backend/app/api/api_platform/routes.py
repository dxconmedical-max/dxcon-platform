import json as jsonlib
from pathlib import Path

from flask import Blueprint, Response, current_app, request

from app.api_platform.openapi_generator import build_openapi, write_openapi_artifacts
from app.api_platform.versioning import apply_version_headers
from app.services.api_platform_service import (
    ApiClientService,
    ApiKeyService,
    ApiPlatformError,
    ApiPlatformService,
    ApiUsageService,
    DeveloperSandboxService,
)


def _error(exc):
    return {"error": exc.message}, exc.status_code


api_platform_bp = Blueprint("api_platform", __name__, url_prefix="/api/v1")


@api_platform_bp.after_request
def _version_headers(response):
    return apply_version_headers(response, request.path)


@api_platform_bp.route("/api-platform/routes", methods=["GET"])
def platform_routes():
    inventory = ApiPlatformService.inventory(current_app._get_current_object())
    return inventory["inventory"]


@api_platform_bp.route("/api-platform/domains", methods=["GET"])
def platform_domains():
    inventory = ApiPlatformService.inventory(current_app._get_current_object())
    return inventory["catalog"]


@api_platform_bp.route("/api-platform/health", methods=["GET"])
def platform_health():
    return ApiPlatformService.health(current_app._get_current_object())


@api_platform_bp.route("/openapi.json", methods=["GET"])
def openapi_json():
    document = build_openapi(current_app._get_current_object())
    return Response(jsonlib.dumps(document, indent=2), mimetype="application/json")


@api_platform_bp.route("/openapi.yaml", methods=["GET"])
def openapi_yaml():
    artifacts = write_openapi_artifacts(current_app._get_current_object())
    yaml_text = Path(artifacts["yaml"]).read_text(encoding="utf-8")
    return Response(yaml_text, mimetype="application/yaml")


@api_platform_bp.route("/api-clients", methods=["GET"])
def list_clients():
    ApiClientService.ensure_defaults()
    return ApiClientService.list_clients()


@api_platform_bp.route("/api-clients", methods=["POST"])
def create_client():
    try:
        return ApiClientService.create(request.get_json(silent=True) or {}), 201
    except ApiPlatformError as exc:
        return _error(exc)


@api_platform_bp.route("/api-keys", methods=["GET"])
def list_keys():
    return ApiKeyService.list_keys(client_id=request.args.get("client_id"))


@api_platform_bp.route("/api-keys", methods=["POST"])
def create_key():
    try:
        return ApiKeyService.create(request.get_json(silent=True) or {}), 201
    except ApiPlatformError as exc:
        return _error(exc)


@api_platform_bp.route("/api-keys/<key_id>/revoke", methods=["POST"])
def revoke_key(key_id):
    try:
        return ApiKeyService.revoke(key_id)
    except ApiPlatformError as exc:
        return _error(exc)


@api_platform_bp.route("/api-usage", methods=["GET"])
def list_usage():
    return ApiUsageService.list_usage(
        client_id=request.args.get("client_id"),
        limit=int(request.args.get("limit") or 100),
    )


@api_platform_bp.route("/developer/sandbox/request", methods=["POST"])
def developer_sandbox_request():
    try:
        return DeveloperSandboxService.execute(
            current_app._get_current_object(),
            request.get_json(silent=True) or {},
        )
    except ApiPlatformError as exc:
        return _error(exc)
