import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import LAB_QC_FAILED, LAB_QC_PASSED
from app.extensions.db import db
from app.services.accession_service import AccessionService
from app.services.analyzer_service import AnalyzerService
from app.services.qc_service import QCService


class QCTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.accession = AccessionService.create_accession({"sample_code": "SMP-QC-001"})
        self.analyzer = AnalyzerService.create_analyzer({"name": "QC Analyzer"})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_qc_pass_and_fail(self):
        passed = QCService.create_qc(
            {
                "accession_id": self.accession.id,
                "analyzer_id": self.analyzer.id,
                "test_code": "GLU",
                "expected_value": 100,
                "observed_value": 101,
            }
        )
        evaluated = QCService.evaluate_qc(passed.id, actor="tech.alpha")
        self.assertEqual(evaluated.status, LAB_QC_PASSED)

        failed = QCService.create_qc(
            {
                "accession_id": self.accession.id,
                "analyzer_id": self.analyzer.id,
                "test_code": "CBC",
                "expected_value": 100,
                "observed_value": 150,
            }
        )
        evaluated_fail = QCService.evaluate_qc(failed.id, actor="tech.alpha")
        self.assertEqual(evaluated_fail.status, LAB_QC_FAILED)

    def test_qc_api(self):
        response = self.client.post(
            "/api/v1/lab/qc",
            json={
                "accession_id": self.accession.id,
                "analyzer_id": self.analyzer.id,
                "test_code": "TSH",
                "expected_value": 2.5,
                "observed_value": 2.6,
            },
        )
        self.assertEqual(response.status_code, 201)
        qc_id = response.get_json()["qc"]["id"]

        response = self.client.post(f"/api/v1/lab/qc/{qc_id}/evaluate")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/v1/lab/qc")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["pagination"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
