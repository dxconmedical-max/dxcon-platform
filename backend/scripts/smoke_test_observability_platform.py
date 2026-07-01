import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        client = app.test_client()

        for path in ("/health", "/ready", "/live", "/api/v1/metrics", "/metrics/prometheus"):
            response = client.get(path)
            assert response.status_code in (200, 503), path

        alert = client.post("/api/v1/alerts/test", json={"rule_code": "QUEUE_BACKLOG"})
        assert alert.status_code == 201

        for page in ("/system/metrics", "/system/health", "/system/alerts", "/system/audit", "/system/traces", "/system/logs"):
            response = client.get(page)
            assert response.status_code == 200, page

    print("SMOKE TEST PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
