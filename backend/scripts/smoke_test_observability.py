import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app


def main():
    print("\n=== DXCON OBSERVABILITY SMOKE TEST ===\n")
    errors = 0

    app = create_app()
    client = app.test_client()

    checks = [
        ("health", "/api/v1/system/health"),
        ("metrics", "/api/v1/system/metrics"),
    ]

    for label, path in checks:
        response = client.get(path)
        request_id = response.headers.get("X-Request-ID")
        if response.status_code == 200 and request_id:
            print(f"OK: {label} responds with request_id={request_id}")
        else:
            print(f"FAIL: {label}", response.status_code, request_id)
            errors += 1

    missing = client.get("/api/v1/system/smoke-missing-endpoint")
    body = missing.get_json() or {}
    if (
        missing.status_code == 404
        and body.get("success") is False
        and body.get("error", {}).get("request_id")
    ):
        print("OK: API error envelope on 404")
    else:
        print("FAIL: API error envelope", missing.status_code, body)
        errors += 1

    if errors:
        print("\nOBSERVABILITY SMOKE TEST FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nOBSERVABILITY SMOKE TEST PASSED\n")


if __name__ == "__main__":
    main()
