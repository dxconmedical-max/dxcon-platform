"""Partner Developer Portal business logic for Phase 4 Sprint 4.5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.api_platform_service import (
    ApiClientService,
    ApiKeyService,
    ApiPlatformError,
    ApiPlatformService,
    DeveloperSandboxService,
)
from app.services.integration_hub_service import SUPPORTED_ADAPTERS, hub_health, sandbox_test
from app.services.integration_platform_service import (
    IntegrationError,
    IntegrationPlatformService,
    SandboxService,
    WebhookEngineService,
)

ROOT = Path(__file__).resolve().parents[2]
SDK_ROOT = ROOT / "generated_api" / "sdk"
POSTMAN_PATH = ROOT / "generated_api" / "postman_collection.json"

FEATURES = (
    "Developer Portal Landing",
    "API Documentation Links",
    "API Key Instructions",
    "Webhook Test Console",
    "Sandbox Payload Examples",
    "Integration Status Page",
    "SDK Download Links",
    "Postman Collection Link",
    "Partner Onboarding Checklist",
    "Verification Report",
)


class DeveloperPortalError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_portal() -> dict[str, Any]:
    ApiClientService.ensure_defaults()
    IntegrationPlatformService.ensure_defaults()
    return {"ready": True}


def api_documentation_links() -> dict[str, Any]:
    return {
        "openapi_json": "/api/v1/openapi.json",
        "openapi_yaml": "/api/v1/openapi.yaml",
        "swagger_ui": "/api-docs/swagger",
        "redoc": "/api-docs/redoc",
        "docs_index": "/api-docs",
        "developer_api": "/developer/api",
    }


def api_key_instructions() -> dict[str, Any]:
    ensure_portal()
    keys = ApiKeyService.list_keys()
    return {
        "header": "X-API-Key",
        "steps": [
            "Request a partner API client from your DxCon administrator.",
            "Receive a client ID and secret key prefix from the onboarding team.",
            "Send the full API key in the X-API-Key header on every /api/v1/ request.",
            "Use POST /api/v1/developer/sandbox/request to validate connectivity before production.",
            "Monitor usage at GET /api/v1/api-usage and rotate keys through your administrator.",
        ],
        "example_headers": {"X-API-Key": "dxcon_live_xxxxxxxxxxxxxxxx"},
        "sandbox_endpoint": "/api/v1/developer/sandbox/request",
        "active_keys": keys["count"],
        "manage_ui": "/developer/api-keys",
    }


def sandbox_payload_examples() -> dict[str, Any]:
    ensure_portal()
    adapter_samples = {
        adapter: {
            "adapter_type": adapter,
            "payload": _default_adapter_payload(adapter),
        }
        for adapter in SUPPORTED_ADAPTERS
    }
    return {
        "sandbox": True,
        "api_request": {
            "method": "GET",
            "path": "/api/v1/api-platform/health",
            "headers": {},
        },
        "adapters": adapter_samples,
        "webhook_test": {
            "event_type": "OrderCreated",
            "payload": {
                "order_id": "ORD-SANDBOX-001",
                "patient_id": "PAT-SANDBOX-001",
                "status": "CREATED",
            },
        },
        "execute_endpoint": "/api/v1/developer/sandbox/request",
        "integration_sandbox_endpoint": "/api/v1/integration-hub/sandbox/test",
    }


def _default_adapter_payload(adapter: str) -> dict[str, Any]:
    defaults = {
        "HIS": {"patient_id": "SANDBOX-PATIENT", "name": "Sandbox Patient"},
        "LIS": {"result_id": "SANDBOX-RESULT", "status": "FINAL"},
        "EMR": {"record_id": "SANDBOX-EMR", "status": "SIGNED"},
        "ERP": {"order_id": "SANDBOX-ERP", "status": "POSTED"},
        "INSURANCE": {"claim_id": "SANDBOX-CLM", "status": "APPROVED"},
        "PAYMENT": {"transaction_id": "SANDBOX-TXN", "status": "PAID"},
    }
    return defaults.get(adapter, {"sample": True})


def integration_status(app) -> dict[str, Any]:
    ensure_portal()
    platform = ApiPlatformService.health(app)
    hub = hub_health()
    sandbox = SandboxService.status()
    webhooks = WebhookEngineService.list_webhooks()
    return {
        "status": platform["status"] if hub["status"] == "OK" else "DEGRADED",
        "platform": platform,
        "integration_hub": hub,
        "sandbox": sandbox,
        "webhooks": {"count": webhooks["count"], "endpoints": webhooks.get("webhooks", [])[:5]},
        "routes_total": platform["summary"]["total"],
        "domains_total": platform["summary"].get("domain_count", 0),
    }


def sdk_download_links() -> dict[str, Any]:
    manifest_path = SDK_ROOT / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    downloads = []
    python_path = SDK_ROOT / "python" / "dxcon_client.py"
    typescript_path = SDK_ROOT / "typescript" / "dxcon_client.ts"
    if python_path.exists():
        downloads.append(
            {
                "language": "python",
                "filename": python_path.name,
                "url": "/api/v1/developer-portal/sdk/python",
            }
        )
    if typescript_path.exists():
        downloads.append(
            {
                "language": "typescript",
                "filename": typescript_path.name,
                "url": "/api/v1/developer-portal/sdk/typescript",
            }
        )
    return {
        "available": bool(downloads),
        "manifest": manifest,
        "downloads": downloads,
    }


def sdk_file_content(language: str) -> tuple[str, str]:
    mapping = {
        "python": SDK_ROOT / "python" / "dxcon_client.py",
        "typescript": SDK_ROOT / "typescript" / "dxcon_client.ts",
    }
    path = mapping.get((language or "").lower())
    if path is None or not path.exists():
        raise DeveloperPortalError(f"SDK not available for language: {language}", 404)
    return path.name, path.read_text(encoding="utf-8")


def postman_collection_link() -> dict[str, Any]:
    ensure_portal()
    return {
        "collection_url": "/api/v1/developer-portal/postman",
        "openapi_import": "/api/v1/openapi.json",
        "instructions": [
            "Download the Postman collection JSON from the link above.",
            "Import into Postman via File → Import.",
            "Set the baseUrl variable to your DxCon environment.",
            "Alternatively import /api/v1/openapi.json directly for full route coverage.",
        ],
        "available": POSTMAN_PATH.exists(),
    }


def postman_collection_payload() -> dict[str, Any]:
    if POSTMAN_PATH.exists():
        return json.loads(POSTMAN_PATH.read_text(encoding="utf-8"))
    return _default_postman_collection()


def _default_postman_collection() -> dict[str, Any]:
    return {
        "info": {
            "name": "DxCon Partner API",
            "description": "Starter collection for DxCon partner integrations.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "baseUrl", "value": "http://localhost:5000"}],
        "item": [
            {
                "name": "Platform Health",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": "{{baseUrl}}/api/v1/api-platform/health",
                },
            },
            {
                "name": "Developer Sandbox Request",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps(
                            {
                                "method": "GET",
                                "path": "/api/v1/api-platform/health",
                            },
                            indent=2,
                        ),
                    },
                    "url": "{{baseUrl}}/api/v1/developer/sandbox/request",
                },
            },
        ],
    }


def onboarding_checklist() -> dict[str, Any]:
    return {
        "title": "Partner Integration Onboarding",
        "steps": [
            {
                "id": 1,
                "title": "Review API documentation",
                "detail": "Browse /developer/api and import OpenAPI into your toolchain.",
                "links": ["/developer/api", "/api/v1/openapi.json"],
            },
            {
                "id": 2,
                "title": "Obtain API credentials",
                "detail": "Work with DxCon admin to provision a client and API key.",
                "links": ["/developer/api-keys"],
            },
            {
                "id": 3,
                "title": "Validate sandbox connectivity",
                "detail": "Run sample requests from /developer/sandbox using the developer sandbox API.",
                "links": ["/developer/sandbox"],
            },
            {
                "id": 4,
                "title": "Configure webhook endpoints",
                "detail": "Register HTTPS endpoints and verify signatures using the webhook test console.",
                "links": ["/developer/webhooks", "/integration-hub/webhooks"],
            },
            {
                "id": 5,
                "title": "Test adapter payloads",
                "detail": "Exercise HIS, LIS, EMR, ERP, insurance, and payment sandbox payloads.",
                "links": ["/developer/sandbox", "/integration-hub/sandbox"],
            },
            {
                "id": 6,
                "title": "Download SDK or Postman collection",
                "detail": "Use generated SDKs or import the Postman starter collection.",
                "links": ["/developer/api"],
            },
            {
                "id": 7,
                "title": "Monitor integration status",
                "detail": "Confirm platform health and webhook delivery before go-live.",
                "links": ["/developer", "/integration-hub"],
            },
            {
                "id": 8,
                "title": "Complete verification report",
                "detail": "Run backend/scripts/verify_developer_portal.py and share DEVELOPER_PORTAL_REPORT.json.",
                "links": ["/developer/onboarding"],
            },
        ],
    }


def dashboard_payload(app) -> dict[str, Any]:
    ensure_portal()
    docs = api_documentation_links()
    keys = api_key_instructions()
    sdk = sdk_download_links()
    postman = postman_collection_link()
    status = integration_status(app)
    return {
        "platform": "Partner Developer Portal",
        "phase": "4.5",
        "sprint": "Partner Developer Portal",
        "status": status["status"],
        "summary": {
            "routes_total": status["routes_total"],
            "domains_total": status["domains_total"],
            "active_api_keys": keys["active_keys"],
            "webhooks": status["webhooks"]["count"],
            "sdk_languages": len(sdk["downloads"]),
            "postman_available": postman["available"],
        },
        "features": list(FEATURES),
        "documentation": docs,
        "onboarding_steps": len(onboarding_checklist()["steps"]),
    }


def test_webhook(webhook_id: int | None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_portal()
    payload = data or {}
    if webhook_id:
        try:
            return WebhookEngineService.test(webhook_id, payload)
        except IntegrationError as exc:
            raise DeveloperPortalError(exc.message, exc.status_code) from exc
    try:
        return SandboxService.webhook_test(payload)
    except IntegrationError as exc:
        raise DeveloperPortalError(exc.message, exc.status_code) from exc


def execute_sandbox(app, data: dict[str, Any]) -> dict[str, Any]:
    ensure_portal()
    try:
        return DeveloperSandboxService.execute(app, data or {})
    except ApiPlatformError as exc:
        raise DeveloperPortalError(str(exc), 400) from exc


def run_adapter_sandbox(adapter_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from app.services.integration_hub_service import IntegrationHubError

    try:
        return sandbox_test(adapter_type, payload)
    except IntegrationHubError as exc:
        raise DeveloperPortalError(exc.message, exc.status_code) from exc
