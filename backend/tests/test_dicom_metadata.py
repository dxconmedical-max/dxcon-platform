import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.healthcare_standards import DICOMStudyMetadata
from tests.standards_test_helpers import seed_demo_data


class DICOMMetadataTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_demo_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_list_and_get_study(self):
        studies = self.client.get("/api/v1/standards/dicom/studies")
        self.assertEqual(studies.status_code, 200)
        self.assertGreaterEqual(studies.get_json()["count"], 1)
        study_id = studies.get_json()["studies"][0]["id"]

        detail = self.client.get(f"/api/v1/standards/dicom/studies/{study_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertGreaterEqual(len(detail.get_json()["series"]), 1)

    def test_save_metadata(self):
        before = DICOMStudyMetadata.query.count()
        response = self.client.post(
            "/api/v1/standards/dicom/metadata",
            json={
                "study": {
                    "study_uid": "1.2.840.demo.study.002",
                    "patient_id": "PAT-002",
                    "modality": "MR",
                    "description": "Demo MR",
                },
                "series": [],
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DICOMStudyMetadata.query.count(), before + 1)


if __name__ == "__main__":
    unittest.main()
