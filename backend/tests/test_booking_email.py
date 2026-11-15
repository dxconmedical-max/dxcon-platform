import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.notifications import booking_email as be  # noqa: E402

KW = dict(to="a@example.com", reference="BK-20261115-ABC123", full_name="Nguyễn <b>Test</b>",
          preferred_date="2026-11-20", preferred_slot="MORNING")


class _Resp:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False


class BookingEmailTests(unittest.TestCase):
    def test_not_configured_sends_nothing(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("urllib.request.urlopen") as op:
            self.assertFalse(be.send_booking_confirmation(**KW))
            op.assert_not_called()

    def test_sends_minimal_payload(self):
        env = {"RESEND_API_KEY": "k", "MAIL_FROM": "DxCon <no-reply@dxcon.com.vn>", "MAIL_REPLY_TO": "x@y.vn"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch("urllib.request.urlopen", return_value=_Resp()) as op:
            self.assertTrue(be.send_booking_confirmation(**KW))
        req = op.call_args[0][0]
        payload = json.loads(req.data)
        self.assertEqual(payload["to"], ["a@example.com"])
        self.assertEqual(payload["reply_to"], "x@y.vn")
        self.assertIn("BK-20261115-ABC123", payload["subject"])
        self.assertIn("20/11/2026", payload["text"])
        self.assertNotIn("<b>Test</b>", payload["html"])  # name is escaped
        self.assertEqual(req.get_header("Authorization"), "Bearer k")
        self.assertTrue(req.get_header("User-agent"))

    def test_failure_never_raises(self):
        env = {"RESEND_API_KEY": "k", "MAIL_FROM": "a@b.vn"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
            self.assertFalse(be.send_booking_confirmation(**KW))

    def test_no_date(self):
        _, text, _ = be.build_booking_email(reference="R", full_name="N", preferred_date=None, preferred_slot=None)
        self.assertIn("Chưa chọn ngày", text)


if __name__ == "__main__":
    unittest.main()
