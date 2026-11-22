import base64
import io
import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import openpyxl
from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.reference_range import ReferenceRange
from app.models.user import User

HEAD = ["code", "name", "ky_hieu", "nhom", "mau", "category", "sample_type", "unit", "sex", "age_from", "age_to", "low", "high", "text", "source"]


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(HEAD)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def _headers(role):
    user = User(email=f"ri-{uuid.uuid4().hex[:8]}@test.local", role=role, password_hash=hash_password("Password123!"), is_active=True)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=user.id, additional_claims={"role": role, "email": user.email})
    return {"Authorization": f"Bearer {token}"}


class ReferenceImportTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.root = _headers("SUPER_ADMIN")
        self.file = _xlsx(
            [
                ["A1", "Glucose", "GLU", "g", "m", "c", "Blood", "mmol/L", "ALL", 18, None, 3.9, 5.6, None, "src"],
                ["A2", "HBsAg", "HBsAg", "g", "m", "c", "Blood", None, "ALL", None, None, None, None, "Âm tính", "src"],
                ["A3", "Bad", "B", "g", "m", "c", "Blood", "u", "ALL", None, None, 9, 1, None, "src"],
                ["A4", "Cobalt", "Co", "g", "m", "c", "Blood", "ug/L", "ALL", None, None, 0.1, 0.4, "< 1.0 µg/L", "src"],
            ]
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _post(self, **extra):
        return self.client.post("/api/v1/reference-ranges-import", json={"file_b64": self.file, **extra}, headers=self.root)

    def test_dry_run_changes_nothing(self):
        data = self._post().get_json()["report"]
        self.assertEqual(data["importable"], 1)
        self.assertEqual(data["text_only_skipped"], 1)
        self.assertEqual(data["conflict_skipped"], 1)
        self.assertFalse(data["applied"])
        self.assertEqual(ReferenceRange.query.count(), 0)

    def test_apply_creates_draft_only_and_draft_is_not_resolved(self):
        self._post(apply=True)
        row = ReferenceRange.query.one()
        self.assertEqual(row.status, "DRAFT")
        self.assertEqual(row.age_min, 18)
        from app.services.interpretation_engine_service import ReferenceRangeService

        self.assertIsNone(ReferenceRangeService.resolve("A1", age=30, sex="M"))

    def test_activate_needs_phrase_and_makes_row_usable(self):
        self._post(apply=True)
        res = self.client.post("/api/v1/reference-ranges-import/activate", json={}, headers=self.root)
        self.assertEqual(res.status_code, 400)
        res = self.client.post("/api/v1/reference-ranges-import/activate", json={"confirm": "toi xac nhan"}, headers=self.root)
        self.assertEqual(res.status_code, 200)
        from app.services.interpretation_engine_service import ReferenceRangeService

        self.assertIsNotNone(ReferenceRangeService.resolve("A1", age=30, sex="M"))
        self.assertIsNone(ReferenceRangeService.resolve("A1", age=10, sex="M"))

    def test_only_super_admin_can_activate_and_doctor_cannot_import(self):
        res = self.client.post("/api/v1/reference-ranges-import/activate", json={"confirm": "TOI XAC NHAN"}, headers=_headers("SYSTEM_ADMIN"))
        self.assertEqual(res.status_code, 403)
        res = self.client.post("/api/v1/reference-ranges-import", json={"file_b64": self.file}, headers=_headers("DOCTOR"))
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
