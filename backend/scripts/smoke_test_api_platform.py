import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.api_platform_service import ApiClientService


def smoke_test():
    with app.app_context():
        db.create_all()
        ApiClientService.ensure_defaults()
        client_id = ApiClientService.list_clients()["clients"][0]["id"]
        key_resp = client.post("/api/v1/api-keys", json={"client_id": client_id})
        raw_key = key_resp.get_json()["api_key"]
        steps = [
            ("GET platform health", "get", "/api/v1/api-platform/health", None),
            ("GET platform routes", "get", "/api/v1/api-platform/routes", None),
            ("GET platform domains", "get", "/api/v1/api-platform/domains", None),
            ("GET openapi json", "get", "/api/v1/openapi.json", None),
            ("GET openapi yaml", "get", "/api/v1/openapi.yaml", None),
            ("GET api clients", "get", "/api/v1/api-clients", None),
            ("GET api keys", "get", "/api/v1/api-keys", None),
            ("GET api usage", "get", "/api/v1/api-usage", None),
            ("POST sandbox request", "post", "/api/v1/developer/sandbox/request", {"method": "GET", "path": "/api/v1/api-platform/health", "headers": {"X-API-Key": raw_key}}),
            ("GET api docs", "get", "/api-docs", None),
            ("GET swagger docs", "get", "/api-docs/swagger", None),
            ("GET redoc docs", "get", "/api-docs/redoc", None),
            ("GET developer home", "get", "/developer", None),
            ("GET developer routes", "get", "/developer/routes", None),
        ]
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            print("OK:", label, response.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON API PLATFORM SMOKE TEST ===\n")
if not smoke_test():
    print("\nAPI PLATFORM SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nAPI PLATFORM SMOKE TEST PASSED\n")
