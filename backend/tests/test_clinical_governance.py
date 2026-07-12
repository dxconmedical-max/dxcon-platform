"""Tests for Clinical Governance — Release 8.0 Sprint 6."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.clinical_governance.service import (
    ClinicalGovernanceError,
    create_critical_policy,
    create_verification_token,
    promote_preliminary_to_result,
    release_report_governed,
    validate_result_item,
    verify_report_token,
)
from app.clinical_governance.workflow import WorkflowError, record_transition
from app.core.statuses import (
    CLINICAL_REPORT_APPROVED,
    CLINICAL_RESULT_PENDING,
    CLINICAL_RESULT_PRELIMINARY,
    CLINICAL_RESULT_RELEASED,
    CLINICAL_RESULT_TECHNICIAN_VALIDATED,
)
from app.extensions.db import db
from app.models.analyzer_integration import AnalyzerPreliminaryResult
from app.models.biz_order import BizOrder, BizResult, BizResultItem
from app.models.clinical_report import ClinicalReport


class ClinicalGovernanceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = "org-clinical-test"
        self.actor = "tech@test"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed_order_with_item(self, *, status: str = CLINICAL_RESULT_PRELIMINARY) -> tuple[BizOrder, BizResultItem]:
        order = BizOrder(
            order_code="ORD-TEST-001",
            patient_code="PAT-001",
            patient_name="Test Patient",
            status="testing",
        )
        db.session.add(order)
        db.session.flush()
        result = BizResult(result_code="RES-TEST", order_id=order.id, status="testing")
        db.session.add(result)
        db.session.flush()
        item = BizResultItem(
            result_id=result.id,
            test_code="GLUCOSE",
            test_name="Glucose",
            result_value="200",
            original_value="200",
            normalized_value="200",
            unit="mg/dL",
            result_status=status,
        )
        db.session.add(item)
        db.session.commit()
        return order, item

    def test_invalid_transition_rejected(self):
        with self.assertRaises(WorkflowError):
            record_transition(
                organization_id=self.org,
                aggregate_type="result",
                aggregate_id="x",
                from_status=CLINICAL_RESULT_PENDING,
                to_status=CLINICAL_RESULT_RELEASED,
                actor=self.actor,
            )

    def test_result_cannot_skip_technician_validation(self):
        order, item = self._seed_order_with_item(status=CLINICAL_RESULT_PRELIMINARY)
        report = ClinicalReport(
            report_code="RPT-001",
            order_id=order.id,
            order_code=order.order_code,
            patient_id=order.patient_code,
            report_status="approved",
        )
        db.session.add(report)
        db.session.commit()
        with self.assertRaises(ClinicalGovernanceError):
            release_report_governed(order.order_code, organization_id=self.org, actor="doc@test")

    def test_technician_validate_preserves_original_value(self):
        order, item = self._seed_order_with_item()
        payload = validate_result_item(item.id, organization_id=self.org, actor=self.actor)
        db.session.commit()
        self.assertEqual(payload["original_value"], "200")
        self.assertEqual(payload["result_status"], CLINICAL_RESULT_TECHNICIAN_VALIDATED)

    def test_promote_preliminary_not_auto_released(self):
        order = BizOrder(order_code="ORD-PROMO", patient_code="P1", patient_name="P", status="testing")
        db.session.add(order)
        db.session.flush()
        prelim = AnalyzerPreliminaryResult(
            organization_id=self.org,
            specimen_barcode="DX-SIM-001",
            test_code="GLUCOSE",
            original_value="100",
            normalized_value="100",
            unit="mg/dL",
            review_status="PENDING_REVIEW",
        )
        db.session.add(prelim)
        db.session.commit()
        row = promote_preliminary_to_result(prelim.id, organization_id=self.org, order_id=order.id, actor=self.actor)
        db.session.commit()
        self.assertNotEqual(row.get("result_status"), CLINICAL_RESULT_RELEASED)

    def test_verification_token_no_phi(self):
        order, _ = self._seed_order_with_item(status=CLINICAL_RESULT_TECHNICIAN_VALIDATED)
        report = ClinicalReport(
            report_code="RPT-VERIFY",
            order_id=order.id,
            order_code=order.order_code,
            patient_id=order.patient_code,
            report_status="released",
            report_version=1,
        )
        db.session.add(report)
        db.session.commit()
        token_row = create_verification_token(report, organization_id=self.org)
        db.session.commit()
        payload = verify_report_token(token_row["token"])
        self.assertTrue(payload["valid"])
        self.assertNotIn("patient_name", payload)
        self.assertNotIn("result_value", payload)

    def test_critical_policy_detection(self):
        order, item = self._seed_order_with_item()
        create_critical_policy(
            {"test_code": "GLUCOSE", "lower_threshold": 50, "upper_threshold": 120},
            organization_id=self.org,
            actor=self.actor,
        )
        validate_result_item(item.id, organization_id=self.org, actor=self.actor)
        db.session.commit()
        refreshed = BizResultItem.query.get(item.id)
        self.assertTrue(refreshed.critical_flag or refreshed.flag == "CRITICAL")


if __name__ == "__main__":
    unittest.main()
