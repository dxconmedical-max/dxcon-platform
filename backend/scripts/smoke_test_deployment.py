import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db


def main():
    print("\n=== DXCON DEPLOYMENT SMOKE TEST ===\n")
    errors = 0

    app = create_app()
    with app.app_context():
        db.create_all()
        app.extensions.setdefault("dxcon_deployment", {})
        app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True}

    client = app.test_client()

    health = client.get("/api/v1/system/health")
    live = client.get("/api/v1/system/live")
    ready = client.get("/api/v1/system/ready")

    if health.status_code == 200 and health.headers.get("X-Correlation-ID"):
        print("OK: health with correlation id")
    else:
        print("FAIL: health", health.status_code)
        errors += 1

    if live.status_code == 200 and live.get_json().get("alive"):
        print("OK: live probe")
    else:
        print("FAIL: live", live.status_code)
        errors += 1

    if ready.status_code == 200 and ready.get_json().get("ready"):
        print("OK: ready probe")
    else:
        print("FAIL: ready", ready.status_code, ready.get_json())
        errors += 1

    if errors:
        print("\nDEPLOYMENT SMOKE TEST FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nDEPLOYMENT SMOKE TEST PASSED\n")


if __name__ == "__main__":
    main()
