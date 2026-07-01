import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.deployment import deployment_readiness
from app.extensions.db import db


def main():
    print("\n=== DXCON DEPLOYMENT VERIFY ===\n")
    errors = 0

    gunicorn_conf = ROOT / "gunicorn.conf.py"
    dockerfile = ROOT / "Dockerfile"
    env_example = ROOT / ".env.example"
    render_yaml = ROOT / "render.yaml"

    for label, path in [
        ("gunicorn.conf.py", gunicorn_conf),
        ("Dockerfile", dockerfile),
        (".env.example", env_example),
        ("render.yaml", render_yaml),
    ]:
        if path.exists():
            print(f"OK: {label} present")
        else:
            print(f"FAIL: missing {label}")
            errors += 1

    try:
        app = create_app()
        print("OK: app creates successfully")
    except Exception as exc:
        print("FAIL: app create", exc)
        sys.exit(1)

    with app.app_context():
        db.create_all()
        app.extensions.setdefault("dxcon_deployment", {})
        app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True}

    client = app.test_client()
    endpoints = [
        ("/api/v1/system/health", 200),
        ("/api/v1/system/live", 200),
        ("/api/v1/system/liveness", 200),
        ("/api/v1/system/ready", 200),
        ("/api/v1/system/readiness", 200),
        ("/api/v1/system/metrics", 200),
        ("/api/v1/system/version", 200),
        ("/api/v1/system/build", 200),
    ]

    for path, expected_status in endpoints:
        response = client.get(path)
        if response.status_code == expected_status:
            print("OK: endpoint", path)
        else:
            print("FAIL: endpoint", path, response.status_code)
            errors += 1

    readiness = deployment_readiness(app)
    print("Deployment readiness score:", readiness["score"])
    print("Ready for production:", readiness["ready_for_production"])
    for check in readiness["checks"]:
        print(f"  - {check['name']}: {check['status']}")

    if readiness["score"] < 80:
        print("WARN: readiness score below 80")
    else:
        print("OK: readiness score acceptable")

    if errors:
        print("\nDEPLOYMENT VERIFY FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nDEPLOYMENT VERIFY PASSED\n")


if __name__ == "__main__":
    main()
