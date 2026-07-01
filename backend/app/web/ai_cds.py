from flask import Blueprint

from app.models.ai_cds import (
    ClinicalGuidelinePack,
    ClinicalRecommendation,
    ClinicalRiskAssessment,
    ClinicalRuleDefinition,
    CriticalAlertEvent,
)
from app.services.ai_cds_service import ClinicalRuleEngineService


ai_cds_web_bp = Blueprint("ai_cds_web", __name__)


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
        ("/ai", "Overview"),
        ("/ai/interpreter", "Interpreter"),
        ("/ai/risk", "Risk"),
        ("/ai/critical", "Critical"),
    ]
    items = ""
    for href, label in links:
        cls = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{cls}>{label}</a>'
    return f'<div class="sidebar"><h2>AI CDS</h2>{items}</div>'


@ai_cds_web_bp.route("/ai")
def ai_home():
    ClinicalRuleEngineService.ensure_default_packs()
    return f"""
    <html><head><title>AI Clinical Decision Support</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/ai")}<div class="content">
    <div class="card"><h1>AI Clinical Decision Support</h1>
    <div class="grid">
        <div class="metric"><span>Guideline Packs</span><strong>{ClinicalGuidelinePack.query.count()}</strong></div>
        <div class="metric"><span>Rule Definitions</span><strong>{ClinicalRuleDefinition.query.count()}</strong></div>
        <div class="metric"><span>Risk Assessments</span><strong>{ClinicalRiskAssessment.query.count()}</strong></div>
        <div class="metric"><span>Recommendations</span><strong>{ClinicalRecommendation.query.count()}</strong></div>
        <div class="metric"><span>Critical Alerts</span><strong>{CriticalAlertEvent.query.count()}</strong></div>
    </div>
    <p>All outputs are advisory only and require physician review.</p>
    </div></div></div></body></html>
    """


@ai_cds_web_bp.route("/ai/interpreter")
def ai_interpreter():
    return f"""
    <html><head><title>AI Interpreter</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/ai/interpreter")}<div class="content">
    <div class="card"><h1>Result Interpreter</h1>
    <p>API: POST /api/v1/ai/interpret</p>
    <p>Panels: CBC, Chemistry, Liver, Kidney, Lipid, HbA1c, Thyroid, Urinalysis, Coagulation</p>
    </div></div></div></body></html>
    """


@ai_cds_web_bp.route("/ai/risk")
def ai_risk():
    rows = ClinicalRiskAssessment.query.order_by(ClinicalRiskAssessment.created_at.desc()).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.assessment_code}</td><td>{row.risk_domain}</td><td>{row.risk_level}</td><td>{row.risk_score}</td></tr>"
    return f"""
    <html><head><title>AI Risk</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/ai/risk")}<div class="content">
    <div class="card"><h1>Risk Assessment</h1>
    <table><tr><th>Code</th><th>Domain</th><th>Level</th><th>Score</th></tr>{table or "<tr><td colspan='4'>No assessments</td></tr>"}</table>
    </div></div></div></body></html>
    """


@ai_cds_web_bp.route("/ai/critical")
def ai_critical():
    rows = CriticalAlertEvent.query.order_by(CriticalAlertEvent.created_at.desc()).limit(20).all()
    table = ""
    for row in rows:
        table += f"<tr><td>{row.alert_code}</td><td>{row.alert_type}</td><td>{row.severity}</td><td>{row.message or ''}</td></tr>"
    return f"""
    <html><head><title>Critical Alerts</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/ai/critical")}<div class="content">
    <div class="card"><h1>Critical Results</h1>
    <table><tr><th>Code</th><th>Type</th><th>Severity</th><th>Message</th></tr>{table or "<tr><td colspan='4'>No alerts</td></tr>"}</table>
    </div></div></div></body></html>
    """
