import os
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask import Blueprint

from app import create_app
from app.core.audit import write_audit
from app.core.errors import ApiError, build_error_response
from app.core.logging_config import configure_logging, sanitize_path
from app.core.metrics import metrics
from app.extensions.db import db
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, NotFound, Unauthorized, UnprocessableEntity


test_obs_bp = Blueprint("test_observability", __name__)


@test_obs_bp.route("/api/v1/_observability/error", methods=["GET"])
def trigger_error():
    raise RuntimeError("observability test failure")


class ObservabilityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.register_blueprint(test_obs_bp)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        metrics.request_count = 0
        metrics.error_count = 0
        metrics.total_latency_ms = 0.0

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_app_creates(self):
        self.assertIsNotNone(self.app)
        self.assertIn("system", self.app.blueprints)

    def test_logging_config_imports_and_sanitize(self):
        configure_logging(self.app)
        sanitized = sanitize_path("/api/v1/login?password=secret&page=1")
        self.assertIn("password=[REDACTED]", sanitized)
        self.assertIn("page=1", sanitized)

    def test_request_id_header_on_response(self):
        response = self.client.get("/api/v1/system/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("X-Request-ID"))

    def test_request_id_can_be_provided(self):
        response = self.client.get(
            "/api/v1/system/health",
            headers={"X-Request-ID": "req-test-123"},
        )
        self.assertEqual(response.headers.get("X-Request-ID"), "req-test-123")

    def test_api_error_response_format(self):
        payload, status_code = build_error_response(
            "NOT_FOUND",
            "missing resource",
            404,
        )
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "NOT_FOUND")
        self.assertEqual(payload["error"]["message"], "missing resource")
        self.assertIn("request_id", payload["error"])
        self.assertEqual(status_code, 404)

    def test_global_not_found_handler(self):
        response = self.client.get("/api/v1/system/does-not-exist-route")
        self.assertEqual(response.status_code, 404)
        payload = response.get_json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "NOT_FOUND")
        self.assertTrue(payload["error"]["request_id"])

    def test_global_internal_error_handler(self):
        response = self.client.get("/api/v1/_observability/error")
        self.assertEqual(response.status_code, 500)
        payload = response.get_json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertEqual(
            payload["error"]["message"],
            "An unexpected error occurred",
        )

    def test_http_exception_handlers(self):
        cases = [
            (BadRequest("invalid input"), 400, "BAD_REQUEST"),
            (Unauthorized("auth required"), 401, "UNAUTHORIZED"),
            (Forbidden("forbidden"), 403, "FORBIDDEN"),
            (Conflict("conflict"), 409, "CONFLICT"),
            (UnprocessableEntity("invalid payload"), 422, "UNPROCESSABLE_ENTITY"),
        ]

        for exc, status_code, code in cases:
            with self.app.test_request_context("/api/v1/system/health"):
                response = self.app.handle_user_exception(exc)
                payload = response[0] if isinstance(response, tuple) else response.get_json()
                if isinstance(response, tuple):
                    body, actual_status = response
                    self.assertEqual(actual_status, status_code)
                    self.assertFalse(body["success"])
                    self.assertEqual(body["error"]["code"], code)
                else:
                    self.assertEqual(response.status_code, status_code)

    def test_api_error_class(self):
        error = ApiError("bad request", status_code=400)
        with self.app.test_request_context("/api/v1/system/health"):
            response = self.app.handle_user_exception(error)
            if isinstance(response, tuple):
                body, status_code = response
            else:
                body = response.get_json()
                status_code = response.status_code
            self.assertEqual(status_code, 400)
            self.assertEqual(body["error"]["code"], "BAD_REQUEST")

    def test_audit_request_id_correlation(self):
        with self.app.test_request_context(
            "/api/v1/system/health",
            headers={"X-Request-ID": "audit-req-001"},
        ):
            write_audit("TEST", "SYSTEM", "1", user_email="tester@dxcon.local")
            db.session.commit()
            from app.models.audit_log import AuditLog

            audit = AuditLog.query.order_by(AuditLog.created_at.desc()).first()
            self.assertEqual(audit.request_id, "audit-req-001")

    def test_metrics_endpoint(self):
        self.client.get("/api/v1/system/health")
        response = self.client.get("/api/v1/system/metrics")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("request_count", payload)
        self.assertIn("error_count", payload)
        self.assertIn("latency_ms", payload)
        self.assertIn("route_count", payload)
        self.assertIn("health_status", payload)
        self.assertGreaterEqual(payload["request_count"], 1)

    def test_no_duplicate_routes_introduced(self):
        route_map = defaultdict(list)
        for rule in self.app.url_map.iter_rules():
            methods = tuple(
                sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            )
            route_map[(rule.rule, methods)].append(rule.endpoint)

        duplicates = [
            endpoints
            for endpoints in route_map.values()
            if len(endpoints) > 1
        ]
        self.assertEqual(duplicates, [])


if __name__ == "__main__":
    unittest.main()
