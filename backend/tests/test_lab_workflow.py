import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import LAB_WF_PATIENT_PORTAL, LAB_WF_RECEIVED_LAB, LAB_WORKFLOW_STAGES
from app.extensions.db import db
from app.models.lab_accession import LabWorkflowTransition, SampleAccession
from app.services.accession_service import AccessionService
from app.services.analyzer_service import AnalyzerService
from app.services.lab_workflow_service import LabWorkflowService
from app.services.qc_service import QCService
from app.services.release_service import ReleaseService
from app.services.review_service import ReviewService


class LabWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        AnalyzerService.ensure_facility_defaults()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_full_workflow_transitions_recorded(self):
        accession = AccessionService.create_accession(
            {"sample_code": "SMP-00001", "patient_name": "Workflow Patient"}
        )
        transitions = []
        while accession.workflow_stage != LAB_WF_PATIENT_PORTAL:
            accession, transition = AccessionService.advance_accession(accession.id, actor="tech.alpha")
            transitions.append(transition.to_stage)

        recorded = LabWorkflowTransition.query.filter_by(accession_id=accession.id).count()
        self.assertGreaterEqual(recorded, len(LAB_WORKFLOW_STAGES))
        self.assertEqual(accession.workflow_stage, LAB_WF_PATIENT_PORTAL)

    def test_receive_at_lab(self):
        accession = AccessionService.create_accession({"sample_code": "SMP-00002"})
        for _ in range(3):
            AccessionService.advance_accession(accession.id)
        accession, _ = AccessionService.receive_at_lab(accession.id)
        self.assertEqual(accession.workflow_stage, LAB_WF_RECEIVED_LAB)
        self.assertIsNotNone(accession.received_at)

    def test_analyzer_queue_workflow(self):
        accession = AccessionService.create_accession({"sample_code": "SMP-00003"})
        analyzer = AnalyzerService.create_analyzer({"name": "Hematology Analyzer"})
        for stage in LAB_WORKFLOW_STAGES[1:6]:
            AccessionService.advance_accession(accession.id, target_stage=stage)
        queue = AnalyzerService.enqueue_sample(analyzer.id, accession.id)
        self.assertEqual(queue.status, "QUEUED")
        started = AnalyzerService.start_queue(queue.id)
        self.assertEqual(started.status, "RUNNING")

    def test_lab_api_endpoints(self):
        response = self.client.post(
            "/api/v1/lab/accessions",
            json={"sample_code": "SMP-API-001", "patient_name": "API Patient"},
        )
        self.assertEqual(response.status_code, 201)
        accession_id = response.get_json()["accession"]["id"]

        response = self.client.get("/api/v1/lab/accessions")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/v1/lab/dashboard")
        self.assertEqual(response.status_code, 200)
        dashboard = response.get_json()
        self.assertIn("pending_samples", dashboard)

        response = self.client.post(f"/api/v1/lab/accessions/{accession_id}/advance")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
