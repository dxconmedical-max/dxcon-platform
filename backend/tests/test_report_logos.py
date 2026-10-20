import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_logo_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.lab_workspace.service import ensure_logo_header
from app.reporting_engine.logos import detect_logo_type


class LogoTests(unittest.TestCase):
    def test_detects_only_png_and_jpeg_by_content(self):
        self.assertEqual(detect_logo_type(b"\x89PNG\r\n\x1a\n" + b"x"), "image/png")
        self.assertEqual(detect_logo_type(b"\xff\xd8\xff\xe0" + b"x"), "image/jpeg")
        self.assertIsNone(detect_logo_type(b"<svg onload=alert(1)></svg>"))
        self.assertIsNone(detect_logo_type(b"GIF89a"))

    def test_serve_without_logo_keeps_html(self):
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            html = "<html><body><p>x</p></body></html>"
            self.assertEqual(ensure_logo_header(html), html)

    def test_routes_registered_and_anonymous_rejected(self):
        from app import create_app

        app = create_app()
        rules = {r.rule for r in app.url_map.iter_rules()}
        self.assertIn("/api/v1/report-logos", rules)
        client = app.test_client()
        self.assertIn(client.get("/api/v1/report-logos").status_code, (401, 403))
        self.assertIn(client.post("/api/v1/report-logos").status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
