import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.ai_cds import (
    ClinicalDeltaCheck,
    ClinicalGuidelinePack,
    ClinicalRecommendation,
    ClinicalRiskAssessment,
    ClinicalRuleDefinition,
    CriticalAlertEvent,
)
from app.models.critical_value_rule import CriticalValueRule
from app.models.reference_range import ReferenceRange
from app.services.ai_cds_service import (
    AIInterpretationService,
    AIRecommendationService,
    AIRiskService,
    ClinicalRuleEngineService,
    CriticalDetectionService,
)


def seed_demo():
    db.session.add(
        ReferenceRange(
            test_code="GLU",
            test_name="Glucose",
            sex="ALL",
            age_min=0,
            age_max=120,
            low_value=70,
            high_value=100,
            status="ACTIVE",
        )
    )
    db.session.add(
        CriticalValueRule(
            rule_code="CRIT-GLU-VERIFY",
            test_code="GLU",
            panic_low=40,
            panic_high=400,
            message_en="Critical glucose",
            status="ACTIVE",
        )
    )
    db.session.commit()


def verify_models_import():
    models = [
        ClinicalGuidelinePack,
        ClinicalRuleDefinition,
        ClinicalDeltaCheck,
        ClinicalRiskAssessment,
        ClinicalRecommendation,
        CriticalAlertEvent,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/ai/interpret",
        "/api/v1/ai/risk",
        "/api/v1/ai/recommend",
        "/api/v1/ai/reference-ranges",
        "/api/v1/ai/critical-results",
    ]
    required_web = [
        "/ai",
        "/ai/interpreter",
        "/ai/risk",
        "/ai/critical",
    ]
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_no_duplicate_routes(app):
    seen = set()
    for rule in app.url_map.iter_rules():
        if not str(rule).startswith("/api/v1/ai"):
            continue
        key = (str(rule.rule), tuple(sorted(rule.methods)))
        if key in seen:
            print("DUPLICATE:", key)
            return False
        seen.add(key)
    print("OK: no duplicate /api/v1/ai routes")
    return True


def verify_engines():
    with app.app_context():
        db.create_all()
        seed_demo()
        ClinicalRuleEngineService.ensure_default_packs()
        if ClinicalGuidelinePack.query.count() < 9:
            print("MISSING: guideline packs")
            return False
        print("OK: rule engine packs", ClinicalGuidelinePack.query.count())

        ranges = ClinicalRuleEngineService.list_reference_ranges(test_code="GLU")
        if not ranges:
            print("MISSING: reference ranges")
            return False
        print("OK: reference ranges")

        delta = ClinicalRuleEngineService.evaluate_delta("p1", "GLU", 150, 100)
        if not delta or not delta.get("is_significant"):
            print("MISSING: delta check")
            return False
        print("OK: delta check")

        interp = AIInterpretationService.interpret_payload(
            {"items": [{"test_code": "GLU", "test_name": "Glucose", "result_value": "180"}]}
        )
        if interp["count"] < 1:
            print("MISSING: interpretation")
            return False
        print("OK: interpretation engine")

        recs = AIRecommendationService.generate(
            {"items": [{"test_code": "GLU", "test_name": "Glucose", "result_value": "180"}]}
        )
        if recs["count"] < 1:
            print("MISSING: recommendations")
            return False
        print("OK: recommendations", recs["count"])

        risk = AIRiskService.assess(
            {"items": [{"test_code": "GLU", "result_value": "140"}, {"test_code": "HBA1C", "result_value": "7.0"}]}
        )
        if not risk["assessments"]:
            print("MISSING: risk scoring")
            return False
        print("OK: risk scoring")

        critical = CriticalDetectionService.detect(
            {
                "patient_id": "p1",
                "items": [
                    {"test_code": "GLU", "result_value": "450"},
                    {"test_code": "WBC", "result_value": "15", "flag": "HIGH"},
                    {"test_code": "CRP", "result_value": "20", "flag": "HIGH"},
                ],
                "repeated_abnormality": True,
            }
        )
        if critical["count"] < 1:
            print("MISSING: critical alerts")
            return False
        print("OK: critical alerts", critical["count"])
        return True


app = create_app()
print("\n=== DXCON AI CDS VERIFY ===\n")
errors = 0
if not verify_models_import():
    errors += 1
if not verify_routes(app):
    errors += 1
if not verify_no_duplicate_routes(app):
    errors += 1
if not verify_engines():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nAI CDS VERIFY PASSED\n")
