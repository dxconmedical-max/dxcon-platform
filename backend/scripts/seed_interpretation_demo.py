import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.statuses import (
    CRITICAL_RULE_ACTIVE,
    INTERPRETATION_FLAG_CRITICAL,
    INTERPRETATION_FLAG_HIGH,
    INTERPRETATION_RULE_ACTIVE,
    INTERPRETATION_TEMPLATE_ACTIVE,
    REFERENCE_RANGE_ACTIVE,
)
from app.extensions.db import db
from app.models.critical_value_rule import CriticalValueRule
from app.models.interpretation_rule import InterpretationRule
from app.models.interpretation_template import InterpretationTemplate
from app.models.reference_range import ReferenceRange


def seed_interpretation_demo():
    if ReferenceRange.query.first():
        return {"rules_seeded": 0, "already_seeded": True}

    ranges = [
        ReferenceRange(
            test_code="GLU",
            test_name="Glucose",
            sex="ALL",
            age_min=18,
            age_max=120,
            unit="mmol/L",
            low_value=3.9,
            high_value=6.1,
            status=REFERENCE_RANGE_ACTIVE,
        ),
        ReferenceRange(
            test_code="GLU",
            test_name="Glucose",
            sex="F",
            age_min=18,
            age_max=50,
            unit="mmol/L",
            low_value=3.8,
            high_value=5.9,
            status=REFERENCE_RANGE_ACTIVE,
        ),
        ReferenceRange(
            test_code="HBA1C",
            test_name="HbA1c",
            sex="ALL",
            age_min=0,
            age_max=120,
            unit="%",
            low_value=4.0,
            high_value=6.0,
            status=REFERENCE_RANGE_ACTIVE,
        ),
        ReferenceRange(
            test_code="K",
            test_name="Potassium",
            sex="ALL",
            age_min=0,
            age_max=120,
            unit="mmol/L",
            low_value=3.5,
            high_value=5.1,
            status=REFERENCE_RANGE_ACTIVE,
        ),
    ]
    for row in ranges:
        db.session.add(row)

    critical_rules = [
        CriticalValueRule(
            rule_code="CRIT-K-LOW",
            test_code="K",
            test_name="Potassium",
            panic_low=2.5,
            severity="CRITICAL",
            message_en="Critical low potassium. Immediate physician notification required.",
            message_vi="Kali thap nguy hiem. Can thong bao bac si ngay.",
            status=CRITICAL_RULE_ACTIVE,
        ),
        CriticalValueRule(
            rule_code="CRIT-GLU-HIGH",
            test_code="GLU",
            test_name="Glucose",
            panic_high=20.0,
            severity="CRITICAL",
            message_en="Critical hyperglycemia detected.",
            message_vi="Duong huyet tang muc nguy hiem.",
            status=CRITICAL_RULE_ACTIVE,
        ),
    ]
    for row in critical_rules:
        db.session.add(row)

    rules = [
        InterpretationRule(
            rule_code="RULE-GLU-HIGH",
            test_code="GLU",
            condition_flag=INTERPRETATION_FLAG_HIGH,
            risk_level="MEDIUM",
            finding_en="Glucose is above the reference range.",
            finding_vi="Glucose cao hon khoang tham chieu.",
            recommendation_en="Recommend fasting glucose confirmation and clinical correlation.",
            recommendation_vi="Can xac nhan glucose doi va danh gia lam sang.",
            priority=10,
            status=INTERPRETATION_RULE_ACTIVE,
        ),
        InterpretationRule(
            rule_code="RULE-HBA1C-HIGH",
            test_code="HBA1C",
            condition_flag=INTERPRETATION_FLAG_HIGH,
            risk_level="MEDIUM",
            finding_en="HbA1c suggests impaired glucose control.",
            finding_vi="HbA1c goi y kiem soat duong huyet chua tot.",
            recommendation_en="Recommend lifestyle review and endocrine follow-up.",
            recommendation_vi="Can danh gia dieu chinh loi song va theo doi noi tiet.",
            priority=20,
            status=INTERPRETATION_RULE_ACTIVE,
        ),
    ]
    for row in rules:
        db.session.add(row)

    templates = [
        InterpretationTemplate(
            template_code="GENERAL_FINDING",
            version=1,
            language="en",
            title="General Finding",
            body_template="{test_name} result {result_value} is flagged {flag} against {reference_range}.",
            status=INTERPRETATION_TEMPLATE_ACTIVE,
        ),
        InterpretationTemplate(
            template_code="GENERAL_FINDING",
            version=1,
            language="vi",
            title="Dien giai chung",
            body_template="Ket qua {test_name} = {result_value}, danh gia {flag} so voi {reference_range}.",
            status=INTERPRETATION_TEMPLATE_ACTIVE,
        ),
    ]
    for row in templates:
        db.session.add(row)

    db.session.commit()
    return {
        "rules_seeded": len(rules),
        "ranges_seeded": len(ranges),
        "critical_rules_seeded": len(critical_rules),
        "templates_seeded": len(templates),
    }


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_interpretation_demo()
        print("\n=== DXCON INTERPRETATION DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
