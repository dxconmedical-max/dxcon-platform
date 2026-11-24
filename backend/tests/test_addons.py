import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_addons_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class AddonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_every_endpoint_requires_login(self):
        c = self.app.test_client()
        base = "/api/v1/reception/workspace"
        for method, url in [
            ("get", f"{base}/addons/candidates?q=ab"),
            ("get", f"{base}/addons/tests?order_code=x"),
            ("post", f"{base}/orders/x/addons"),
            ("get", f"{base}/sendout-reminders"),
            ("post", f"{base}/sendout-reminders/x/y"),
            ("get", f"{base}/test-flags"),
            ("post", f"{base}/test-flags/x"),
        ]:
            r = getattr(c, method)(url)
            self.assertIn(r.status_code, (401, 403), f"{method} {url} -> {r.status_code}")

    def test_addon_window(self):
        from app.api.addons.routes import evaluate_addon, window_hours
        from app.models.addon import TestFlag

        now = datetime(2026, 11, 24, 12, 0)
        self.assertEqual(window_hours(None), 72)
        ok, left = evaluate_addon(now - timedelta(hours=71), None, now)
        self.assertTrue(ok)
        self.assertEqual(left, 1.0)
        ok, _ = evaluate_addon(now - timedelta(hours=73), None, now)
        self.assertFalse(ok)
        flag = TestFlag(test_catalog_id="t", addon_window_hours=24)
        ok, _ = evaluate_addon(now - timedelta(hours=30), flag, now)
        self.assertFalse(ok)

    def test_sendout_status(self):
        from app.api.addons.routes import sendout_status

        today = date(2026, 11, 24)
        self.assertEqual(sendout_status(date(2026, 11, 23), today), "OVERDUE")
        self.assertEqual(sendout_status(date(2026, 11, 25), today), "DUE_SOON")
        self.assertEqual(sendout_status(date(2026, 11, 28), today), "WAITING")


if __name__ == "__main__":
    unittest.main()
