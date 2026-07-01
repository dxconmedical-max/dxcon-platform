import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db


def _payload(response):
    body = response.get_json() or {}
    if isinstance(body.get("data"), dict) and "success" in body:
        return body["data"]
    return body


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        client = app.test_client()

        jobs = client.get("/api/v1/operations/jobs")
        assert jobs.status_code == 200
        job_id = _payload(jobs)["jobs"][0]["id"]
        assert client.post(f"/api/v1/operations/jobs/{job_id}/run").status_code == 200

        assert client.post("/api/v1/operations/backups/run", json={"backup_type": "DATABASE"}).status_code == 201
        assert client.post("/api/v1/operations/restores/dry-run").status_code == 201
        assert client.get("/api/v1/operations/deployment").status_code == 200

        for page in (
            "/operations",
            "/operations/jobs",
            "/operations/backups",
            "/operations/maintenance",
            "/operations/secrets",
            "/operations/deployment",
            "/operations/queues",
        ):
            assert client.get(page).status_code == 200, page

    print("SMOKE TEST PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
