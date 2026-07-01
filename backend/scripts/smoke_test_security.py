import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.security import SECURITY_HEADERS


def main():
    print("\n=== DXCON SECURITY SMOKE TEST ===\n")
    errors = 0

    app = create_app()
    client = app.test_client()

    health = client.get("/api/v1/system/health")
    if health.status_code == 200 and health.headers.get("X-Request-ID"):
        print("OK: health responds with request_id")
    else:
        print("FAIL: health", health.status_code)
        errors += 1

    if all(header in health.headers for header in SECURITY_HEADERS):
        print("OK: security headers on API response")
    else:
        print("FAIL: security headers missing")
        errors += 1

    bad_login = client.post(
        "/api/v1/auth/login",
        data="{}",
        content_type="text/plain",
    )
    body = bad_login.get_json() or {}
    if bad_login.status_code == 422 and body.get("error", {}).get("code") == "VALIDATION_ERROR":
        print("OK: input validation rejects non-json login")
    else:
        print("FAIL: input validation", bad_login.status_code, body)
        errors += 1

    if errors:
        print("\nSECURITY SMOKE TEST FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nSECURITY SMOKE TEST PASSED\n")


if __name__ == "__main__":
    main()
