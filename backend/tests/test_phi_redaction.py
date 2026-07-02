import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.ai_platform.phi_redaction import redact_payload, redact_phi


class PHIRedactionTestCase(unittest.TestCase):
    def test_redact_email(self):
        text = "Email patient@example.com for follow up"
        redacted = redact_phi(text)
        self.assertNotIn("patient@example.com", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)

    def test_redact_mrn(self):
        text = "Patient ID: ABC12345 admitted"
        redacted = redact_phi(text)
        self.assertIn("[REDACTED_MRN]", redacted)

    def test_redact_payload(self):
        payload = {"note": "Call 555-123-4567", "email": "user@test.com"}
        redacted = redact_payload(payload)
        self.assertNotIn("user@test.com", redacted["email"])
        self.assertIn("[REDACTED_PHONE]", redacted["note"])


if __name__ == "__main__":
    unittest.main()
