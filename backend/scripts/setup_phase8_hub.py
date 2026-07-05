#!/usr/bin/env python3
"""Generate Phase 8 Intelligent Healthcare Platform hub scaffolding."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HUB = {
    "phase": "8",
    "slug": "intelligent_healthcare",
    "prefix": "intelligent-healthcare",
    "title": "Intelligent Healthcare Platform",
    "roles": "INTELLIGENT_HEALTHCARE_ROLES",
    "service": "intelligent_healthcare_service",
    "features": [
        ("ai-clinical-platform", "ai_clinical_platform", "AI Clinical Platform"),
        ("medical-knowledge", "medical_knowledge_base", "Medical Knowledge Base"),
        ("clinical-rules", "clinical_rules_engine", "Clinical Rules Engine"),
        ("reference-ranges", "reference_range_engine", "Reference Range Engine"),
        ("loinc-registry", "loinc_registry", "LOINC Registry"),
        ("icd10-registry", "icd10_registry", "ICD10 Registry"),
        ("snomed-mapping", "snomed_mapping_layer", "SNOMED Mapping Layer"),
        ("drug-knowledge", "drug_knowledge_layer", "Drug Knowledge Layer"),
        ("medical-ocr", "medical_ocr_platform", "Medical OCR Platform"),
        ("voice-clinical", "voice_clinical_platform", "Voice Clinical Platform"),
        ("ai-copilot", "ai_copilot_hub", "AI Copilot"),
        ("doctor-copilot", "doctor_copilot", "Doctor Copilot"),
        ("reception-copilot", "reception_copilot", "Reception Copilot"),
        ("collector-copilot", "collector_copilot", "Collector Copilot"),
        ("ceo-copilot", "ceo_copilot", "CEO Copilot"),
        ("predictive-analytics", "predictive_analytics", "Predictive Analytics"),
        ("clinical-summary", "clinical_summary", "Clinical Summary"),
        ("patient-explanation", "patient_friendly_explanation", "Patient-friendly Explanation"),
        ("ai-gateway", "ai_gateway", "AI Gateway"),
        ("llm-providers", "llm_provider_registry", "LLM Provider Registry"),
        ("prompt-registry", "prompt_registry", "Prompt Registry"),
        ("prompt-versioning", "prompt_versioning", "Prompt Versioning"),
        ("ai-safety", "ai_safety_layer", "AI Safety Layer"),
        ("prompt-audit", "prompt_audit", "Prompt Audit"),
        ("cost-analytics", "cost_analytics", "Cost Analytics"),
        ("hallucination-detection", "hallucination_detection", "Hallucination Detection"),
        ("model-comparison", "model_comparison", "Model Comparison"),
        ("phi-redaction", "phi_redaction", "PHI Redaction"),
        ("medical-guardrails", "medical_guardrails", "Medical Guardrails"),
        ("clinical-recommendations", "clinical_recommendation_engine", "Clinical Recommendation Engine"),
        ("ai-monitoring", "ai_monitoring_dashboard", "AI Monitoring Dashboard"),
    ],
}


def write_api(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    svc = hub["service"]
    lines = [
        f'"""{hub["title"]} API routes — Phase {hub["phase"]}."""',
        "",
        "from __future__ import annotations",
        "",
        "from flask import Blueprint",
        "",
        f"from app.services.{svc} import (",
        "    dashboard_payload,",
    ]
    for _, fn, _ in hub["features"]:
        lines.append(f"    {fn},")
    lines.append(f"    {slug}_readiness_report,")
    lines.append(")")
    lines.append("")
    lines.append(f'{slug}_bp = Blueprint("{slug}_api", __name__, url_prefix="/api/v1/{prefix}")')
    lines.append("")
    lines.append(f'@{slug}_bp.route("/dashboard", methods=["GET"])')
    lines.append(f"def {slug}_dashboard_api():")
    lines.append("    return dashboard_payload()")
    lines.append("")
    for route, fn, _ in hub["features"]:
        lines.append(f'@{slug}_bp.route("/{route}", methods=["GET"])')
        lines.append(f"def {slug}_{fn}_api():")
        lines.append(f"    return {fn}()")
        lines.append("")
    lines.append(f'@{slug}_bp.route("/readiness", methods=["GET"])')
    lines.append(f"def {slug}_readiness_api():")
    lines.append(f"    return {slug}_readiness_report()")
    lines.append("")
    path = ROOT / "app" / "api" / slug / "routes.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_web_lib(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    svc = hub["service"]
    nav = f'("Overview", "/{prefix}"),\n    ' + ",\n    ".join(
        f'("{label}", "/{prefix}/{route}")' for route, _, label in hub["features"]
    )
    builds = "\n".join(
        f"def build_{fn}_body() -> str:\n    return build_json_section({label!r}, svc.{fn}())\n"
        for _, fn, label in hub["features"]
    )
    imports = ",\n    ".join(f"build_{fn}_body" for _, fn, _ in hub["features"])
    feature_count = len(hub["features"])
    content = f'''"""{hub["title"]} web rendering helpers — Phase {hub["phase"]}."""

from __future__ import annotations

import html
import json

from app.services import {svc} as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    {nav}
)


def hub_styles() -> str:
    return pilot_styles() + """
    pre {{ background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }}
    .muted-note {{ color:#64748b; font-size:13px; margin-bottom:16px; }}
    """


def render_hub_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{{href}}">{{label}}</a>' for label, href in NAV)
    return f"""
    <html>
    <head><title>{{title}}</title><meta name="viewport" content="width=device-width, initial-scale=1" /><style>{{hub_styles()}}</style></head>
    <body><div class="wrap"><div class="nav">{{nav}}</div><div class="muted-note">{hub["title"]} · Phase {hub["phase"]} · Human medical review mandatory</div>{{body_html}}</div></body>
    </html>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {{page_header(title, data.get("report", ""))}}
    <div class="card"><pre>{{html.escape(json.dumps(data, indent=2, default=str))}}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data.get("summary", {{}})
    cards = metric_cards([(k.replace("_", " ").title(), v) for k, v in list(summary.items())[:6]])
    features = "".join(f"<li>{{html.escape(item)}}</li>" for item in data.get("features", []))
    policy = data.get("policy", {{}})
    policy_html = "".join(f"<li>{{html.escape(k)}}: {{html.escape(str(v))}}</li>" for k, v in policy.items())
    return f"""
    {{page_header("{hub["title"]}", "Phase {hub["phase"]} — AI-assisted healthcare with mandatory human review.")}}
    {{cards}}
    <div class="card"><h3>Governance Policy</h3><ul>{{policy_html}}</ul></div>
    <div class="card"><h3>Modules ({feature_count})</h3><ul>{{features}}</ul></div>
    """


{builds}
'''
    (ROOT / "app" / "web" / f"{slug}_lib.py").write_text(content, encoding="utf-8")


def write_web(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    roles = hub["roles"]
    imports = ",\n    ".join(f"build_{fn}_body" for _, fn, _ in hub["features"])
    routes = [
        f'@{slug}_web_bp.route("/{prefix}")\n@role_required(*{roles})\ndef {slug}_dashboard():\n    return render_hub_page("{hub["title"]}", build_dashboard_body())\n'
    ]
    for route, fn, label in hub["features"]:
        routes.append(
            f'@{slug}_web_bp.route("/{prefix}/{route}")\n@role_required(*{roles})\ndef {slug}_{fn}():\n    return render_hub_page("{label}", build_{fn}_body())\n'
        )
    content = f'''"""{hub["title"]} web routes — Phase {hub["phase"]}."""

from __future__ import annotations

from flask import Blueprint

from app.services.{hub["service"]} import {roles}
from app.utils.auth import role_required
from app.web.{slug}_lib import (
    build_dashboard_body,
    {imports},
    render_hub_page,
)

{slug}_web_bp = Blueprint("{slug}_web", __name__)

{"".join(routes)}
'''
    (ROOT / "app" / "web" / f"{slug}.py").write_text(content, encoding="utf-8")


def write_test(hub: dict) -> None:
    slug = hub["slug"]
    prefix = hub["prefix"]
    content = f'''import os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

class IntelligentHealthcareTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        user = User(email="demo-{slug}@demo.dxcon.test", role="ADMIN", password_hash=hash_password("DemoPass123!"), is_active=True)
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_routes_registered(self):
        routes = {{str(r.rule) for r in self.app.url_map.iter_rules()}}
        self.assertIn("/{prefix}", routes)
        self.assertIn("/api/v1/{prefix}/dashboard", routes)

    def test_dashboard(self):
        r = self.client.get("/{prefix}")
        self.assertEqual(r.status_code, 200)
        d = self.client.get("/api/v1/{prefix}/dashboard")
        self.assertEqual(d.status_code, 200)
        payload = d.get_json()
        if isinstance(payload, dict) and payload.get("success"):
            payload = payload["data"]
        self.assertEqual(payload["phase"], "{hub["phase"]}")
        self.assertTrue(payload.get("policy", {{}}).get("human_review_required"))

    def test_governance_policy(self):
        from app.services.{hub["service"]} import FEATURES, GOVERNANCE_POLICY
        self.assertEqual(len(FEATURES), {len(hub["features"])})
        self.assertTrue(GOVERNANCE_POLICY["human_review_required"])
        self.assertFalse(GOVERNANCE_POLICY["automatic_diagnosis"])
'''
    (ROOT / "tests" / f"test_{slug}_hub.py").write_text(content, encoding="utf-8")


def main():
    write_api(HUB)
    write_web_lib(HUB)
    write_web(HUB)
    write_test(HUB)
    print("scaffolded", HUB["slug"], f"({len(HUB['features'])} features)")


if __name__ == "__main__":
    main()
