import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.config_validation import config_summary, validate_config
from app.core.rate_limit import rate_limiter
from app.core.security import SECURITY_HEADERS


def _route_key(rule):
    methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
    return rule.rule, tuple(methods)


def main():
    print("\n=== DXCON SECURITY VERIFY ===\n")
    errors = 0

    try:
        app = create_app()
        print("OK: app creates successfully")
    except Exception as exc:
        print("FAIL: app create", exc)
        sys.exit(1)

    try:
        validate_config(app)
        print("OK: config validation passed")
    except Exception as exc:
        print("FAIL: config validation", exc)
        errors += 1

    summary = config_summary(app)
    if summary["database_configured"]:
        print("OK: environment config loaded", summary)
    else:
        print("FAIL: environment config", summary)
        errors += 1

    if app.secret_key == "dxcon-secret-key":
        print("FAIL: hard-coded secret key still in use")
        errors += 1
    else:
        print("OK: app secret key loaded from config")

    client = app.test_client()

    health = client.get("/api/v1/system/health")
    missing_headers = [
        header for header in SECURITY_HEADERS if header not in health.headers
    ]
    if missing_headers:
        print("FAIL: missing security headers", missing_headers)
        errors += 1
    else:
        print("OK: security headers present")

    bad_json = client.post(
        "/api/v1/auth/login",
        data="{bad",
        content_type="application/json",
    )
    bad_payload = bad_json.get_json() or {}
    if (
        bad_json.status_code == 422
        and bad_payload.get("success") is False
        and bad_payload.get("error", {}).get("code") == "VALIDATION_ERROR"
    ):
        print("OK: malformed payload rejected with validation error")
    else:
        print("FAIL: malformed payload handling", bad_json.status_code, bad_payload)
        errors += 1

    invalid_jwt = client.get(
        "/api/v1/mobile/secure/profile",
        headers={"Authorization": "Bearer invalid-token"},
    )
    jwt_payload = invalid_jwt.get_json() or {}
    if invalid_jwt.status_code == 401 and jwt_payload.get("error", {}).get("code"):
        print("OK: JWT validation error format", jwt_payload["error"]["code"])
    else:
        print("FAIL: JWT validation", invalid_jwt.status_code, jwt_payload)
        errors += 1

    rate_limiter.reset()
    app.config["TESTING"] = False
    app.config["RATE_LIMIT_ENABLED"] = True
    app.config["RATE_LIMIT_MAX"] = 1
    app.config["RATE_LIMIT_WINDOW_SECONDS"] = 60
    client.get("/api/v1/security/roles")
    limited = client.get("/api/v1/security/roles")
    if limited.status_code == 429:
        print("OK: rate limiting helper enforced")
    else:
        print("FAIL: rate limiting", limited.status_code)
        errors += 1

    route_map = defaultdict(list)
    for rule in app.url_map.iter_rules():
        route_map[_route_key(rule)].append(rule.endpoint)
    duplicates = [item for item in route_map.values() if len(item) > 1]
    if duplicates:
        print("FAIL: duplicate routes", duplicates[:3])
        errors += 1
    else:
        print("OK: no duplicate routes introduced")

    if errors:
        print("\nSECURITY VERIFY FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nSECURITY VERIFY PASSED\n")


if __name__ == "__main__":
    main()
