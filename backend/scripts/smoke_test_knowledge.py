import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.knowledge_engine_service import KnowledgeEngineService


def smoke_test():
    with app.app_context():
        db.create_all()
        KnowledgeEngineService.ensure_default_content()
        steps = [
            ("GET knowledge search", "get", "/api/v1/knowledge?q=diabetes", None),
            ("GET guidelines", "get", "/api/v1/guidelines?pack=WHO", None),
            ("GET guideline packs", "get", "/api/v1/guidelines/packs", None),
            ("GET biomarkers", "get", "/api/v1/biomarkers?q=glucose", None),
            ("GET biomarker relationships", "get", "/api/v1/biomarkers/BM-GLU/relationships", None),
            ("GET diseases", "get", "/api/v1/diseases?q=diabetes", None),
            ("GET disease tests", "get", "/api/v1/diseases/DM-T2/tests", None),
            ("GET diseases by test", "get", "/api/v1/diseases/by-test/GLU", None),
            ("GET references", "get", "/api/v1/knowledge/references?test_code=GLU", None),
            (
                "POST correlation match",
                "post",
                "/api/v1/correlations/match",
                {"items": [{"test_code": "GLU", "result_value": "180"}, {"test_code": "HBA1C", "result_value": "7.2"}]},
            ),
            (
                "POST correlation evaluate",
                "post",
                "/api/v1/correlations/evaluate",
                {"items": [{"test_code": "GLU", "result_value": "140"}, {"test_code": "HBA1C", "result_value": "7.0"}]},
            ),
            ("GET knowledge dashboard", "get", "/knowledge", None),
            ("GET guidelines dashboard", "get", "/guidelines", None),
            ("GET disease library", "get", "/disease-library", None),
        ]
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            print("OK:", label, response.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON KNOWLEDGE SMOKE TEST ===\n")
if not smoke_test():
    print("\nKNOWLEDGE SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nKNOWLEDGE SMOKE TEST PASSED\n")
