import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.knowledge_engine import (
    Biomarker,
    ClinicalGuideline,
    DiseaseProfile,
    MedicalKnowledge,
    ReferenceLibrary,
)
from app.services.knowledge_engine_service import (
    BiomarkerService,
    CorrelationService,
    DiseaseMappingService,
    GuidelinePackService,
    KnowledgeEngineService,
    KnowledgeSearchService,
    ReferenceLibraryService,
)


def verify_models_import():
    models = [
        MedicalKnowledge,
        ClinicalGuideline,
        DiseaseProfile,
        Biomarker,
        ReferenceLibrary,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/knowledge",
        "/api/v1/knowledge/<knowledge_id>",
        "/api/v1/knowledge/references",
        "/api/v1/guidelines",
        "/api/v1/guidelines/packs",
        "/api/v1/guidelines/<guideline_id>",
        "/api/v1/biomarkers",
        "/api/v1/biomarkers/<biomarker_code>",
        "/api/v1/biomarkers/<biomarker_code>/relationships",
        "/api/v1/diseases",
        "/api/v1/diseases/<disease_code>",
        "/api/v1/diseases/<disease_code>/tests",
        "/api/v1/diseases/by-test/<test_code>",
        "/api/v1/correlations/match",
        "/api/v1/correlations/evaluate",
    ]
    required_web = [
        "/knowledge",
        "/guidelines",
        "/disease-library",
    ]
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/knowledge", "/api/v1/guidelines", "/api/v1/biomarkers", "/api/v1/diseases", "/api/v1/correlations")
    seen = set()
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path.startswith(prefix) for prefix in prefixes):
            continue
        key = (path, tuple(sorted(rule.methods)))
        if key in seen:
            print("DUPLICATE:", key)
            return False
        seen.add(key)
    print("OK: no duplicate knowledge routes")
    return True


def verify_engines():
    with app.app_context():
        db.create_all()
        seed = KnowledgeEngineService.ensure_default_content()
        if not seed.get("seeded") and MedicalKnowledge.query.count() < 1:
            print("MISSING: default knowledge seed")
            return False
        print("OK: knowledge seed", MedicalKnowledge.query.count(), "articles")

        packs = GuidelinePackService.list_packs()
        if len(packs["packs"]) < 6:
            print("MISSING: guideline packs")
            return False
        print("OK: guideline packs", len(packs["packs"]))

        search = KnowledgeSearchService.search(query="diabetes")
        if search["total"] < 1:
            print("MISSING: searchable knowledge")
            return False
        print("OK: searchable knowledge")

        tests = DiseaseMappingService.tests_for_disease("DM-T2")
        if "GLU" not in tests["tests"]:
            print("MISSING: disease to test mapping")
            return False
        print("OK: disease to test mapping")

        by_test = DiseaseMappingService.diseases_for_test("GLU")
        if not by_test["diseases"]:
            print("MISSING: test to disease mapping")
            return False
        print("OK: test to disease mapping")

        rel = BiomarkerService.relationships("BM-GLU")
        if not rel["related_biomarkers"] and not rel["related_diseases"]:
            print("MISSING: biomarker relationships")
            return False
        print("OK: biomarker relationships")

        refs = ReferenceLibraryService.list_references(test_code="GLU")
        if len(refs["references"]) < 1:
            print("MISSING: reference library")
            return False
        print("OK: reference library", len(refs["references"]))

        match = CorrelationService.match_markers(
            {"items": [{"test_code": "GLU", "result_value": "180"}, {"test_code": "HBA1C", "result_value": "7.2"}]}
        )
        if not match["matches"]:
            print("MISSING: disease pattern matching")
            return False
        print("OK: disease pattern matching")

        chains = CorrelationService.evaluate_chains(
            {"items": [{"test_code": "GLU", "result_value": "140"}, {"test_code": "HBA1C", "result_value": "7.0"}]}
        )
        if chains["evaluated"] < 1:
            print("MISSING: rule chain evaluation")
            return False
        print("OK: rule chain evaluation")
        return True


app = create_app()
print("\n=== DXCON KNOWLEDGE VERIFY ===\n")
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
print("\nKNOWLEDGE VERIFY PASSED\n")
