import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from scripts.go_live_rc1_lib import (
    GENERATED_DIR,
    build_api_route_summary,
    compute_rc1_score,
    run_full_rc1_validation,
    write_json,
)


class ReleaseCandidateTestCase(unittest.TestCase):
    def setUp(self):
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    def test_route_summary(self):
        from app import create_app

        app = create_app()
        summary = build_api_route_summary(app)
        self.assertGreater(summary["api_routes"], 50)

    def test_score_computation(self):
        payload = {
            "passed": 20,
            "total": 20,
            "ok": True,
        }
        score = compute_rc1_score(payload, payload, payload, payload, payload)
        self.assertGreaterEqual(score["score"], 85)
        self.assertTrue(score["ready_for_rc1"])

    def test_full_rc1_validation(self):
        result = run_full_rc1_validation(write_reports=True)
        self.assertIn("score", result)
        for name in (
            "RC1_REPORT.json",
            "RC1_CHECKLIST.json",
            "API_ROUTE_SUMMARY.json",
            "GO_LIVE_RISKS.json",
        ):
            self.assertTrue((GENERATED_DIR / name).exists(), name)

    def test_write_json_helper(self):
        path = write_json("_test_rc1.json", {"ok": True})
        self.assertTrue(Path(path).exists())
        Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
