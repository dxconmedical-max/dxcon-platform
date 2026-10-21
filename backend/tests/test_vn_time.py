import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.vn_time import format_vn_time, localize_report_times


class VnTimeTests(unittest.TestCase):
    def test_naive_is_utc(self):
        self.assertEqual(format_vn_time(datetime(2026, 10, 20, 16, 39, 3, 559078)), "20/10/2026 23:39:03 (GMT+7)")

    def test_crosses_midnight_and_z_suffix(self):
        self.assertEqual(format_vn_time("2026-10-20 20:00:00"), "21/10/2026 03:00:00 (GMT+7)")
        self.assertEqual(format_vn_time("2026-10-20T20:00:00Z"), "21/10/2026 03:00:00 (GMT+7)")
        self.assertEqual(
            format_vn_time(datetime(2026, 10, 20, 20, 0, tzinfo=timezone.utc)), "21/10/2026 03:00:00 (GMT+7)"
        )

    def test_empty_and_garbage(self):
        self.assertEqual(format_vn_time(None), "—")
        self.assertEqual(format_vn_time(""), "—")
        self.assertEqual(format_vn_time("not a date"), "not a date")

    def test_stored_html_is_localized_once(self):
        html = (
            "<p>Released: 2026-10-20 16:39:06.372624</p>"
            "<p><strong>Approved at:</strong> 2026-10-20 16:39:03.559078</p>"
        )
        out = localize_report_times(html)
        self.assertIn("Released: 20/10/2026 23:39:06 (GMT+7)", out)
        self.assertIn("Approved at:</strong> 20/10/2026 23:39:03 (GMT+7)", out)
        self.assertEqual(localize_report_times(out), out)


if __name__ == "__main__":
    unittest.main()
