import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.iot_device_auth import (
    extract_event_timestamp,
    validate_event_timestamp,
)


class NaiveTimestampTests(unittest.TestCase):
    def test_naive_iso_is_treated_as_utc(self):
        recent = (datetime.now(timezone.utc) - timedelta(seconds=5)).replace(tzinfo=None)
        ts = extract_event_timestamp({"timestamp": recent.isoformat()})
        self.assertIsNotNone(ts)
        self.assertEqual(ts.tzinfo, timezone.utc)

    def test_naive_iso_does_not_raise_in_validation(self):
        recent = (datetime.now(timezone.utc) - timedelta(seconds=5)).replace(tzinfo=None)
        ts = extract_event_timestamp({"event_timestamp": recent.isoformat()})
        ok, err = validate_event_timestamp(ts)
        self.assertTrue(ok, err)

    def test_naive_old_timestamp_is_rejected_not_500(self):
        ts = extract_event_timestamp({"recorded_at": "2020-01-01T00:00:00"})
        ok, err = validate_event_timestamp(ts)
        self.assertFalse(ok)
        self.assertEqual(err, "Event timestamp too old")

    def test_z_suffix_and_offset_unchanged(self):
        self.assertEqual(
            extract_event_timestamp({"timestamp": "2026-10-18T10:00:00Z"}),
            datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            extract_event_timestamp({"timestamp": "2026-10-18T17:00:00+07:00"}),
            datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
