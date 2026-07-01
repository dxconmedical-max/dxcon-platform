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
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    client = app.test_client()

    checks = [
        ("/live", 200),
        ("/ready", 200),
        ("/api/v1/infrastructure/status", 200),
        ("/api/v1/infrastructure/readiness", 200),
        ("/api/v1/infrastructure/config", 200),
        ("/deployment", 200),
    ]
    errors = 0
    for path, expected in checks:
        response = client.get(path)
        if response.status_code == expected:
            print("OK:", path, response.status_code)
        else:
            print("FAIL:", path, response.status_code)
            errors += 1

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
