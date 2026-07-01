import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.api_platform.openapi_generator import write_openapi_artifacts
from app.core.passwords import verify_password
from app.extensions.db import db
from app.models.api_platform import ApiKey
from app.services.api_platform_service import ApiClientService, ApiKeyService, DeveloperSandboxService


def verify_models():
    from app.models.api_platform import ApiClient, ApiKey as ApiKeyModel, ApiUsageLog

    for model in (ApiClient, ApiKeyModel, ApiUsageLog):
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/api-platform/routes",
        "/api/v1/api-platform/domains",
        "/api/v1/api-platform/health",
        "/api/v1/openapi.json",
        "/api/v1/openapi.yaml",
        "/api/v1/api-clients",
        "/api/v1/api-keys",
        "/api/v1/api-keys/<key_id>/revoke",
        "/api/v1/api-usage",
        "/api/v1/developer/sandbox/request",
        "/api-docs",
        "/api-docs/swagger",
        "/api-docs/redoc",
        "/developer",
        "/developer/api-keys",
        "/developer/routes",
        "/developer/sandbox",
    ]
    missing = [route for route in required if route not in routes]
    for route in required:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
        return False
    return True


def verify_no_duplicate_routes(app):
    prefixes = (
        "/api/v1/api-platform",
        "/api/v1/openapi",
        "/api/v1/api-clients",
        "/api/v1/api-keys",
        "/api/v1/api-usage",
        "/api/v1/developer",
        "/api-docs",
        "/developer",
    )
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in prefixes):
            continue
        key = (path, tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})))
        seen[key].append(rule.endpoint)
    duplicates = {key: endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    if duplicates:
        print("DUPLICATE:", duplicates)
        return False
    print("OK: no duplicate API platform routes")
    return True


def _payload(response):
    body = response.get_json() or {}
    if isinstance(body.get("data"), dict) and "success" in body:
        return body["data"]
    return body


def verify_engines(app):
    inventory = app.test_client().get("/api/v1/api-platform/routes")
    body = _payload(inventory)
    if inventory.status_code != 200 or body.get("count", 0) < 100:
        print("FAIL: API inventory")
        return False
    print("OK: API inventory")

    artifacts = write_openapi_artifacts(app)
    for label in ("json", "yaml"):
        path = Path(artifacts[label])
        if not path.exists() or path.stat().st_size < 20:
            print("MISSING:", path)
            return False
        print("OK:", path)

    sdk = subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_sdk.py")], cwd=ROOT)
    if sdk.returncode != 0:
        print("FAIL: SDK generation")
        return False
    print("OK: SDK generation")

    ApiClientService.ensure_defaults()
    client_id = ApiClientService.list_clients()["clients"][0]["id"]
    created = ApiKeyService.create({"client_id": client_id})
    row = ApiKey.query.filter_by(id=created["id"]).first()
    if not verify_password(row.key_hash, created["api_key"]):
        print("FAIL: API key hashing")
        return False
    print("OK: API key hashing")

    revoked = ApiKeyService.revoke(created["id"])
    if revoked["status"] != "REVOKED":
        print("FAIL: API key revocation")
        return False
    print("OK: API key revocation")

    sandbox = DeveloperSandboxService.execute(
        app,
        {"method": "GET", "path": "/api/v1/api-platform/health", "headers": {"X-API-Key": created["api_key"]}},
    )
    if sandbox["status_code"] != 200:
        print("FAIL: developer sandbox")
        return False
    print("OK: developer sandbox")
    return True


app = create_app()
print("\n=== DXCON API PLATFORM VERIFY ===\n")
errors = 0
try:
    app.test_client().get("/api/v1/api-platform/health")
except Exception as exc:
    print("FAIL: app create", exc)
    sys.exit(1)
print("OK: app creates successfully")
with app.app_context():
    db.create_all()
    if not verify_models():
        errors += 1
    if not verify_routes(app):
        errors += 1
    if not verify_no_duplicate_routes(app):
        errors += 1
    if not verify_engines(app):
        errors += 1
if errors:
    print("\nAPI PLATFORM VERIFY FAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nAPI PLATFORM VERIFY PASSED\n")
