import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.knowledge_engine import Biomarker, ClinicalGuideline, DiseaseProfile, MedicalKnowledge
from app.services.knowledge_engine_service import (
    BiomarkerService,
    CorrelationService,
    DiseaseMappingService,
    GuidelinePackService,
    KnowledgeEngineService,
    KnowledgeSearchService,
)


class KnowledgeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        KnowledgeEngineService.ensure_default_content()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_knowledge_search_api(self):
        response = self.client.get("/api/v1/knowledge?q=diabetes")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["total"], 1)

    def test_guideline_packs_api(self):
        response = self.client.get("/api/v1/guidelines/packs")
        self.assertEqual(response.status_code, 200)
        packs = {row["pack_source"] for row in response.get_json()["packs"]}
        self.assertIn("WHO", packs)
        self.assertIn("VN_MOH", packs)
        self.assertGreaterEqual(ClinicalGuideline.query.count(), 6)

    def test_biomarker_relationships_api(self):
        response = self.client.get("/api/v1/biomarkers/BM-GLU/relationships")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["biomarker"]["test_code"], "GLU")
        self.assertGreaterEqual(len(payload["related_diseases"]), 1)

    def test_disease_test_mapping_api(self):
        tests = self.client.get("/api/v1/diseases/DM-T2/tests")
        self.assertEqual(tests.status_code, 200)
        self.assertIn("GLU", tests.get_json()["tests"])

        by_test = self.client.get("/api/v1/diseases/by-test/GLU")
        self.assertEqual(by_test.status_code, 200)
        codes = {row["disease_code"] for row in by_test.get_json()["diseases"]}
        self.assertIn("DM-T2", codes)

    def test_correlation_apis(self):
        match = self.client.post(
            "/api/v1/correlations/match",
            json={"items": [{"test_code": "GLU", "result_value": "180"}, {"test_code": "HBA1C", "result_value": "7.2"}]},
        )
        self.assertEqual(match.status_code, 200)
        self.assertGreaterEqual(len(match.get_json()["matches"]), 1)

        evaluate = self.client.post(
            "/api/v1/correlations/evaluate",
            json={"items": [{"test_code": "GLU", "result_value": "140"}, {"test_code": "HBA1C", "result_value": "7.0"}]},
        )
        self.assertEqual(evaluate.status_code, 200)
        self.assertGreaterEqual(evaluate.get_json()["evaluated"], 1)

    def test_services(self):
        self.assertGreaterEqual(MedicalKnowledge.query.count(), 1)
        self.assertGreaterEqual(Biomarker.query.count(), 1)
        self.assertGreaterEqual(DiseaseProfile.query.count(), 1)
        search = KnowledgeSearchService.search(query="ckd")
        self.assertGreaterEqual(search["total"], 1)
        guidelines = GuidelinePackService.list_guidelines(pack_source="CLSI")
        self.assertGreaterEqual(guidelines["total"], 1)
        biomarker = BiomarkerService.get_by_code("BM-CREA")
        self.assertEqual(biomarker["test_code"], "CREA")
        disease = DiseaseMappingService.get_by_code("CKD")
        self.assertEqual(disease["icd10"], "N18")
        chains = CorrelationService.evaluate_chains({"items": [{"test_code": "CREA", "result_value": "2.0"}, {"test_code": "EGFR", "result_value": "45"}]})
        self.assertTrue(any(row["matched"] for row in chains["chains"]))


if __name__ == "__main__":
    unittest.main()
