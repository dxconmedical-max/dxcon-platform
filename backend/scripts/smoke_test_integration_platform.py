import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.integration_platform_service import IntegrationPlatformService


def smoke_test():
    with app.app_context():
        db.create_all()
        IntegrationPlatformService.ensure_defaults()
        steps = [
            ("GET plugins", "get", "/api/v1/plugins", None),
            ("GET events", "get", "/api/v1/events", None),
            ("POST event test", "post", "/api/v1/events/test", {"event_type": "OrderCreated"}),
            ("GET webhooks", "get", "/api/v1/webhooks", None),
            ("GET webhook deliveries", "get", "/api/v1/webhooks/deliveries", None),
            ("GET queue jobs", "get", "/api/v1/integration-queue/jobs", None),
            ("POST queue job", "post", "/api/v1/integration-queue/jobs", {"adapter_type": "HIS", "payload": {}}),
            ("GET dead letters", "get", "/api/v1/integration-queue/dead-letters", None),
            ("GET sandbox status", "get", "/api/v1/sandbox/status", None),
            ("POST sandbox LIS", "post", "/api/v1/sandbox/lis/result", {"result_id": "R1"}),
            ("POST sandbox HIS", "post", "/api/v1/sandbox/his/patient", {"patient_id": "P1"}),
            ("POST sandbox payment", "post", "/api/v1/sandbox/payment/callback", {"transaction_id": "T1"}),
            ("POST sandbox webhook", "post", "/api/v1/sandbox/webhook/test", {}),
            ("GET platform dashboard", "get", "/integrations/platform", None),
            ("GET adapters dashboard", "get", "/integrations/adapters", None),
            ("GET plugins dashboard", "get", "/integrations/plugins", None),
            ("GET events dashboard", "get", "/integrations/events", None),
            ("GET webhooks dashboard", "get", "/integrations/webhooks", None),
            ("GET queue dashboard", "get", "/integrations/queue", None),
            ("GET sandbox dashboard", "get", "/integrations/sandbox", None),
        ]
        job_id = None
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            if path == "/api/v1/integration-queue/jobs" and method == "post":
                job_id = response.get_json().get("id")
            print("OK:", label, response.status_code)
        if job_id:
            retry = client.post(f"/api/v1/integration-queue/jobs/{job_id}/retry")
            if retry.status_code >= 400:
                print("FAIL: retry job", retry.status_code)
                return False
            print("OK: retry job", retry.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON INTEGRATION PLATFORM SMOKE TEST ===\n")
if not smoke_test():
    print("\nINTEGRATION PLATFORM SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nINTEGRATION PLATFORM SMOKE TEST PASSED\n")
