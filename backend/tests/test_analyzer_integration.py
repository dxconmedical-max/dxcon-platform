"""Tests for Analyzer Integration — Release 7.0 Sprint 5."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.analyzer_integration.adapters import SimulatorAdapter, get_adapter
from app.analyzer_integration.service import (
    AnalyzerIntegrationError,
    analyzer_dashboard,
    create_test_mapping,
    get_analyzer,
    ingest_result_message,
    list_quarantine,
    register_analyzer,
)
from app.extensions.db import db


class AnalyzerIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = "org-analyzer-test"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_analyzer_registration(self):
        row = register_analyzer({"name": "Chemistry 1", "protocol": "SIMULATOR"}, organization_id=self.org)
        db.session.commit()
        self.assertIn("analyzer_code", row)

    def test_valid_result_preliminary_not_released(self):
        anz = register_analyzer({"name": "Sim", "protocol": "SIMULATOR"}, organization_id=self.org)
        db.session.commit()
        create_test_mapping(
            {"analyzer_test_code": "GLU", "dxcon_test_code": "GLUCOSE", "unit": "mg/dL"},
            organization_id=self.org,
            actor="lab@test",
        )
        db.session.commit()
        result = ingest_result_message(
            {"specimen_barcode": "DX20260712000001", "analyzer_test_code": "GLU", "value": "95", "unit": "mg/dL"},
            organization_id=self.org,
            analyzer_id=anz["id"],
        )
        db.session.commit()
        self.assertEqual(result["status"], "preliminary")
        self.assertFalse(result["auto_released"])

    def test_unknown_barcode_quarantine(self):
        anz = register_analyzer({"name": "Sim"}, organization_id=self.org)
        db.session.commit()
        result = ingest_result_message(
            {"analyzer_test_code": "GLU", "value": "95"},
            organization_id=self.org,
            analyzer_id=anz["id"],
        )
        db.session.commit()
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(result["reason_code"], "UNKNOWN_BARCODE")

    def test_unmapped_test_quarantine(self):
        anz = register_analyzer({"name": "Sim"}, organization_id=self.org)
        db.session.commit()
        result = ingest_result_message(
            {"specimen_barcode": "DX001", "analyzer_test_code": "UNKNOWN", "value": "1"},
            organization_id=self.org,
            analyzer_id=anz["id"],
        )
        db.session.commit()
        self.assertEqual(result["reason_code"], "UNMAPPED_TEST")

    def test_duplicate_result_quarantine(self):
        anz = register_analyzer({"name": "Sim"}, organization_id=self.org)
        db.session.commit()
        create_test_mapping(
            {"analyzer_test_code": "HGB", "dxcon_test_code": "HEMOGLOBIN", "unit": "g/dL"},
            organization_id=self.org,
            actor="lab@test",
        )
        db.session.commit()
        payload = {"specimen_barcode": "DX002", "analyzer_test_code": "HGB", "value": "14.2", "unit": "g/dL"}
        ingest_result_message({**payload, "correlation_id": "c1"}, organization_id=self.org, analyzer_id=anz["id"])
        db.session.commit()
        dup = ingest_result_message({**payload, "correlation_id": "c2"}, organization_id=self.org, analyzer_id=anz["id"])
        db.session.commit()
        self.assertEqual(dup["reason_code"], "DUPLICATE_RESULT")

    def test_unit_mismatch_quarantine(self):
        anz = register_analyzer({"name": "Sim"}, organization_id=self.org)
        db.session.commit()
        create_test_mapping(
            {"analyzer_test_code": "GLU", "dxcon_test_code": "GLUCOSE", "unit": "mg/dL"},
            organization_id=self.org,
            actor="lab@test",
        )
        db.session.commit()
        result = ingest_result_message(
            {"specimen_barcode": "DX003", "analyzer_test_code": "GLU", "value": "5.5", "unit": "mmol/L"},
            organization_id=self.org,
            analyzer_id=anz["id"],
        )
        db.session.commit()
        self.assertEqual(result["reason_code"], "UNIT_MISMATCH")

    def test_tenant_isolation(self):
        anz = register_analyzer({"name": "Sim"}, organization_id=self.org)
        db.session.commit()
        with self.assertRaises(AnalyzerIntegrationError):
            get_analyzer(anz["id"], organization_id="other-org")

    def test_simulator_disabled_in_production(self):
        os.environ["FLASK_ENV"] = "production"
        adapter = SimulatorAdapter()
        with self.assertRaises(PermissionError):
            adapter.connect()
        os.environ["FLASK_ENV"] = "development"

    def test_original_value_preserved(self):
        anz = register_analyzer({"name": "Sim"}, organization_id=self.org)
        db.session.commit()
        create_test_mapping(
            {"analyzer_test_code": "NA", "dxcon_test_code": "SODIUM", "unit": "mEq/L"},
            organization_id=self.org,
            actor="lab@test",
        )
        db.session.commit()
        result = ingest_result_message(
            {"specimen_barcode": "DX004", "analyzer_test_code": "NA", "value": "140", "unit": "mEq/L", "correlation_id": "na-1"},
            organization_id=self.org,
            analyzer_id=anz["id"],
        )
        db.session.commit()
        from app.models.analyzer_integration import AnalyzerPreliminaryResult
        self.assertIn("result_id", result)
        row = AnalyzerPreliminaryResult.query.get(result["result_id"])
        self.assertEqual(row.original_value, "140")
        self.assertIsNotNone(row.normalized_value)

    def test_dashboard(self):
        dash = analyzer_dashboard(organization_id=self.org)
        self.assertIn("kpis", dash)


if __name__ == "__main__":
    unittest.main()
