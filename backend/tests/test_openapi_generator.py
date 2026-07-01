import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.api_platform.openapi_generator import build_openapi, write_openapi_artifacts


class OpenAPIGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()

    def test_build_openapi_document(self):
        document = build_openapi(self.app)
        self.assertEqual(document["openapi"], "3.0.3")
        self.assertEqual(document["info"]["version"], "v1")
        self.assertIn("ApiKeyAuth", document["components"]["securitySchemes"])
        self.assertIn("ErrorResponse", document["components"]["schemas"])
        self.assertGreater(len(document["paths"]), 100)
        self.assertGreater(len(document["tags"]), 10)

    def test_write_artifacts(self):
        artifacts = write_openapi_artifacts(self.app)
        self.assertTrue(Path(artifacts["json"]).exists())
        self.assertTrue(Path(artifacts["yaml"]).exists())
        self.assertGreater(artifacts["paths"], 100)


if __name__ == "__main__":
    unittest.main()
