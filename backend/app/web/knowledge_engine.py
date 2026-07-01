from flask import Blueprint

from app.models.knowledge_engine import (
    Biomarker,
    ClinicalGuideline,
    DiseaseProfile,
    MedicalKnowledge,
    ReferenceLibrary,
)
from app.services.knowledge_engine_service import KnowledgeEngineService


knowledge_web_bp = Blueprint("knowledge_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#1e293b; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#e0f2fe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/knowledge", "Overview"),
        ("/guidelines", "Guidelines"),
        ("/disease-library", "Disease Library"),
    ]
    items = ""
    for href, label in links:
        cls = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{cls}>{label}</a>'
    return f'<div class="sidebar"><h2>Knowledge</h2>{items}</div>'


@knowledge_web_bp.route("/knowledge")
def knowledge_home():
    KnowledgeEngineService.ensure_default_content()
    return f"""
    <html><head><title>Medical Knowledge</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/knowledge")}<div class="content">
    <div class="card"><h1>Medical Knowledge Base</h1>
    <div class="grid">
        <div class="metric"><span>Knowledge Articles</span><strong>{MedicalKnowledge.query.count()}</strong></div>
        <div class="metric"><span>Guidelines</span><strong>{ClinicalGuideline.query.count()}</strong></div>
        <div class="metric"><span>Biomarkers</span><strong>{Biomarker.query.count()}</strong></div>
        <div class="metric"><span>Reference Entries</span><strong>{ReferenceLibrary.query.count()}</strong></div>
    </div>
    <p>API: GET /api/v1/knowledge?q=diabetes</p>
    </div></div></div></body></html>
    """


@knowledge_web_bp.route("/guidelines")
def guidelines_page():
    KnowledgeEngineService.ensure_default_content()
    rows = ClinicalGuideline.query.order_by(ClinicalGuideline.pack_source.asc()).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.pack_source}</td><td>{row.guideline_code}</td><td>{row.version}</td><td>{row.evidence_level}</td></tr>"
    return f"""
    <html><head><title>Guidelines</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/guidelines")}<div class="content">
    <div class="card"><h1>Guideline Packs</h1>
    <p>WHO, CLSI, IFCC, CAP, CDC, Vietnam MOH</p>
    <table><tr><th>Pack</th><th>Code</th><th>Version</th><th>Evidence</th></tr>{table or "<tr><td colspan='4'>No guidelines</td></tr>"}</table>
    </div></div></div></body></html>
    """


@knowledge_web_bp.route("/disease-library")
def disease_library_page():
    KnowledgeEngineService.ensure_default_content()
    rows = DiseaseProfile.query.order_by(DiseaseProfile.name.asc()).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.disease_code}</td><td>{row.name}</td><td>{row.icd10 or ''}</td><td>{row.evidence_level}</td></tr>"
    return f"""
    <html><head><title>Disease Library</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/disease-library")}<div class="content">
    <div class="card"><h1>Disease Library</h1>
    <table><tr><th>Code</th><th>Name</th><th>ICD-10</th><th>Evidence</th></tr>{table or "<tr><td colspan='4'>No diseases</td></tr>"}</table>
    </div></div></div></body></html>
    """
