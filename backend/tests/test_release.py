import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import LAB_WF_PATIENT_PORTAL, LAB_WORKFLOW_STAGES
from app.extensions.db import db
from app.models.lab_operations import LabOperationResultRelease
from app.services.accession_service import AccessionService
from app.services.release_service import ReleaseService
from app.services.review_service import ReviewService


class ReleaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.accession = AccessionService.create_accession(
            {"sample_code": "SMP-REL-001", "patient_name": "Release Patient"}
        )
        for stage in LAB_WORKFLOW_STAGES[1:9]:
            AccessionService.advance_accession(self.accession.id, target_stage=stage)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_release_to_patient_portal(self):
        ReviewService.create_technician_review(
            {"accession_id": self.accession.id, "reviewer": "tech.alpha"}
        )
        AccessionService.advance_accession(
            self.accession.id, target_stage=LAB_WORKFLOW_STAGES[9]
        )
        ReviewService.create_pathologist_review(
            {"accession_id": self.accession.id, "pathologist": "path.one"}
        )
        release = ReleaseService.create_release(
            {"accession_id": self.accession.id, "released_by": "path.one"}
        )
        self.assertIsNotNone(release.released_at)
        accession = AccessionService.get_accession(self.accession.id)
        self.assertEqual(accession["workflow_stage"], LAB_WF_PATIENT_PORTAL)
        self.assertEqual(LabOperationResultRelease.query.count(), 1)

    def test_release_api(self):
        response = self.client.post(
            "/api/v1/lab/releases",
            json={"accession_id": self.accession.id, "released_by": "tech.alpha"},
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/v1/lab/releases")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["pagination"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
