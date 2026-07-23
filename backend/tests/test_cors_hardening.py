"""Extended CORS integration tests — Release 8.1."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.security import init_security
from app.infrastructure.production_readiness import cors_status, validate_cors

PRODUCTION_ORIGINS = (
    "https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn"
)
STAGING_ORIGINS = (
    "https://staging.dxcon.com.vn,https://app-staging.dxcon.com.vn"
)


def _cors_test_app(*, app_env: str, cors_origins: str) -> Flask:
    """Minimal app exercising init_security CORS without full create_app import side-effects."""
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "APP_ENV": app_env,
            "CORS_ORIGINS": cors_origins,
            "RATE_LIMIT_ENABLED": False,
            "SECURITY_HEADERS_ENABLED": False,
        }
    )

    @app.get("/api/v1/system/health")
    def health():
        return {"success": True}

    @app.get("/api/v1/auth/me")
    def me():
        return {"error": "Unauthorized"}, 401

    init_security(app)
    return app


class CorsHardeningTestCase(unittest.TestCase):
    def test_dev_allows_wildcard(self):
        app = _cors_test_app(app_env="development", cors_origins="*")
        self.assertTrue(cors_status(app)["ok"])
        validate_cors(app)

    def test_production_rewrites_wildcard_to_explicit_origins(self):
        app = _cors_test_app(app_env="production", cors_origins="*")
        self.assertNotEqual(app.config.get("CORS_ORIGINS"), "*")
        self.assertIn("https://dxcon.com.vn", app.config.get("CORS_ORIGINS"))
        self.assertTrue(cors_status(app)["ok"])
        validate_cors(app)
        client = app.test_client()
        response = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://dxcon.com.vn"},
        )
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://dxcon.com.vn",
        )

    def test_production_rewrites_empty_cors_to_explicit_origins(self):
        app = _cors_test_app(app_env="production", cors_origins="")
        self.assertIn("https://dxcon.com.vn", app.config.get("CORS_ORIGINS"))
        client = app.test_client()
        response = client.open(
            "/api/v1/system/health",
            method="OPTIONS",
            headers={
                "Origin": "https://dxcon.com.vn",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertIn(response.status_code, (200, 204))
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://dxcon.com.vn",
        )

    def test_production_accepts_explicit_origins(self):
        app = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS)
        self.assertTrue(cors_status(app)["ok"])
        validate_cors(app)

    def test_permitted_apex_origin(self):
        client = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS).test_client()
        response = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://dxcon.com.vn"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://dxcon.com.vn",
        )
        self.assertEqual(response.headers.get("Access-Control-Allow-Credentials"), "true")

    def test_permitted_www_origin(self):
        client = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS).test_client()
        response = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://www.dxcon.com.vn"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://www.dxcon.com.vn",
        )

    def test_permitted_application_origin(self):
        client = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS).test_client()
        response = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://app.dxcon.com.vn"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://app.dxcon.com.vn",
        )

    def test_rejected_attacker_origin(self):
        client = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS).test_client()
        response = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://evil.attacker.example"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_options_preflight_allowed_origin(self):
        client = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS).test_client()
        response = client.open(
            "/api/v1/system/health",
            method="OPTIONS",
            headers={
                "Origin": "https://app.dxcon.com.vn",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type,X-Organization-ID",
            },
        )
        self.assertIn(response.status_code, (200, 204))
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://app.dxcon.com.vn",
        )
        allowed_headers = (response.headers.get("Access-Control-Allow-Headers") or "").lower()
        self.assertIn("authorization", allowed_headers)
        self.assertIn("content-type", allowed_headers)

    def test_credentials_enabled_with_explicit_origins(self):
        client = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS).test_client()
        response = client.get(
            "/api/v1/auth/me",
            headers={"Origin": "https://app.dxcon.com.vn"},
        )
        self.assertEqual(response.headers.get("Access-Control-Allow-Credentials"), "true")

    def test_staging_origins_separate_from_production(self):
        client = _cors_test_app(app_env="staging", cors_origins=STAGING_ORIGINS).test_client()
        allowed = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://staging.dxcon.com.vn"},
        )
        denied = client.get(
            "/api/v1/system/health",
            headers={"Origin": "https://dxcon.com.vn"},
        )
        self.assertEqual(
            allowed.headers.get("Access-Control-Allow-Origin"),
            "https://staging.dxcon.com.vn",
        )
        self.assertIsNone(denied.headers.get("Access-Control-Allow-Origin"))

    def test_no_wildcard_production_cors(self):
        app = _cors_test_app(app_env="production", cors_origins=PRODUCTION_ORIGINS)
        self.assertNotEqual(app.config.get("CORS_ORIGINS"), "*")
        self.assertTrue(cors_status(app)["ok"])


if __name__ == "__main__":
    unittest.main()
