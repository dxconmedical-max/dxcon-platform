import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.api_platform_service import ApiClientService


class ApiPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        ApiClientService.ensure_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_platform_routes_and_domains(self):
        routes = self.client.get("/api/v1/api-platform/routes")
        self.assertEqual(routes.status_code, 200)
        payload = routes.get_json()
        self.assertGreater(payload["count"], 100)
        self.assertEqual(payload["summary"]["duplicate_count"], 0)

        domains = self.client.get("/api/v1/api-platform/domains")
        self.assertEqual(domains.status_code, 200)
        self.assertGreater(domains.get_json()["domain_count"], 10)

    def test_platform_health_and_headers(self):
        response = self.client.get("/api/v1/api-platform/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-API-Version"), "v1")
        self.assertEqual(response.get_json()["status"], "OK")

    def test_openapi_endpoints(self):
        json_resp = self.client.get("/api/v1/openapi.json")
        yaml_resp = self.client.get("/api/v1/openapi.yaml")
        self.assertEqual(json_resp.status_code, 200)
        self.assertEqual(yaml_resp.status_code, 200)
        document = json_resp.get_json()
        self.assertEqual(document["info"]["title"], "DxCon API")
        self.assertIn("paths", document)

    def test_docs_and_developer_routes(self):
        for path in (
            "/api-docs",
            "/api-docs/swagger",
            "/api-docs/redoc",
            "/developer",
            "/developer/api-keys",
            "/developer/routes",
            "/developer/sandbox",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)


if __name__ == "__main__":
    unittest.main()
